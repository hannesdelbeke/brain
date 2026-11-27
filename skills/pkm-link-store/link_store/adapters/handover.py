"""Deterministic post-pass that infers handed_over_to edges between sessions."""

from __future__ import annotations

from bisect import bisect_left
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

from ..db import LinkStoreDB

SOURCE = "handover_heuristic"
REL = "handed_over_to"
MAX_GAP = timedelta(hours=48)
DEFAULT_HUB_MAX_SESSIONS = 10
READ_CONFIDENCE = 0.80
SHARED_BASE_CONFIDENCE = 0.65
SHARED_STEP = 0.05
SHARED_MAX_CONFIDENCE = 0.85
MIN_SHARED = 2

# Only these carry session activity times. Derived edges must stay out, or a
# previous run's output would shift the next run's session end times.
_ACTIVITY_RELS = (
    "read_file",
    "modified_file",
    "made_commit",
    "fetched_url",
    "cited_url",
    "worked_in_branch",
)


@dataclass
class _Session:
    node_id: str
    start: datetime | None = None
    end: datetime | None = None
    start_raw: str = ""
    reads: set[str] = field(default_factory=set)
    modified: set[str] = field(default_factory=set)
    commits: set[str] = field(default_factory=set)
    repos: set[str] = field(default_factory=set)

    def observe(self, raw: str | None) -> None:
        ts = _parse_ts(raw)
        if ts is None:
            return
        if self.start is None or ts < self.start:
            self.start, self.start_raw = ts, str(raw)
        if self.end is None or ts > self.end:
            self.end = ts

    @property
    def root(self) -> str:
        """Parent session id, shared by a session and its subagents."""
        return self.node_id.split(":agent-", 1)[0]


def _parse_ts(raw: str | None) -> datetime | None:
    if not raw:
        return None
    text = raw.strip()
    if text.endswith(("Z", "z")):  # fromisoformat rejects Z before Python 3.11
        text = text[:-1] + "+00:00"
    try:
        ts = datetime.fromisoformat(text)
    except ValueError:
        return None
    return ts if ts.tzinfo else ts.replace(tzinfo=timezone.utc)


def _repo_of(node_id: str) -> str | None:
    """Repo slug embedded in a branch:, file:, or commit: id."""
    kind, _, rest = node_id.partition(":")
    if kind not in ("branch", "file", "commit"):
        return None
    slug, sep, _ = rest.partition("@")
    return slug if sep else None


def _load_sessions(db: LinkStoreDB) -> dict[str, _Session]:
    sessions = {
        row["id"]: _Session(row["id"])
        for row in db.conn.execute(
            "SELECT id FROM nodes WHERE node_type = 'Session' AND expired_at IS NULL"
        )
    }
    placeholders = ",".join("?" * len(_ACTIVITY_RELS))
    for row in db.conn.execute(
        f"SELECT src_id, dst_id, rel, valid_from, valid_to FROM edges "
        f"WHERE expired_at IS NULL AND rel IN ({placeholders})",
        _ACTIVITY_RELS,
    ):
        sess = sessions.get(row["src_id"])
        if sess is None:
            continue
        sess.observe(row["valid_from"])
        sess.observe(row["valid_to"])
        rel, dst = row["rel"], row["dst_id"]
        if rel == "read_file":
            sess.reads.add(dst)
            continue
        if rel == "modified_file":
            sess.modified.add(dst)
        elif rel == "made_commit":
            sess.commits.add(dst)
        elif rel != "worked_in_branch":
            continue
        repo = _repo_of(dst)
        if repo:
            sess.repos.add(repo)

    # A commit's Session: trailer is the same fact as made_commit, reversed.
    for row in db.conn.execute(
        "SELECT src_id, dst_id FROM edges WHERE expired_at IS NULL AND rel = 'mentions_session'"
    ):
        sess = sessions.get(row["dst_id"])
        if sess is None:
            continue
        sess.commits.add(row["src_id"])
        repo = _repo_of(row["src_id"])
        if repo:
            sess.repos.add(repo)
    return sessions


