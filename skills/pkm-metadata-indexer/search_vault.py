"""Search vault notes from the shell, through the daemon when one is running.

This used to load the embedding model itself, which cost about 3.0s per call
and ranked with a second, cosine-only implementation that could drift from the
one in `index_pkm_meta.search_index`. Both are gone. The daemon answers in tens
of milliseconds, and when it is not running the same `search_index` runs here
in-process, so the ranking exists once no matter who asks.

    python search_vault.py "notes on feeling overwhelmed by projects"
    python search_vault.py "battery mode" --vault work --top 5
    python search_vault.py "battery mode" --direct    # skip the daemon
    python search_vault.py "Obsidian" --unlinked      # mentions that are not links

Searches every registered corpus by default. The vault on this machine is two
repositories, private notes and published ones, kept apart so their git
histories are; nothing about looking for a note cares which half it is in.
Name one with `--vault` when it matters.

Each result header names the corpus that answered and when that corpus was last
indexed, and any file the index has not read yet is listed under the results.
"""

import argparse
import json
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urlencode

sys.path.insert(0, str(Path(__file__).resolve().parent))

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DEFAULT_DAEMON = "http://127.0.0.1:44771"
# Long enough to outwait a reindex, because the daemon serialises the model and
# a write to any watched path starts a pass. At 2s a search landing during one
# timed out, fell through to a direct search of whichever corpus the working
# directory resolved to, and printed the answer as if nothing had happened. A
# missing daemon refuses the connection instantly, so this only costs when there
# really is one to wait for.
DAEMON_TIMEOUT_S = 30.0


def daemon_get(base: str, route: str, params: dict, vault: str | None, timeout: float = DAEMON_TIMEOUT_S):
    """Ask the daemon, returning None only when there is no daemon to ask.

    An HTTP error is an answer: the daemon ran and refused. Catching it
    alongside the connection failures made a typo in `--vault` fall through to a
    direct search against whatever database the working directory resolved to,
    so the wrong corpus answered and the output said `(direct)` as if that were
    normal. Exit instead, since a search of a corpus the caller did not name is
    worse than no search.
    """
    if vault:
        params = {**params, "vault": vault}
    url = f"{base.rstrip('/')}/{route}?{urlencode(params)}"
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            return json.load(response)
    except urllib.error.HTTPError as error:
        try:
            message = json.load(error).get("error", error.reason)
        except ValueError:
            message = error.reason
        raise SystemExit(f"daemon refused the request: {message}")
    except (urllib.error.URLError, OSError, ValueError, TimeoutError):
        return None


def direct_search(query: str, top: int, db: str | None):
    import index_pkm_meta as pkm  # numpy and fastembed cost ~1.3s to import, skip them for a daemon hit

    return [
        {"path": row["path"], "heading": row["heading"],
         "line": row["start_line"], "score": row["score"]}
        for row in pkm.search_index(query, db_path=db, limit=top)
    ]


def direct_unlinked(note: str, top: int, db: str | None):
    """Same function the daemon calls, so the two can never disagree.

    Unlinked mentions need the vault root as well as the database, because the
    aliases and the fenced code blocks are read from the files themselves. When
    only `--db` is given, the root is the grandparent of `<vault>/.obsidian/db`.
    """
    import index_pkm_meta as pkm

    vault_path = str(Path(db).resolve().parents[1]) if db else None
    return [
        {"path": row["path"], "heading": row["heading"],
         "line": row["start_line"], "snippet": row["snippet"]}
        for row in pkm.find_unlinked_mentions(note, vault_path=vault_path, db_path=db, limit=top) or []
    ]


def spawn_reindex(root: Path, db: Path):
    """Reindex in a process that outlives this one, so the next search is complete.

    The daemon does this on a thread. Here there is no daemon by definition, and
    a search that blocks for a full pass to answer a question the current index
    can nearly answer is the wrong trade, so the pass is detached and the results
    print now.
    """
    command = [sys.executable, str(Path(__file__).with_name("index_pkm_meta.py")),
               "--vault", str(root), "--db", str(db)]
    if sys.platform == "win32":
        # DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP, or closing this shell kills it
        extra = {"creationflags": 0x00000008 | 0x00000200}
    else:
        extra = {"start_new_session": True}
    subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, **extra)


