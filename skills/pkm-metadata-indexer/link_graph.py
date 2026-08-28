"""Query the link graph in a pkm_index.db: who points at a file, what nothing points at.

Reads the `edges` table, whichever scanner filled it (vault wikilinks, repo
markdown links and image embeds), and opens the database read-only.

    python skills/pkm-metadata-indexer/link_graph.py refs "src/auth/token.py"
    python skills/pkm-metadata-indexer/link_graph.py refs token.py --db /path/to/pkm_index.db
    python skills/pkm-metadata-indexer/link_graph.py orphans
    python skills/pkm-metadata-indexer/link_graph.py orphans --ext .png,.svg
    python skills/pkm-metadata-indexer/link_graph.py broken
    python skills/pkm-metadata-indexer/link_graph.py --selfcheck

`refs` takes a full indexed path or any trailing part of one, so `token.py`
finds `src/auth/token.py`. `orphans` lists indexed files with an image
extension that no edge resolves to. `broken` lists references that resolved to
nothing, grouped by the text that was written.

An index whose edges table is empty says so instead of printing an empty list,
because a missing index and a genuinely empty answer look identical otherwise.
"""
import argparse
import sqlite3
import sys
from pathlib import Path

VAULT = Path(__file__).resolve().parents[2]
DEFAULT_DB = VAULT / ".obsidian" / "pkm_index.db"
DEFAULT_EXT = ".png,.jpg,.jpeg,.gif,.svg,.webp,.bmp,.ico,.tif,.tiff,.avif"


def like_escape(text):
    for char in ("\\", "%", "_"):
        text = text.replace(char, "\\" + char)
    return text


def suffix_match(column, target):
    """Match a full indexed path or any trailing path segment of one."""
    clause = f"{column} = ? COLLATE NOCASE OR {column} LIKE ? ESCAPE '\\'"
    return clause, [target, "%/" + like_escape(target)]


def referrers(connection, target):
    target = target.replace("\\", "/")
    resolved, params = suffix_match("resolved_target_path", target)
    raw, raw_params = suffix_match("raw_target", target)
    return connection.execute(
        f"SELECT source_path, raw_target, start_line FROM edges "
        f"WHERE {resolved} OR {raw} ORDER BY source_path, start_line",
        params + raw_params,
    ).fetchall()


def basename(path):
    return (path or "").replace("\\", "/").rsplit("/", 1)[-1].lower()


def orphan_assets(connection, extensions):
    """Return (orphans, total_images). Zero images is not zero orphans.

    An unreferenced name counts as referenced as well as an unreferenced path,
    because a scanner that never resolved its image embeds would otherwise
    report every image in the repository as safe to delete.
    """
    clause = " OR ".join("lower(n.path) LIKE ?" for _ in extensions)
    params = ["%" + extension.lower() for extension in extensions]
    images = [row[0] for row in connection.execute(
        f"SELECT n.path FROM notes n WHERE {clause} ORDER BY n.path", params)]
    referenced = set()
    for resolved, raw in connection.execute("SELECT resolved_target_path, raw_target FROM edges"):
        referenced.add((resolved or "").lower())
        referenced.update((basename(resolved), basename(raw)))
    orphans = [path for path in images
               if path.lower() not in referenced and basename(path) not in referenced]
    return orphans, len(images)


def broken_links(connection):
    return connection.execute(
        "SELECT source_path, raw_target, start_line FROM edges "
        "WHERE resolved_target_path IS NULL OR resolved_target_path = '' "
        "ORDER BY source_path, start_line"
    ).fetchall()


def edge_count(connection):
    try:
        return connection.execute("SELECT count(*) FROM edges").fetchone()[0]
    except sqlite3.OperationalError:
        return 0