def _explicit_pairs(db: LinkStoreDB) -> set[frozenset[str]]:
    return {
        frozenset((row["src_id"], row["dst_id"]))
        for row in db.conn.execute(
            "SELECT src_id, dst_id FROM edges "
            "WHERE expired_at IS NULL AND rel IN ('continued_in', 'derived_from')"
        )
    }


def _score(a: _Session, b: _Session, hubs: set[str]) -> tuple[float, str, str] | None:
    """Return (confidence, evidence_id, rule) for the strongest matching rule."""
    best: tuple[float, str, str] | None = None
    read_after = b.reads & a.modified
    if read_after:
        best = (READ_CONFIDENCE, min(read_after), "read_after_modify")
    shared = ((a.modified | a.commits) & (b.modified | b.commits)) - hubs
    if len(shared) >= MIN_SHARED:
        confidence = round(
            min(SHARED_MAX_CONFIDENCE, SHARED_BASE_CONFIDENCE + SHARED_STEP * (len(shared) - MIN_SHARED)),
            2,
        )
        if best is None or confidence > best[0]:
            best = (confidence, min(shared), "shared_targets")
    return best


def derive_handovers(
    db: LinkStoreDB, hub_max_sessions: int = DEFAULT_HUB_MAX_SESSIONS
) -> dict[str, int]:
    """Recompute all handed_over_to edges and expire those that no longer qualify.

    A pair (A, B) needs: no explicit continued_in/derived_from either way, not the
    same parent session, 0 <= start(B) - end(A) <= 48h, a shared repo, and either
    B reading something A modified or >= 2 shared non-hub modified files/commits.
    A shared non-default branch needs no separate check: it implies a shared repo.
    """
    sessions = _load_sessions(db)
    explicit = _explicit_pairs(db)
    popularity = Counter(t for s in sessions.values() for t in s.modified | s.commits)
    hubs = {target for target, count in popularity.items() if count > hub_max_sessions}

    timed = sorted(
        (s for s in sessions.values() if s.start is not None),
        key=lambda s: (s.start, s.node_id),
    )
    starts = [s.start for s in timed]

    desired: dict[tuple[str, str, str], tuple[float, str, str]] = {}
    for a in timed:
        for index in range(bisect_left(starts, a.end), len(timed)):
            b = timed[index]
            if b.start - a.end > MAX_GAP:
                break
            if a.root == b.root or frozenset((a.node_id, b.node_id)) in explicit:
                continue
            # Two instantaneous sessions at one moment qualify both ways; keep one.
            if b.end == a.start and b.node_id < a.node_id:
                continue
            if not a.repos & b.repos:
                continue
            hit = _score(a, b, hubs)
            if hit:
                desired[(a.node_id, b.node_id, b.start_raw)] = hit

    totals = {"sessions": len(timed), "hubs": len(hubs), "handovers": len(desired), "expired_edges": 0}
    for row in db.conn.execute(
        "SELECT src_id, dst_id, valid_from FROM edges "
        "WHERE source_adapter = ? AND rel = ? AND expired_at IS NULL",
        (SOURCE, REL),
    ).fetchall():
        if (row["src_id"], row["dst_id"], row["valid_from"]) not in desired:
            db.expire_edge(row["src_id"], row["dst_id"], REL, valid_from=row["valid_from"])
            totals["expired_edges"] += 1

    for (src, dst, valid_from), (confidence, target, rule) in sorted(desired.items()):
        evidence = f"shared:{target}"
        db.upsert_edge(
            src,
            dst,
            REL,
            SOURCE,
            valid_from=valid_from,
            source_ref=evidence,
            confidence=confidence,
            metadata={"source": SOURCE, "evidence": evidence, "rule": rule},
        )
    return totals
