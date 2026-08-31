"""Extract and query the session co-touch graph from Claude Code transcripts.

Candidate signal #2 from `2026-08-31 other candidate relatedness signals for
search reranking.md`: notes an agent session's tool calls touch together may
carry the same associative relationship `co_commit.py` mines from git commits,
just observed one step earlier - a session can touch two notes together and
never commit, or commit only one of them. The open question that note asks is
whether this is actually true, or whether a session that touches two notes
together almost always also commits them together, making this redundant.

Mechanically this is `co_commit.py` with the git log replaced by the session
index `index_sessions.py` already built: instead of `git log --name-only`
grouping files by commit, this groups a transcript's tool-call `file_path`/
`notebook_path` arguments (already extracted into that index's `edges` table,
`resolved_target_path IS NULL` marking a file-touch edge rather than a
wikilink or subagent-parent edge) by `source_path`, and applies the same
power-law pairwise weight to each transcript's touched-file set that
`co_commit.py` applies to each commit's changed-file set.

    python skills/pkm-metadata-indexer/co_touch.py --vault-dir <private-vault> --vault private-vault
    python skills/pkm-metadata-indexer/co_touch.py --compare-co-commit --vault private-vault
    python skills/pkm-metadata-indexer/co_touch.py --selfcheck

Weighting: identical to `co_commit.py`, imported rather than re-derived -
`touch_weight = max(0.005, 1.0 / (N - 1) ** 1.5)` where N is the number of
distinct notes one transcript touched. No concrete reason found to treat a
session differently: a focused session touching 2-3 notes is exactly as
intimate a relationship as a focused commit touching 2-3 files, and a session
that reads/edits half the vault (a broad refactor, an agent doing wide
research) floods pairs the same way a bulk import commit does, so it gets the
same floor and the same `MAX_SESSION_FILES` skip-entirely cutoff.

Incremental by checkpoint, adapted for transcripts rather than commit SHAs: a
git commit is immutable the moment it is scanned, so `co_commit.py` can just
remember the newest SHA it saw and never look at older ones again. A
transcript is append-only and can still be growing when this runs, so instead
of a single high-water mark this remembers the *set* of transcripts already
scanned (`touch_scan_state`) and skips exactly those on a repeat run.

# ponytail: a transcript that grows after being scanned keeps the touched-file
# set it had at first-scan time until `--rebuild` is passed; a session still
# open when this runs undercounts until then. Upgrade path if this gets wired
# in: store each transcript's file count in the checkpoint and reprocess only
# the ones whose count changed, the way a real diff would, instead of an
# all-or-nothing rebuild.
"""

import argparse
import sqlite3
import sys
from collections import defaultdict
from datetime import datetime
from itertools import combinations
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).resolve().parent))

import index_pkm_meta as pkm
from co_commit import calculate_commit_weight as touch_weight

DEFAULT_DB = Path.home() / ".pkm" / "co_touch.db"
DEFAULT_CO_COMMIT_DB = Path.home() / ".pkm" / "co_commit.db"
DEFAULT_VAULT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SESSIONS_ROOT = Path.home() / ".claude" / "projects"

# Same reasoning as co_commit.py's MAX_COMMIT_FILES: a session that touches
# more files than this (a vault-wide reformat, an agent surveying half the
# notes) is pure noise for pairwise association, and C(N, 2) rows for it would
# swamp the genuinely intimate small sessions the signal exists to find.
MAX_SESSION_FILES = 200


def connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path, timeout=30.0)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS co_touch (
            vault TEXT NOT NULL,
            note_a TEXT NOT NULL,
            note_b TEXT NOT NULL,
            weight REAL NOT NULL,
            touch_count INTEGER NOT NULL,
            last_touch TEXT NOT NULL,
            last_session TEXT NOT NULL,
            PRIMARY KEY (vault, note_a, note_b)
        )
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_ct_note_a ON co_touch(vault, note_a);")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_ct_note_b ON co_touch(vault, note_b);")
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS touch_scan_state (
            vault TEXT NOT NULL,
            source_path TEXT NOT NULL,
            scanned_at TEXT NOT NULL,
            PRIMARY KEY (vault, source_path)
        )
        """
    )
    return conn


def relative_touch_path(raw_target: str, vault_root: Path) -> str | None:
    """A tool's `file_path` argument, cut down to a vault-relative note path.

    None for anything outside `vault_root` (another project's file, a temp
    file, a memory note) or not a `.md` file - co_commit.py's edges are
    git-scanned `.md` files only, so this has to match that shape to be
    comparable at all.
    """
    try:
        path = Path(raw_target)
        if not path.is_absolute():
            return None
        path = path.resolve()
    except (OSError, ValueError):
        return None
    try:
        rel = path.relative_to(vault_root)
    except ValueError:
        return None
    if rel.suffix.lower() != ".md":
        return None
    return rel.as_posix()


def iter_session_touches(sessions_db: Path, vault_root: Path):
    """Yield (source_path, sorted distinct vault-relative note paths) for every
    transcript that touched 2+ notes under `vault_root`."""
    conn = sqlite3.connect(f"file:{sessions_db}?mode=ro", uri=True)
    try:
        rows = conn.execute(
            "SELECT source_path, raw_target FROM edges WHERE resolved_target_path IS NULL"
        ).fetchall()
    finally:
        conn.close()
    by_session = defaultdict(set)
    for source_path, raw_target in rows:
        rel = relative_touch_path(raw_target, vault_root)
        if rel:
            by_session[source_path].add(rel)
    for source_path, files in by_session.items():
        if len(files) >= 2:
            yield source_path, sorted(files)


def session_mtime(sessions_root: Path, source_path: str) -> str:
    """The transcript's own mtime stands in for a commit date - sessions have
    no equivalent of `git log`'s per-commit timestamp in the edges table."""
    try:
        ts = (sessions_root / source_path).stat().st_mtime
        return datetime.fromtimestamp(ts).isoformat(sep=" ", timespec="seconds")
    except OSError:
        return "unknown"


def update_co_touch(db_path: Path, sessions_db: Path, sessions_root: Path, vault_root: Path,
                    vault_name: str = "root", rebuild: bool = False) -> tuple[int, int, int]:
    """Mine the session index and update the co_touch edge table.

    Incremental by default: a transcript already in `touch_scan_state` is
    skipped, so a repeat run only pays for sessions new since the last one.
    `--rebuild` clears both tables for this vault and starts over.
    """
    conn = connect(db_path)
    try:
        with conn:
            if rebuild:
                conn.execute("DELETE FROM co_touch WHERE vault = ?", (vault_name,))
                conn.execute("DELETE FROM touch_scan_state WHERE vault = ?", (vault_name,))
                done = set()
            else:
                done = {row[0] for row in conn.execute(
                    "SELECT source_path FROM touch_scan_state WHERE vault = ?", (vault_name,)
                )}

            weights = defaultdict(float)
            counts = defaultdict(int)
            last_touch = {}
            last_session = {}
            new_state_rows = []
            sessions_scanned = 0
            skipped_bulk = 0

            for source_path, files in iter_session_touches(sessions_db, vault_root):
                if source_path in done:
                    continue
                sessions_scanned += 1
                touched_at = session_mtime(sessions_root, source_path)
                new_state_rows.append((vault_name, source_path, touched_at))
                if len(files) > MAX_SESSION_FILES:
                    skipped_bulk += 1
                    continue
                w = touch_weight(len(files))
                for a, b in combinations(files, 2):
                    pair = (a, b)
                    weights[pair] += w
                    counts[pair] += 1
                    last_touch[pair] = touched_at
                    last_session[pair] = source_path

            rows = [
                (vault_name, a, b, round(weights[(a, b)], 4), counts[(a, b)],
                 last_touch[(a, b)], last_session[(a, b)])
                for (a, b) in weights
            ]
            conn.executemany(
                """
                INSERT INTO co_touch (vault, note_a, note_b, weight, touch_count, last_touch, last_session)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(vault, note_a, note_b) DO UPDATE SET
                    weight = co_touch.weight + excluded.weight,
                    touch_count = co_touch.touch_count + excluded.touch_count,
                    last_touch = excluded.last_touch,
                    last_session = excluded.last_session
                """,
                rows,
            )
            conn.executemany(
                "INSERT OR REPLACE INTO touch_scan_state (vault, source_path, scanned_at) VALUES (?, ?, ?)",
                new_state_rows,
            )

        edge_count = conn.execute("SELECT count(*) FROM co_touch WHERE vault = ?", (vault_name,)).fetchone()[0]
        return sessions_scanned, edge_count, skipped_bulk
    finally:
        conn.close()