def selfcheck():
    connection = sqlite3.connect(":memory:")
    connection.executescript(
        "CREATE TABLE notes (path TEXT PRIMARY KEY);"
        "CREATE TABLE edges (source_path TEXT, raw_target TEXT, resolved_target_path TEXT, start_line INTEGER);"
    )
    connection.executemany("INSERT INTO notes VALUES (?)", [
        ("docs/guide.md",), ("docs/setup.md",), ("src/auth/token.py",),
        ("docs/img/used.png",), ("docs/img/lonely.png",), ("docs/img/UPPER.SVG",),
    ])
    connection.executemany("INSERT INTO edges VALUES (?, ?, ?, ?)", [
        ("docs/guide.md", "src/auth/token.py", "src/auth/token.py", 12),
        ("docs/guide.md", "img/used.png", "docs/img/used.png", 30),
        ("docs/setup.md", "../src/auth/token.py", "src/auth/token.py", 4),
        ("docs/setup.md", "missing/page.md", None, 9),
        ("docs/setup.md", "gone.png", "", 11),
    ])

    assert [row[0] for row in referrers(connection, "src/auth/token.py")] == ["docs/guide.md", "docs/setup.md"]
    assert [row[0] for row in referrers(connection, "token.py")] == ["docs/guide.md", "docs/setup.md"], "suffix match"
    assert referrers(connection, "src\\auth\\token.py"), "windows separators"
    assert referrers(connection, "docs/guide.md") == [], "nothing points at the guide"
    assert referrers(connection, "en.py") == [], "suffix match is on segments, not characters"

    extensions = DEFAULT_EXT.split(",")
    orphans, total = orphan_assets(connection, extensions)
    assert orphans == ["docs/img/UPPER.SVG", "docs/img/lonely.png"], orphans
    assert total == 3, total
    assert orphan_assets(connection, [".png"]) == (["docs/img/lonely.png"], 2)
    assert orphan_assets(connection, [".xyz"]) == ([], 0), "no assets of that kind is not an orphan"

    assert [row[1] for row in broken_links(connection)] == ["missing/page.md", "gone.png"]
    assert edge_count(connection) == 5
    connection.execute("INSERT INTO edges VALUES ('docs/setup.md', 'img/lonely.png', NULL, 40)")
    assert orphan_assets(connection, extensions)[0] == ["docs/img/UPPER.SVG"], "an unresolved embed still counts"
    connection.execute("DELETE FROM edges")
    assert edge_count(connection) == 0
    print("selfcheck ok")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("command", nargs="?", choices=["refs", "orphans", "broken"])
    parser.add_argument("target", nargs="?", help="path for `refs`")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--ext", default=DEFAULT_EXT, help=f"image extensions, default {DEFAULT_EXT}")
    parser.add_argument("--top", type=int, default=50)
    parser.add_argument("--selfcheck", action="store_true")
    args = parser.parse_args()

    if args.selfcheck:
        return selfcheck()
    if not args.command:
        parser.error("give a command, or --selfcheck")
    if args.command == "refs" and not args.target:
        parser.error("refs needs a path")
    if not args.db.exists():
        sys.exit(f"no index at {args.db}. Run the indexer first.")

    connection = sqlite3.connect(f"file:{args.db.as_posix()}?mode=ro", uri=True)
    if edge_count(connection) == 0:
        sys.exit(f"{args.db} has no edges. The index exists but nothing has scanned links into it yet.")

    if args.command == "refs":
        rows = referrers(connection, args.target)
        for source_path, raw_target, start_line in rows[:args.top]:
            print(f"{source_path}:{start_line}  ({raw_target})")
        print(f"\n{len(rows)} reference(s) to {args.target}", file=sys.stderr)
    elif args.command == "orphans":
        rows, total = orphan_assets(connection, args.ext.split(","))
        for path in rows[:args.top]:
            print(path)
        if not total:
            print(f"no files matching {args.ext} are indexed, so nothing can be orphaned", file=sys.stderr)
        else:
            print(f"\n{len(rows)} of {total} image(s) referenced by nothing", file=sys.stderr)
    else:
        rows = broken_links(connection)
        for source_path, raw_target, start_line in rows[:args.top]:
            print(f"{source_path}:{start_line}  -> {raw_target}")
        print(f"\n{len(rows)} reference(s) resolving to nothing", file=sys.stderr)


if __name__ == "__main__":
    main()
