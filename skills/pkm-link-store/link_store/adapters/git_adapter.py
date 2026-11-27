"""Incremental Git repository adapter for pkm-link-store."""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

from ..canonical_ids import branch_id, commit_id, repo_id, session_id, strip_branch_ref
from ..db import SHORT_SESSION_RE, LinkStoreDB
from . import BoundaryPolicy

MAX_COMMIT_FILES = 200
_SESSION_TRAILER_RE = re.compile(r"(?im)^Session:\s*(?:session:)?([A-Za-z0-9_-]+(?::agent-[A-Za-z0-9_-]+)?)\s*$")


def _run_git(repo_path: Path, args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(repo_path), *args],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )


def _detect_default_branch(repo_path: Path, local_branches: list[str]) -> str | None:
    sym = _run_git(repo_path, ["symbolic-ref", "--short", "refs/remotes/origin/HEAD"])
    if sym.returncode == 0 and sym.stdout.strip():
        return strip_branch_ref(f"refs/remotes/{sym.stdout.strip()}")
    for candidate in ("main", "master"):
        if candidate in local_branches:
            return candidate
    return local_branches[0] if local_branches else None


def _resolve_trailer_session(db: LinkStoreDB, token: str) -> str | None:
    """Session node for a Session: trailer value.

    An 8-char value resolves through its alias, then a unique id prefix, and
    returns None rather than creating a stub when neither identifies one session.
    """
    aliased = db.resolve_alias(token)
    if not SHORT_SESSION_RE.fullmatch(token):
        resolved = aliased or f"session:{token}"
        if not db.get_node(resolved):
            db.upsert_node(resolved, "Session", title=token)
        return resolved

    for candidate in (aliased, db.resolve_alias(token.lower())):
        node = db.get_node(candidate) if candidate else None
        if node and node["node_type"] == "Session" and node["expired_at"] is None:
            return candidate
    matches = db.find_sessions_by_prefix(token)
    if len(matches) == 1:
        return matches[0]
    if matches:
        return None
    # A stub that already exists (e.g. from a session note) is still a valid target.
    stub = db.get_node(f"session:{token}")
    return stub["id"] if stub and stub["expired_at"] is None else None


def _link_trailer(
    db: LinkStoreDB, cid: str, token: str, author_iso: str, sha40: str
) -> bool:
    session_node = _resolve_trailer_session(db, token)
    if session_node is None:
        return False
    db.upsert_edge(
        cid,
        session_node,
        "mentions_session",
        "git_adapter",
        valid_from=author_iso,
        source_ref=sha40,
    )
    return True


