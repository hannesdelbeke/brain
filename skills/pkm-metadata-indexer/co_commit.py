"""Extract and query the co-commit graph from Git history.

Notes modified in the same Git commit share an associative relationship that
pure vector semantic search misses (e.g. an art tool pipeline note and an
attention-budget note inspired by the same session).

    python skills/pkm-metadata-indexer/co_commit.py
    python skills/pkm-metadata-indexer/co_commit.py --note "profile.md" --top 15
    python skills/pkm-metadata-indexer/co_commit.py --note "profile.md" --exclude-hubs
    python skills/pkm-metadata-indexer/co_commit.py --rebuild
    python skills/pkm-metadata-indexer/co_commit.py --selfcheck

Mathematical Weighting (pure power-law, no discount for autosave commits):
    commit_weight = max(0.005, 1.0 / (N - 1) ** 1.5)

- Small focused commits (2-3 files) receive high intimate weight (1.0 to 0.35).
- Large bulk commits receive a minimum 0.5% floor (0.005), preserving all co-edits.
- Evergreen accumulation: Historical architectural links do not suffer artificial time decay.

Incremental by default: a run scans only commits after the last checkpoint
(`commit_scan_state.last_scanned_sha`) and adds to what is stored, so a repeat
run costs what changed rather than the whole history. `--rebuild`, or history
being rewritten out from under a stale checkpoint, starts over from empty.
"""

import argparse
import math
import sqlite3
import subprocess
import sys
from collections import defaultdict
from itertools import combinations
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DEFAULT_DB = Path.home() / ".pkm" / "co_commit.db"
DEFAULT_VAULT_ROOT = Path(__file__).resolve().parents[2]

# A commit touching more files than this is skipped entirely rather than
# pairwise-weighted. The floor already pushes its per-pair weight to 0.005,
# but row count is C(N, 2) regardless of weight: measured against a real
# vault, two historical bulk-import commits of ~2,476 files each produced
# 3.13M rows, 95.7% of the whole table, all administrative noise. A genuine
# multi-note restructuring sprint (the case the floor exists to protect) is
# nowhere near this size, so the cutoff only ever drops bulk imports/reformats.
MAX_COMMIT_FILES = 200


def find_vault_root(start_path: Path = None) -> Path:
    curr = (start_path or Path.cwd()).resolve()
    for parent in [curr, *curr.parents]:
        if (parent / ".obsidian").exists() or (parent / ".git").exists():
            return parent
    return curr


def connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS co_commits (
            vault TEXT NOT NULL,
            note_a TEXT NOT NULL,
            note_b TEXT NOT NULL,
            weight REAL NOT NULL,
            commit_count INTEGER NOT NULL,
            last_commit TEXT NOT NULL,
            last_sha TEXT NOT NULL,
            PRIMARY KEY (vault, note_a, note_b)
        )
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_cc_note_a ON co_commits(vault, note_a);")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_cc_note_b ON co_commits(vault, note_b);")
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS commit_scan_state (
            vault TEXT PRIMARY KEY,
            last_scanned_sha TEXT NOT NULL,
            scanned_at TEXT NOT NULL
        )
        """
    )
    return conn


def calculate_commit_weight(num_files: int, commit_msg: str = "") -> float:
    """Pure power-law scaling across all commits without artificial auto-backup discounts."""
    if num_files < 2:
        return 0.0
    return max(0.005, 1.0 / math.pow(num_files - 1, 1.5))


def scan_git_commits(vault_dir: Path, since: str | None = None):
    """Yield (sha, date, msg, list_of_md_files), optionally only commits after `since`."""
    cmd = ["git", "-C", str(vault_dir), "log", "--name-only", "--format=commit %h|%ad|%s", "--date=iso"]
    if since:
        cmd.append(f"{since}..HEAD")
    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, text=True, errors="ignore")
    except Exception as e:
        print(f"Failed to run git log in {vault_dir}: {e}", file=sys.stderr)
        return

    curr_sha, curr_date, curr_msg = None, None, ""
    curr_files = []

    for line in proc.stdout:
        line = line.strip()
        if line.startswith("commit "):
            if curr_sha and curr_files:
                md_files = [f.replace("\\", "/") for f in curr_files if f.endswith(".md")]
                if len(md_files) >= 2:
                    yield curr_sha, curr_date, curr_msg, md_files
            parts = line[7:].split("|", 2)
            curr_sha = parts[0]
            curr_date = parts[1] if len(parts) > 1 else ""
            curr_msg = parts[2] if len(parts) > 2 else ""
            curr_files = []
        elif line:
            curr_files.append(line)

    if curr_sha and curr_files:
        md_files = [f.replace("\\", "/") for f in curr_files if f.endswith(".md")]
        if len(md_files) >= 2:
            yield curr_sha, curr_date, curr_msg, md_files


def checkpoint_valid(vault_dir: Path, sha: str) -> bool:
    """False when `sha` is not an ancestor of HEAD (rewritten history: amend, rebase, filter-repo).

    `git cat-file -e` only proves the object still exists, which an amended or
    rebased commit does until garbage collection actually removes it; `merge-base
    --is-ancestor` is what actually answers whether it is still on this history.
    """
    return subprocess.run(
        ["git", "-C", str(vault_dir), "merge-base", "--is-ancestor", sha, "HEAD"],
        capture_output=True,
    ).returncode == 0


def update_co_commits(db_path: Path, vault_dir: Path, vault_name: str = "root", rebuild: bool = False) -> tuple[int, int]:
    """Mine git history and update SQLite edge table.

    Incremental by default: scans only commits after the last checkpoint and
    adds their weight to what is already stored, so a run costs the size of
    what changed rather than the whole history every time. `--rebuild`, or a
    checkpoint whose commit no longer exists (history was rewritten), starts
    over from an empty table.
    """
    conn = connect(db_path)
    try:
        with conn:
            since = None
            if rebuild:
                conn.execute("DELETE FROM co_commits WHERE vault = ?", (vault_name,))
                conn.execute("DELETE FROM commit_scan_state WHERE vault = ?", (vault_name,))
            else:
                row = conn.execute(
                    "SELECT last_scanned_sha FROM commit_scan_state WHERE vault = ?", (vault_name,)
                ).fetchone()
                if row and checkpoint_valid(vault_dir, row[0]):
                    since = row[0]
                elif row:
                    conn.execute("DELETE FROM co_commits WHERE vault = ?", (vault_name,))

            weights = defaultdict(float)
            counts = defaultdict(int)
            last_dates = {}
            last_shas = {}
            total_commits = 0
            skipped_bulk = 0
            latest_sha = None

            for sha, date, msg, files in scan_git_commits(vault_dir, since=since):
                if not latest_sha:
                    latest_sha = sha
                total_commits += 1
                unique_files = sorted(set(files))
                if len(unique_files) > MAX_COMMIT_FILES:
                    skipped_bulk += 1
                    continue
                w = calculate_commit_weight(len(unique_files), msg)
                for a, b in combinations(unique_files, 2):
                    pair = (a, b)
                    weights[pair] += w
                    counts[pair] += 1
                    if pair not in last_dates:
                        last_dates[pair] = date
                        last_shas[pair] = sha

            rows = [
                (vault_name, a, b, round(weights[(a, b)], 4), counts[(a, b)], last_dates[(a, b)], last_shas[(a, b)])
                for (a, b) in weights
            ]

            # A commit found here is always newer than whatever is stored, since
            # scanning started at the last checkpoint: weight and commit_count
            # accumulate, last_commit/last_sha simply take the newer value.
            conn.executemany(
                """
                INSERT INTO co_commits (vault, note_a, note_b, weight, commit_count, last_commit, last_sha)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(vault, note_a, note_b) DO UPDATE SET
                    weight = co_commits.weight + excluded.weight,
                    commit_count = co_commits.commit_count + excluded.commit_count,
                    last_commit = excluded.last_commit,
                    last_sha = excluded.last_sha
                """,
                rows,
            )

            if latest_sha:
                conn.execute(
                    "INSERT INTO commit_scan_state (vault, last_scanned_sha, scanned_at) VALUES (?, ?, datetime('now')) "
                    "ON CONFLICT(vault) DO UPDATE SET last_scanned_sha = excluded.last_scanned_sha, scanned_at = excluded.scanned_at",
                    (vault_name, latest_sha),
                )

        edge_count = conn.execute("SELECT count(*) FROM co_commits WHERE vault = ?", (vault_name,)).fetchone()[0]
        return total_commits, edge_count, skipped_bulk
    finally:
        conn.close()


def hub_notes(db_path: Path, vault: str = "", degree_threshold: int = 20) -> set[str]:
    """Notes with more than `degree_threshold` distinct co-commit partners.

    Cheap mitigation for hub inflation: measured against real vault history,
    unfiltered top-weight edges were 63% redundant or hub noise and 7%
    genuinely serendipitous, and a third of the noise was a "current project"
    doc or an AGENTS.md/memory.md-style index file dragging in whatever else
    that session happened to touch. Excluding high-degree notes is a single
    query, not the diff-scaling or submodule-aware rework the architecture
    spec describes for the same problem.
    """
    conn = connect(db_path)
    try:
        clause = "WHERE vault = ?" if vault else ""
        params = (vault,) if vault else ()
        rows = conn.execute(
            f"""
            SELECT note, COUNT(*) AS degree FROM (
                SELECT note_a AS note FROM co_commits {clause}
                UNION ALL
                SELECT note_b AS note FROM co_commits {clause}
            )
            GROUP BY note HAVING degree > ?
            """,
            params + params + (degree_threshold,),
        ).fetchall()
        return {note for note, _ in rows}
    finally:
        conn.close()


def query_associations(db_path: Path, note: str, vault: str = "", top: int = 25,
                       exclude_hubs: bool = False, hub_degree: int = 20) -> list[tuple]:
    """Find notes most strongly co-committed with a given note."""
    conn = connect(db_path)
    try:
        clean_note = note.replace("\\", "/").strip().lower()
        clause = "AND vault = ?" if vault else ""
        params = (vault,) if vault else ()
        fetch_limit = top * 4 if exclude_hubs else top

        # Match exact note path, ending suffix, or basename
        rows = conn.execute(
            f"""
            SELECT vault,
                   CASE WHEN lower(note_a) LIKE ? THEN note_b ELSE note_a END AS associated_note,
                   weight, commit_count, last_commit, last_sha
            FROM co_commits
            WHERE (lower(note_a) = ? OR lower(note_b) = ? OR lower(note_a) LIKE ? OR lower(note_b) LIKE ?) {clause}
            ORDER BY weight DESC, commit_count DESC
            LIMIT ?
            """,
            (f"%{clean_note}", clean_note, clean_note, f"%/{clean_note}", f"%/{clean_note}") + params + (fetch_limit,),
        ).fetchall()
    finally:
        conn.close()
    if exclude_hubs:
        hubs = hub_notes(db_path, vault, hub_degree)
        rows = [row for row in rows if row[1] not in hubs][:top]
    return rows


def heaviest_edges(db_path: Path, vault: str = "", top: int = 25) -> list[tuple]:
    """List globally strongest co-commit edges."""
    conn = connect(db_path)
    try:
        clause = "WHERE vault = ?" if vault else ""
        params = (vault, top) if vault else (top,)
        return conn.execute(
            f"SELECT vault, note_a, note_b, weight, commit_count, last_commit FROM co_commits {clause} "
            f"ORDER BY weight DESC LIMIT ?",
            params,
        ).fetchall()
    finally:
        conn.close()


def selfcheck():
    assert calculate_commit_weight(1) == 0.0, "1 file has 0 co-commit weight"
    assert abs(calculate_commit_weight(2) - 1.0) < 1e-6, "2 files get 1.0 weight"
    assert abs(calculate_commit_weight(3) - 1.0 / (2 ** 1.5)) < 1e-4, "3 files power law"
    assert calculate_commit_weight(100) == 0.005, "bulk commit hits 0.5% floor"

    import tempfile
    with tempfile.TemporaryDirectory() as temp:
        db = Path(temp) / "test_co_commit.db"
        conn = connect(db)
        with conn:
            conn.execute(
                "INSERT INTO co_commits VALUES ('v', 'a.md', 'b.md', 3.5, 5, '2026-08-31', 'abc1234')"
            )
            conn.execute(
                "INSERT INTO co_commits VALUES ('v', 'a.md', 'c.md', 1.2, 2, '2026-08-30', 'def5678')"
            )
        conn.close()  # Windows will not delete the temp dir with the file still open
        assocs = query_associations(db, "a.md", top=5)
        assert len(assocs) == 2
        assert assocs[0][1] == "b.md" and assocs[0][2] == 3.5
        assert assocs[1][1] == "c.md" and assocs[1][2] == 1.2

        heaviest = heaviest_edges(db, top=1)
        assert len(heaviest) == 1
        assert heaviest[0][1] == "a.md" and heaviest[0][2] == "b.md"

        # d.md touches 3 other notes, e/f/g touch only d.md: d is a hub at
        # degree_threshold=2, e/f/g are not.
        conn = connect(db)
        with conn:
            conn.executemany(
                "INSERT INTO co_commits VALUES ('v', ?, ?, 1.0, 1, '2026-08-31', 'aaa0000')",
                [("d.md", "e.md"), ("d.md", "f.md"), ("d.md", "g.md")],
            )
        conn.close()
        assert hub_notes(db, "v", degree_threshold=2) == {"d.md"}
        assert "d.md" not in {row[1] for row in query_associations(
            db, "e.md", vault="v", top=5, exclude_hubs=True, hub_degree=2)}
    print("co_commit.py selfcheck ok")


def main():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--db", type=Path, default=DEFAULT_DB, help=f"SQLite database (default: {DEFAULT_DB})")
    parser.add_argument("--vault-dir", type=Path, default=None, help="Root directory of Git repository to scan")
    parser.add_argument("--vault", default="root", help="Vault/corpus identifier name")
    parser.add_argument("--note", help="Query top co-committed notes for this specific note")
    parser.add_argument("--top", type=int, default=25, help="Number of results to display")
    parser.add_argument("--rebuild", action="store_true", help="Rebuild edge table from entire git history")
    parser.add_argument("--exclude-hubs", action="store_true",
                        help="Drop high-degree notes (current-project docs, AGENTS.md-style index "
                             "files) from --note results, measured to be most of the noise")
    parser.add_argument("--hub-degree", type=int, default=20,
                        help="A note with more distinct co-commit partners than this counts as a hub")
    parser.add_argument("--selfcheck", action="store_true", help="Run internal validation unit tests")
    args = parser.parse_args()

    if args.selfcheck:
        return selfcheck()

    vault_dir = args.vault_dir or find_vault_root()

    if args.note:
        rows = query_associations(args.db, args.note, args.vault, args.top,
                                  args.exclude_hubs, args.hub_degree)
        if not rows:
            print(f"No co-commit associations found for '{args.note}' in {args.db}. (Try running index update first)")
        print(f"\n--- Top Co-Committed Notes for: {args.note} [{args.vault}] ---")
        max_w = rows[0][2] if rows else 1.0
        for vault, associated, weight, count, last_date, last_sha in rows:
            bar = "█" * max(1, round(8 * weight / max(0.001, max_w)))
            print(f"{weight:6.2f} pts ({count:2d} commits)  {bar:<8}  {associated}  (last: {last_date[:10]} @ {last_sha})")
        return

    print(f"Scanning Git history in: {vault_dir} ...")
    commits, edges, skipped = update_co_commits(args.db, vault_dir, args.vault, args.rebuild)
    print(f"Processed {commits:,} multi-file commits ({skipped:,} bulk commits over "
          f"{MAX_COMMIT_FILES} files skipped) -> {edges:,} co-commit edges stored in {args.db}\n")

    rows = heaviest_edges(args.db, args.vault, args.top)
    if not rows:
        print("No co-commit edges found.")
        return

    print(f"--- Top {len(rows)} Heaviest Co-Commit Associations ---")
    max_w = rows[0][3] if rows else 1.0
    for vault, note_a, note_b, weight, count, last_date in rows:
        bar = "█" * max(1, round(8 * weight / max(0.001, max_w)))
        print(f"{weight:6.2f} pts ({count:2d} commits)  {bar:<8}  [{vault}] {note_a} <---> {note_b}")


if __name__ == "__main__":
    main()