def hub_notes(db_path: Path, vault: str = "", degree_threshold: int = 20) -> set[str]:
    """Notes with more than `degree_threshold` distinct co-touch partners.

    Same mitigation as co_commit.py's hub_notes: a session's "current project"
    doc or an AGENTS.md/memory.md-style file gets touched alongside whatever
    else that session happened to work on, and inflates degree without being a
    genuine association.
    """
    conn = connect(db_path)
    try:
        clause = "WHERE vault = ?" if vault else ""
        params = (vault,) if vault else ()
        rows = conn.execute(
            f"""
            SELECT note, COUNT(*) AS degree FROM (
                SELECT note_a AS note FROM co_touch {clause}
                UNION ALL
                SELECT note_b AS note FROM co_touch {clause}
            )
            GROUP BY note HAVING degree > ?
            """,
            params + params + (degree_threshold,),
        ).fetchall()
        return {note for note, _ in rows}
    finally:
        conn.close()


def heaviest_edges(db_path: Path, vault: str = "", top: int = 25) -> list[tuple]:
    conn = connect(db_path)
    try:
        clause = "WHERE vault = ?" if vault else ""
        params = (vault, top) if vault else (top,)
        return conn.execute(
            f"SELECT vault, note_a, note_b, weight, touch_count, last_touch FROM co_touch {clause} "
            f"ORDER BY weight DESC LIMIT ?",
            params,
        ).fetchall()
    finally:
        conn.close()


def load_edge_set(db_path: Path, table: str, vault: str = "") -> set[tuple[str, str, str]]:
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        clause = "WHERE vault = ?" if vault else ""
        params = (vault,) if vault else ()
        return {(v, a, b) for v, a, b in conn.execute(
            f"SELECT vault, note_a, note_b FROM {table} {clause}", params
        )}
    finally:
        conn.close()


def compare_with_co_commit(co_touch_db: Path, co_commit_db: Path, vault: str = "") -> dict:
    """The redundancy check the note asks for: plain set overlap between the
    two edge tables, same shape as shared_neighbor_experiment.py's overlap
    with vector neighbours, just between two graph edge sets instead of a
    graph metric and a vector similarity ranking."""
    touch_edges = load_edge_set(co_touch_db, "co_touch", vault)
    commit_edges = load_edge_set(co_commit_db, "co_commits", vault)
    overlap = touch_edges & commit_edges
    distinct = touch_edges - commit_edges
    return {
        "vault": vault or "(all)",
        "co_touch_edges": len(touch_edges),
        "co_commit_edges": len(commit_edges),
        "overlap_edges": len(overlap),
        "overlap_pct": round(100 * len(overlap) / len(touch_edges), 1) if touch_edges else None,
        "co_touch_only_edges": len(distinct),
        "co_touch_only_pct": round(100 * len(distinct) / len(touch_edges), 1) if touch_edges else None,
    }


def selfcheck():
    assert touch_weight(1) == 0.0, "1 file has 0 co-touch weight"
    assert abs(touch_weight(2) - 1.0) < 1e-6, "2 files get 1.0 weight"
    assert touch_weight(100) == 0.005, "bulk session hits 0.5% floor"

    import tempfile
    with tempfile.TemporaryDirectory() as temp:
        db = Path(temp) / "test_co_touch.db"
        conn = connect(db)
        with conn:
            conn.execute(
                "INSERT INTO co_touch VALUES ('v', 'a.md', 'b.md', 3.5, 5, '2026-08-31 00:00:00', 's1.jsonl')"
            )
            conn.execute(
                "INSERT INTO co_touch VALUES ('v', 'a.md', 'c.md', 1.2, 2, '2026-08-30 00:00:00', 's2.jsonl')"
            )
            # d.md touches 3 other notes in one hub-like session: d is a hub at
            # degree_threshold=2, e/f/g are not.
            conn.executemany(
                "INSERT INTO co_touch VALUES ('v', ?, ?, 1.0, 1, '2026-08-31 00:00:00', 's3.jsonl')",
                [("d.md", "e.md"), ("d.md", "f.md"), ("d.md", "g.md")],
            )
        conn.close()  # Windows will not delete the temp dir with the file still open
        assert hub_notes(db, "v", degree_threshold=2) == {"d.md"}

        heaviest = heaviest_edges(db, "v", top=1)
        assert heaviest[0][1] == "a.md" and heaviest[0][2] == "b.md"

        commit_db = Path(temp) / "test_co_commit.db"
        cconn = sqlite3.connect(commit_db)
        with cconn:
            cconn.execute(
                "CREATE TABLE co_commits (vault TEXT, note_a TEXT, note_b TEXT, weight REAL, "
                "commit_count INTEGER, last_commit TEXT, last_sha TEXT)"
            )
            # Only a.md<->b.md is also a co-commit edge; the other 4 co_touch
            # edges (a-c, d-e, d-f, d-g) exist only in co_touch.
            cconn.execute("INSERT INTO co_commits VALUES ('v', 'a.md', 'b.md', 3.5, 5, '2026-08-31', 'abc1234')")
        cconn.close()

        result = compare_with_co_commit(db, commit_db, vault="v")
        assert result["co_touch_edges"] == 5
        assert result["co_commit_edges"] == 1
        assert result["overlap_edges"] == 1
        assert result["overlap_pct"] == 20.0
        assert result["co_touch_only_edges"] == 4
        assert result["co_touch_only_pct"] == 80.0
    print("co_touch.py selfcheck ok")