def sync_git_repo(
    db: LinkStoreDB,
    repo_name: str,
    repo_path: Path | str,
    policy: BoundaryPolicy | None = None,
    max_commits: int | None = None,
) -> dict[str, int]:
    """Incrementally ingest branches, commits, changed files, and Session: trailers."""
    root = Path(repo_path).expanduser().resolve()
    pol = policy or BoundaryPolicy()
    totals = {
        "branches": 0,
        "expired_branches": 0,
        "commits": 0,
        "edges": 0,
        "skipped_large": 0,
        "unresolved_trailers": 0,
    }
    if not root.exists() or not pol.is_allowed(root):
        return totals

    rem = _run_git(root, ["remote", "get-url", "origin"])
    remote_url = rem.stdout.strip() if rem.returncode == 0 else None
    rid = repo_id(remote_url=remote_url, fallback_name=repo_name)
    db.upsert_node(rid, "Repo", title=repo_name, metadata={"path": str(root)})

    refs_res = _run_git(root, ["for-each-ref", "--format=%(refname)", "refs/heads"])
    full_refs = [line.strip() for line in refs_res.stdout.splitlines() if line.strip()]
    short_branches = [strip_branch_ref(ref) for ref in full_refs]
    default_branch = _detect_default_branch(root, short_branches)

    active_branch_ids: set[str] = set()
    for full_ref, short in zip(full_refs, short_branches):
        bid = branch_id(rid, full_ref)
        active_branch_ids.add(bid)
        is_default = short == default_branch
        db.upsert_node(
            bid,
            "Branch",
            title=short,
            metadata={"branch": short, "is_default": is_default},
        )
        db.upsert_edge(bid, rid, "in_repo", "git_adapter", source_ref=full_ref)
        totals["branches"] += 1
        totals["edges"] += 1

    # Expire branches that belong to this repo and were deleted
    existing_branches = db.conn.execute(
        """
        SELECT e.src_id FROM edges e
        JOIN nodes n ON n.id = e.src_id
        WHERE e.dst_id = ? AND e.rel = 'in_repo'
          AND e.expired_at IS NULL AND n.node_type = 'Branch' AND n.expired_at IS NULL
        """,
        (rid,),
    ).fetchall()
    for row in existing_branches:
        if row["src_id"] not in active_branch_ids:
            db.expire_node(row["src_id"])
            totals["expired_branches"] += 1

    # Sync commits per branch incrementally
    state_key = f"git:{rid}"
    state = db.get_sync_state("git_adapter", state_key)
    seen_tips: dict[str, str] = (
        json.loads(state["extra_json"]) if state and state.get("extra_json") else {}
    )

    # Commits are read once, so unresolved short trailers are kept and retried
    # until their transcript shows up.
    pending_key = f"git_pending:{rid}"
    pending_state = db.get_sync_state("git_adapter", pending_key)
    pending: set[tuple[str, str, str, str]] = set()
    if pending_state and pending_state.get("extra_json"):
        for item in json.loads(pending_state["extra_json"]).get("pending", []):
            if _link_trailer(db, *item):
                totals["edges"] += 1
            else:
                pending.add(tuple(item))

    for full_ref, short in zip(full_refs, short_branches):
        bid = branch_id(rid, full_ref)
        tip_res = _run_git(root, ["rev-parse", full_ref])
        if tip_res.returncode != 0:
            continue
        tip_sha = tip_res.stdout.strip()
        prev_tip = seen_tips.get(short)
        if prev_tip == tip_sha:
            continue

        rev_range = f"{prev_tip}..{full_ref}" if prev_tip else full_ref
        log_args = [
            "log",
            "--format=%x1e%H%x1f%aI%x1f%s%x1f%b%x1f",
            "--name-only",
        ]
        if max_commits and not prev_tip:
            log_args.extend(["-n", str(max_commits)])
        log_args.append(rev_range)

        log_res = _run_git(root, log_args)
        if log_res.returncode != 0:
            continue

        for entry in log_res.stdout.split("\x1e"):
            entry = entry.strip()
            if not entry:
                continue
            parts = entry.split("\x1f", 4)
            if len(parts) < 4:
                continue
            sha40, author_iso, subject, body = parts[0].strip(), parts[1].strip(), parts[2].strip(), parts[3]
            files_blob = parts[4] if len(parts) > 4 else ""
            if len(sha40) != 40:
                continue

            cid = commit_id(rid, sha40)
            db.upsert_node(cid, "Commit", title=subject[:120], metadata={"sha": sha40})
            db.upsert_edge(cid, rid, "in_repo", "git_adapter", valid_from=author_iso, source_ref=sha40)
            db.upsert_edge(cid, bid, "on_branch", "git_adapter", valid_from=author_iso, source_ref=sha40)
            totals["commits"] += 1
            totals["edges"] += 2

            for sess_match in _SESSION_TRAILER_RE.findall(body):
                if _link_trailer(db, cid, sess_match, author_iso, sha40):
                    totals["edges"] += 1
                else:
                    pending.add((cid, sess_match, author_iso, sha40))

            changed_files = [f.strip() for f in files_blob.splitlines() if f.strip()]
            if len(changed_files) > MAX_COMMIT_FILES:
                totals["skipped_large"] += 1
                continue

            for rel_fp in changed_files:
                abs_fp = root / rel_fp
                target = pol.resolve_target(abs_fp, repo_root=root, repo_id_str=rid)
                if target is None:
                    continue
                dst_id, dst_type, dst_title = target
                db.upsert_node(dst_id, dst_type, title=dst_title)
                db.upsert_edge(
                    cid,
                    dst_id,
                    "changed_file",
                    "git_adapter",
                    valid_from=author_iso,
                    source_ref=sha40,
                )
                totals["edges"] += 1

        seen_tips[short] = tip_sha

    db.set_sync_state("git_adapter", state_key, extra=seen_tips)
    db.set_sync_state("git_adapter", pending_key, extra={"pending": sorted(pending)})
    totals["unresolved_trailers"] = len(pending)
    return totals
