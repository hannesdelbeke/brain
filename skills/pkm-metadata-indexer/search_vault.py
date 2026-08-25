"""Search vault notes from the shell, through the daemon when one is running.

This used to load the embedding model itself, which cost about 3.0s per call
and ranked with a second, cosine-only implementation that could drift from the
one in `index_pkm_meta.search_index`. Both are gone. The daemon answers in tens
of milliseconds, and when it is not running the same `search_index` runs here
in-process, so the ranking exists once no matter who asks.

    python search_vault.py "notes on feeling overwhelmed by projects"
    python search_vault.py "battery mode" --vault work --top 5
    python search_vault.py "battery mode" --direct    # skip the daemon
"""

import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urlencode

sys.path.insert(0, str(Path(__file__).resolve().parent))

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DEFAULT_DAEMON = "http://127.0.0.1:44771"


def daemon_search(base: str, query: str, top: int, vault: str | None, timeout: float = 2.0):
    params = {"q": query, "limit": top}
    if vault:
        params["vault"] = vault
    url = f"{base.rstrip('/')}/search?{urlencode(params)}"
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            return json.load(response).get("results", [])
    except (urllib.error.URLError, OSError, ValueError, TimeoutError):
        return None


def direct_search(query: str, top: int, db: str | None):
    import index_pkm_meta as pkm  # numpy and fastembed cost ~1.3s to import, skip them for a daemon hit

    return [
        {"path": row["path"], "heading": row["heading"],
         "line": row["start_line"], "score": row["score"]}
        for row in pkm.search_index(query, db_path=db, limit=top)
    ]


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("query", help="Search query or vibe")
    parser.add_argument("--top", type=int, default=10, help="Number of results to return")
    parser.add_argument("--db", default=None, help="Path to SQLite database, for a direct search")
    parser.add_argument("--vault", default=None, help="Vault name registered with the daemon")
    parser.add_argument("--daemon", default=DEFAULT_DAEMON, help="Daemon base URL")
    parser.add_argument("--direct", action="store_true", help="Never use the daemon, load the model here")
    args = parser.parse_args()

    results = None if args.direct else daemon_search(args.daemon, args.query, args.top, args.vault)
    source = "daemon"
    if results is None:
        results = direct_search(args.query, args.top, args.db)
        source = "direct"

    print(f'\n--- Semantic Search Results for: "{args.query}" ({source}) ---')
    for index, row in enumerate(results, 1):
        print(f"{index}. [{row['score']:.3f}] {row['path']} (line {row['line']}) -> {row['heading']}")


if __name__ == "__main__":
    main()