def main():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--db", type=Path, default=DEFAULT_DB, help=f"SQLite database (default: {DEFAULT_DB})")
    parser.add_argument("--co-commit-db", type=Path, default=DEFAULT_CO_COMMIT_DB,
                        help=f"co_commit.py's database, for --compare-co-commit (default: {DEFAULT_CO_COMMIT_DB})")
    parser.add_argument("--sessions-root", type=Path, default=DEFAULT_SESSIONS_ROOT,
                        help=f"Claude Code transcript root (default: {DEFAULT_SESSIONS_ROOT})")
    parser.add_argument("--sessions-db", type=Path, default=None,
                        help="index_sessions.py's database, defaults to <sessions-root>/.pkm_index.db")
    parser.add_argument("--vault-dir", type=Path, default=None, help="Root directory of the vault to match touches against")
    parser.add_argument("--vault", default="root", help="Vault/corpus identifier name")
    parser.add_argument("--top", type=int, default=25, help="Number of results to display")
    parser.add_argument("--rebuild", action="store_true", help="Rebuild edge table from all indexed sessions")
    parser.add_argument("--hub-degree", type=int, default=20,
                        help="A note with more distinct co-touch partners than this counts as a hub")
    parser.add_argument("--compare-co-commit", action="store_true",
                        help="Measure overlap between co_touch and co_commit edges instead of building")
    parser.add_argument("--selfcheck", action="store_true", help="Run internal validation unit tests")
    args = parser.parse_args()

    if args.selfcheck:
        return selfcheck()

    if args.compare_co_commit:
        import json
        result = compare_with_co_commit(args.db, args.co_commit_db, args.vault if args.vault != "root" else "")
        print(json.dumps(result, indent=1))
        return

    vault_dir = (args.vault_dir or DEFAULT_VAULT_ROOT).resolve()
    sessions_root = args.sessions_root.expanduser().resolve()
    sessions_db = args.sessions_db or pkm.default_db_path(sessions_root)

    print(f"Scanning session index {sessions_db} for touches under {vault_dir} ...")
    scanned, edges, skipped = update_co_touch(args.db, sessions_db, sessions_root, vault_dir, args.vault, args.rebuild)
    print(f"Processed {scanned:,} new multi-file sessions ({skipped:,} bulk sessions over "
          f"{MAX_SESSION_FILES} files skipped) -> {edges:,} co-touch edges stored in {args.db}\n")

    rows = heaviest_edges(args.db, args.vault, args.top)
    if not rows:
        print("No co-touch edges found.")
        return
    print(f"--- Top {len(rows)} Heaviest Co-Touch Associations ---")
    max_w = rows[0][3] if rows else 1.0
    for vault, note_a, note_b, weight, count, last_date in rows:
        bar = "█" * max(1, round(8 * weight / max(0.001, max_w)))
        print(f"{weight:6.2f} pts ({count:2d} touches)  {bar:<8}  [{vault}] {note_a} <---> {note_b}")


if __name__ == "__main__":
    main()