def direct_stale(db: str | None, reindex: bool) -> dict:
    """What a direct search could not see, and a background pass to fix it."""
    import index_pkm_meta as pkm

    if db:
        database = Path(db).resolve()
        # a vault hides its index in .obsidian, any other corpus keeps it alongside
        root = database.parents[1] if database.parent.name == ".obsidian" else database.parent
    else:
        root = pkm.find_vault_root()
        database = pkm.default_db_path(root)
    missing = pkm.stale_paths(root, database)
    if (missing["count"] or missing.get("no_index")) and reindex:
        spawn_reindex(root, database)
        missing["reindexing"] = True
    return missing


def print_stale(stale: dict):
    """Name the files the answer could not include, since the ranking cannot.

    Results from a stale index look exactly like results from a fresh one. The
    only place the difference can show up is here.
    """
    for name, missing in stale.items():
        if missing.get("no_index"):
            print(f"\n! {name} has no index yet"
                  f"{', building one now' if missing.get('reindexing') else ''}")
            continue
        shown = missing["paths"]
        print(f"\n! {name} has {missing['count']} file(s) newer than its index "
              f"({missing['indexed_at'][:19]}Z), not searched"
              f"{', reindexing now' if missing.get('reindexing') else ''}:")
        for path in shown:
            print(f"    {path}")
        if missing["count"] > len(shown):
            print(f"    ... and {missing['count'] - len(shown)} more")


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("query", help="Search query or vibe")
    parser.add_argument("--top", type=int, default=10, help="Number of results to return")
    parser.add_argument("--db", default=None,
                        help="Path to SQLite database. Implies --direct, since the daemon "
                             "answers from the corpora it registered, not from a path")
    parser.add_argument("--vault", default="all",
                        help="Vault name registered with the daemon, or a comma-separated "
                             "list. Defaults to every registered corpus")
    parser.add_argument("--daemon", default=DEFAULT_DAEMON, help="Daemon base URL")
    parser.add_argument("--direct", action="store_true", help="Never use the daemon, load the model here")
    parser.add_argument("--no-reindex", action="store_true",
                        help="Report files missing from the index without starting a pass over them")
    parser.add_argument("--unlinked", action="store_true",
                        help="Treat the query as a note title and list unlinked mentions of it")
    args = parser.parse_args()

    # --db names one database and the daemon answers from the corpora it was
    # started with, so honouring both meant printing results from one and the
    # name of the other. The flag wins, because it is the more specific request.
    direct = args.direct or bool(args.db)
    vault = None if direct else args.vault

    if args.unlinked:
        payload = None if direct else daemon_get(
            args.daemon, "unlinked", {"note": args.query, "limit": args.top}, vault
        )
        if payload and "error" in payload:
            raise SystemExit(payload["error"])
        source = f"daemon, {payload['vault']}" if payload else "direct"
        results = payload["results"] if payload else direct_unlinked(args.query, args.top, args.db)
        print(f'\n--- Unlinked Mentions of: "{args.query}" ({source}) ---')
        for index, row in enumerate(results, 1):
            print(f"{index}. {row['path']}:{row['line']} -> {row['heading']}")
            print(f"   {row['snippet']}")
        return

    params = {"q": args.query, "limit": args.top}
    if args.no_reindex:
        params["reindex"] = "0"
    payload = None if direct else daemon_get(args.daemon, "search", params, vault)
    if payload is not None:
        results, stale = payload["results"], payload["stale"]
        indexed = ", ".join(f"{name} @ {(at or 'never')[:19]}"
                            for name, at in payload["indexed_at"].items())
        source = f"daemon: {indexed}"
    else:
        results = direct_search(args.query, args.top, args.db)
        missing = direct_stale(args.db, not args.no_reindex)
        stale = {"vault": missing} if missing["count"] or missing.get("no_index") else {}
        source = f"direct @ {(missing['indexed_at'] or 'never')[:19]}"

    print(f'\n--- Semantic Search Results for: "{args.query}" ({source}) ---')
    for index, row in enumerate(results, 1):
        where = f"{row['vault']}/" if "vault" in row else ""
        print(f"{index}. [{row['score']:.3f}] {where}{row['path']} "
              f"(line {row['line']}) -> {row['heading']}")
    print_stale(stale)


if __name__ == "__main__":
    main()
