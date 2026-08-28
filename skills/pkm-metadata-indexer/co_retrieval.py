"""Accumulate co-retrieval edges from the query log: notes returned together.

Two notes that keep coming back in the same result set are related in a way the
text does not say, and nothing in the index records that. `searchd.py` logs the
result paths of every `/search` and `/similar` call, so the association is
derivable after the fact: read the log, add a point to every pair of notes that
shared a result set, let old points fade.

    python skills/pkm-metadata-indexer/co_retrieval.py
    python skills/pkm-metadata-indexer/co_retrieval.py --vault brain --top 40
    python skills/pkm-metadata-indexer/co_retrieval.py --rebuild
    python skills/pkm-metadata-indexer/co_retrieval.py --selfcheck

A run consumes whatever the log has gained since the last run and prints the
heaviest edges. Weight is a decaying count:

    weight = weight * 0.5 ** (days_since_last_seen / 30) + 1

so a pair seen once today is worth 1, a pair seen once 30 days ago is worth
0.5, and a pair seen twice 30 days apart is worth 1.5. Decaying on update, from
the row's own `last_seen`, is what makes the incremental run equal the rebuild:
there is no pass that has to touch every row when time passes, and a reader
decays from `last_seen` to now the same way.

Edges live in `~/.pkm/co_retrieval.db`, beside the log rather than inside the
vault index, for the reason the log is not in the index either: a reindex
rebuilds the index, and history a reindex deletes is not history.

Nothing reads these edges yet. Wiring them into ranking is a separate change
and it goes through `eval_rerank.py` first, or it is an opinion rather than an
improvement.
"""

import argparse
import json
import sqlite3
import sys
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

QUERY_LOG = Path.home() / ".pkm" / "queries.jsonl"
EDGE_DB = Path.home() / ".pkm" / "co_retrieval.db"
# One knob: how fast an association cools. The same half-life as mention_heatmap.
HALF_LIFE_DAYS = 30


def decay(weight: float, days: float) -> float:
    """Registered as a SQLite function, so no math extension is needed."""
    return weight * 0.5 ** (max(0.0, days) / HALF_LIFE_DAYS)


def connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(db_path)
    connection.create_function("decay", 2, decay)
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS co_retrieval (
            vault TEXT NOT NULL,
            note_a TEXT NOT NULL,
            note_b TEXT NOT NULL,
            weight REAL NOT NULL,
            last_seen TEXT NOT NULL,
            PRIMARY KEY (vault, note_a, note_b)
        )
        """
    )
    # Byte offset already folded in, so a run costs only what the log gained.
    connection.execute(
        "CREATE TABLE IF NOT EXISTS log_state ("
        "log TEXT PRIMARY KEY, offset INTEGER NOT NULL, queries INTEGER NOT NULL)"
    )
    return connection


def read_new(log_path: Path, offset: int) -> tuple[list[str], int]:
    """Complete lines added since `offset`, and the offset past them.

    Read as bytes: the log is written in text mode, so on Windows a line ends
    with two bytes and a character count would drift out of the file. A trailing
    half-written line is left for the next run rather than parsed.
    """
    if not log_path.exists():
        return [], 0
    if log_path.stat().st_size < offset:  # truncated or rotated, start over
        offset = 0
    with log_path.open("rb") as handle:
        handle.seek(offset)
        data = handle.read()
    end = data.rfind(b"\n") + 1
    lines = [raw.decode("utf-8", "replace") for raw in data[:end].splitlines() if raw.strip()]
    return lines, offset + end


def pairs(results: list) -> list[tuple[str, str]]:
    """Every unordered pair of the distinct notes in one result set.

    A note can appear more than once in a result set, once per matching section,
    and that is one note rather than a note associated with itself.
    """
    # ponytail: O(n^2) in the result limit, which searchd caps at 100, so 4950
    # pairs is the worst one query can cost. Cap the depth if that stops being fine.
    notes = sorted(dict.fromkeys(results))
    return [(a, b) for index, a in enumerate(notes) for b in notes[index + 1:]]


def fold(connection: sqlite3.Connection, lines: list[str]) -> int:
    """Add one point to every pair in every logged query. Returns queries folded."""
    folded = 0
    for line in lines:
        try:
            row = json.loads(line)
            vault, when = row["vault"], row["t"]
            found = pairs(row.get("results") or [])
        except (ValueError, KeyError, TypeError):
            continue  # a truncated or foreign line is not worth failing a run over
        if not found:
            continue
        connection.executemany(
            """
            INSERT INTO co_retrieval (vault, note_a, note_b, weight, last_seen)
            VALUES (?, ?, ?, 1.0, ?)
            ON CONFLICT(vault, note_a, note_b) DO UPDATE SET
                weight = decay(weight, julianday(excluded.last_seen) - julianday(last_seen)) + 1.0,
                last_seen = excluded.last_seen
            """,
            [(vault, a, b, when) for a, b in found],
        )
        folded += 1
    return folded


def update(db_path: Path, log_path: Path, rebuild: bool = False) -> tuple[int, int]:
    """Fold the unread tail of the log into the edge table. Returns (queries, edges)."""
    connection = connect(db_path)
    try:
        with connection:
            if rebuild:
                connection.execute("DELETE FROM co_retrieval")
                connection.execute("DELETE FROM log_state")
            state = connection.execute(
                "SELECT offset, queries FROM log_state WHERE log = ?", (str(log_path),)
            ).fetchone() or (0, 0)
            lines, offset = read_new(log_path, state[0])
            folded = fold(connection, lines)
            connection.execute(
                "INSERT INTO log_state (log, offset, queries) VALUES (?, ?, ?) "
                "ON CONFLICT(log) DO UPDATE SET offset = excluded.offset, queries = excluded.queries",
                (str(log_path), offset, state[1] + folded),
            )
        edges = connection.execute("SELECT count(*) FROM co_retrieval").fetchone()[0]
        return folded, edges
    finally:
        connection.close()


def heaviest(db_path: Path, vault: str = "", top: int = 25) -> list[tuple]:
    """Edges by weight decayed to now, which is how a reader has to see them."""
    connection = connect(db_path)
    try:
        clause = "WHERE vault = ?" if vault else ""
        return connection.execute(
            "SELECT vault, note_a, note_b, "
            "decay(weight, julianday('now', 'localtime') - julianday(last_seen)) AS now_weight, "
            f"last_seen FROM co_retrieval {clause} ORDER BY now_weight DESC, note_a, note_b LIMIT ?",
            ((vault, top) if vault else (top,)),
        ).fetchall()
    finally:
        connection.close()


def selfcheck():
    import tempfile

    assert pairs(["b.md", "a.md"]) == [("a.md", "b.md")], "pairs are unordered and sorted"
    assert pairs(["a.md", "a.md"]) == [], "one note twice is not a pair with itself"
    assert pairs(["a.md"]) == [] and pairs([]) == [], "a lone result associates with nothing"
    assert len(pairs(["a.md", "b.md", "c.md"])) == 3, "three notes make three pairs"
    assert decay(1.0, 0) == 1.0 and decay(1.0, HALF_LIFE_DAYS) == 0.5, "half life is the half life"
    assert decay(1.0, -5) == 1.0, "a log row out of order must not grow a weight"

    with tempfile.TemporaryDirectory() as temp:
        log = Path(temp) / "queries.jsonl"
        db = Path(temp) / "edges.db"

        def write(when, vault, results):
            with log.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps({"t": when, "kind": "search", "vault": vault,
                                         "q": "x", "results": results}) + "\n")

        def stored():
            """Undecayed weights, so an assert does not depend on today's date."""
            connection = connect(db)
            try:
                return {row[:3]: row[3] for row in connection.execute(
                    "SELECT vault, note_a, note_b, weight FROM co_retrieval")}
            finally:
                connection.close()

        assert update(db, log) == (0, 0), "no log yet is not an error, it is no edges"

        write("2026-07-01T10:00:00", "v", ["a.md", "b.md", "b.md"])
        assert update(db, log) == (1, 1), "one query over two distinct notes is one edge"
        assert update(db, log) == (0, 1), "the same log read twice must not double a weight"

        write("2026-07-31T10:00:00", "v", ["a.md", "b.md"])
        write("2026-07-31T10:00:00", "other", ["a.md", "b.md"])
        assert update(db, log) == (2, 2), "the same pair in another vault is another edge"
        raw = stored()
        assert abs(raw[("v", "a.md", "b.md")] - 1.5) < 1e-9, \
            f"one point 30 days on plus one is 1.5, got {raw[('v', 'a.md', 'b.md')]}"
        shown = {row[0]: row[3] for row in heaviest(db, top=10)}
        assert shown["v"] < 1.5 and shown["other"] < 1.0, "a reader sees weight decayed to now"
        assert abs(shown["v"] / shown["other"] - 1.5) < 1e-6, \
            "two edges last seen the same day decay by the same factor"
        assert [row[0] for row in heaviest(db, vault="other", top=10)] == ["other"], \
            "--vault shows one vault"

        with log.open("ab") as handle:  # a write caught mid-line
            handle.write(b'{"t": "2026-08-01T10:00:00", "vault": "v", "resul')
        assert update(db, log) == (0, 2), "a half-written last line waits for the next run"
        with log.open("ab") as handle:
            handle.write(b'ts": ["a.md", "c.md"]}\n')
        assert update(db, log) == (1, 3), "and is folded once it is complete"

        incremental = stored()
        update(db, log, rebuild=True)
        assert stored() == incremental, "a rebuild from the whole log equals the incremental runs"
    print("selfcheck ok")


def main():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--log", type=Path, default=QUERY_LOG, help="searchd's query log")
    parser.add_argument("--db", type=Path, default=EDGE_DB, help="where edges accumulate")
    parser.add_argument("--vault", default="", help="only show edges from this vault")
    parser.add_argument("--top", type=int, default=25)
    parser.add_argument("--rebuild", action="store_true",
                        help="drop the edges and replay the whole log")
    parser.add_argument("--selfcheck", action="store_true")
    args = parser.parse_args()

    if args.selfcheck:
        return selfcheck()

    folded, edges = update(args.db, args.log, args.rebuild)
    print(f"folded {folded} queries from {args.log}, {edges} edges in {args.db}")
    rows = heaviest(args.db, args.vault, args.top)
    if not rows:
        print("no co-retrieval yet. run some searches through searchd.py and come back.")
        return
    heaviest_weight = rows[0][3]
    for vault, note_a, note_b, weight, last_seen in rows:
        bar = "█" * max(1, round(8 * weight / heaviest_weight))
        print(f"{weight:6.2f}  {bar:<8}  {last_seen[:10]}  [{vault}] {note_a}  ~  {note_b}")


if __name__ == "__main__":
    main()
