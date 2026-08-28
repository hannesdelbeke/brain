"""Resident search daemon for the vault index.

A one-shot `search_vault.py` call takes about 3.0s, and nearly all of it is
loading the embedding model to encode a single query string. Keeping the model
in a long-lived process turns that into a few tens of milliseconds, which is
the whole reason this file exists. Ranking is not reimplemented here, every
query goes through `index_pkm_meta.search_index` so the CLI and the daemon can
never drift apart.

One process serves every vault and every consumer. The model is the expensive
resident thing and it is vault-independent, so a second daemon per vault would
pay for it twice for nothing. Register vaults by name and select one per query:

    python searchd.py --vault brain=/path/to/brain --vault work=/path/to/work
    curl "http://127.0.0.1:44771/search?q=battery+mode&vault=work&limit=5"
    curl http://127.0.0.1:44771/health
    curl -X POST "http://127.0.0.1:44771/reindex?vault=brain"

A bare `--vault /path/to/brain` names it after the folder, and the first vault
registered is the default when a request omits `vault`. `/search` also takes
`vault=all` or a comma-separated list and merges the rankings, for a vault split
across repositories that an agent reads as one.

Every `/search` reports the files each corpus holds that its index has not read,
under `stale`, and starts a reindex behind the answer rather than making the
caller wait for one. A search that ranks well over a stale index is
indistinguishable from one that works, which is the failure this exists to make
visible.

Endpoints, all accepting `?vault=name`:
    GET  /health           registered vaults, counts, provider, warm state
    GET  /search?q=&limit= hybrid FTS5 + vector results with RRF scores,
                           `&rerank=1` reorders the top with a cross-encoder,
                           `&vault=all` searches every registered corpus
    GET  /links?note=      inbound and outbound wikilink edges for one note
    GET  /unlinked?note=   sections naming a note without linking to it
    POST /reindex          incremental rebuild, blocks until done

`--watch` starts one watcher thread per corpus, so a write reindexes that
corpus a couple of seconds later instead of waiting for someone to POST
/reindex. Changes are batched by debounce and the indexer's own writes are
filtered out, or the reindex would trigger the next one.

Off this machine, pass `--bind 0.0.0.0 --token <secret>` and send the secret as
`X-PKM-Token`. A non-loopback bind without a token is refused rather than
silently publishing the vault.

Every `/search` and `/similar` call appends a row to `~/.pkm/queries.jsonl`,
which is what makes a ranking change judgeable and a co-retrieval edge
derivable. `--query-log` moves it, `--no-query-log` turns it off, and a caller
can name where a search came from with `&origin=<note>`.
"""

import argparse
import hmac
import importlib
import importlib.util
import json
import os
import sqlite3
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs

sys.path.insert(0, str(Path(__file__).resolve().parent))

import index_pkm_meta as pkm

try:
    import watchfiles
except ImportError:  # only --watch needs it
    watchfiles = None

HOST = "127.0.0.1"
PORT = 44771
DEFAULT_LIMIT = 20
MAX_LIMIT = 100
LOOPBACK = {"127.0.0.1", "localhost", "[::1]", "::1"}
KEEPALIVE_S = 0.25
STALE_TTL_S = 30
WATCHED_STALE_TTL_S = 300
WATCH_DEBOUNCE_MS = 2000
WATCH_STEP_MS = 200
INDEX_SUFFIXES = (".db", ".db-wal", ".db-shm", ".db-journal")
QUERY_LOG = Path.home() / ".pkm" / "queries.jsonl"

# ponytail: one lock over the whole query path. The ONNX session is shared and
# queries are tens of milliseconds once warm, so serialising them costs nothing
# a single user can notice. Give the model its own lock if that stops being true.
LOCK = threading.Lock()

# Guards the one-reindex-per-corpus flag only, never held across a reindex.
REINDEX_LOCK = threading.Lock()

# Set by main(), None disables logging. The lock is separate from LOCK so a write
# never sits inside the query path.
LOG_PATH = None
LOG_LOCK = threading.Lock()


def log_query(kind: str, vault: str, subject: str, limit: int, took_ms: float,
              results: list, origin: str = ""):
    """Append one line per query, so ranking changes can be judged after the fact.

    JSON Lines rather than a table, because the index database is rebuilt by
    reindex and a log that a reindex deletes is not a log. Results are paths
    only: the scores are reproducible from the query, the paths are what a
    co-retrieval edge needs.
    """
    if LOG_PATH is None:
        return
    row = {
        "t": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "kind": kind,
        "vault": vault,
        "q": subject,
        "limit": limit,
        "took_ms": took_ms,
        "results": [result["path"] for result in results],
    }
    if origin:
        row["origin"] = origin
    line = json.dumps(row, ensure_ascii=False)
    try:
        with LOG_LOCK:
            LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
            with LOG_PATH.open("a", encoding="utf-8") as handle:
                handle.write(line + "\n")
    except OSError as error:  # a full or read-only disk must not fail the query
        print(f"query log write failed: {error}", flush=True)


class Vault:
    def __init__(self, name: str, root: Path, db: Path, collect=None):
        self.name = name
        self.root = root
        self.db = db
        self.collect = collect  # None scans markdown, otherwise a corpus scanner
        self.queries = 0
        self.vectors = None
        self.vectors_version = None
        self.reader = None
        self.watched = False  # set when a watcher thread takes this corpus
        self.reindexing = False
        self.stale_cache = None
        self.stale_at = 0.0

    def stale(self) -> dict:
        """Which files this corpus holds that its index has not read.

        A search is the only thing that will notice a watcher that died, so the
        check runs on the query path rather than on a timer. It costs a walk and
        a stat per file, 0.09s over 3,272 notes, which is several times a warm
        query, so the answer is cached: briefly when nothing is watching, and for
        minutes when something is, since a live watcher already reindexes within
        seconds and the check is then only there to catch it dying.
        """
        ttl = WATCHED_STALE_TTL_S if self.watched else STALE_TTL_S
        now = time.time()
        if self.stale_cache is None or now - self.stale_at > ttl:
            self.stale_cache = pkm.stale_paths(self.root, self.db)
            self.stale_at = now
        return self.stale_cache

    def matrix(self):
        """Keep the vector matrix resident, rebuilt only when the database changes.

        Re-reading 10 MB of blobs per query was the largest remaining cost. SQLite
        bumps `data_version` on any commit made through another connection, which
        is exactly how a reindex reaches us, so it is the invalidation signal.

        The connection has to outlive the call. A fresh connection reads 2 and
        keeps reading 2 no matter what any other connection commits, so opening
        one per query pinned the cache for the life of the daemon and a reindex
        never reached a search. Every caller holds LOCK, so one connection shared
        across the handler threads is safe, but sqlite3 has to be told that.
        """
        if not self.db.exists():
            return [], None
        if self.reader is None:
            self.reader = sqlite3.connect(
                f"file:{self.db}?mode=ro", uri=True, check_same_thread=False
            )
        cursor = self.reader.cursor()
        version = cursor.execute("PRAGMA data_version").fetchone()[0]
        if self.vectors is None or version != self.vectors_version:
            self.vectors = pkm.load_vectors(cursor)
            self.vectors_version = version
        return self.vectors

    def close(self):
        """Release the read connection. Only a test needs this: Windows refuses to
        delete a database file while a handle is open, and the daemon never exits."""
        if self.reader is not None:
            self.reader.close()
            self.reader = None

    def counts(self) -> dict:
        if not self.db.exists():
            return {"error": f"no index at {self.db}"}
        connection = sqlite3.connect(f"file:{self.db}?mode=ro", uri=True)
        try:
            cursor = connection.cursor()
            one = lambda sql: cursor.execute(sql).fetchone()[0]
            return {
                "notes": one("SELECT COUNT(*) FROM notes"),
                "sections": one("SELECT COUNT(*) FROM sections"),
                "vectors": one("SELECT COUNT(*) FROM sections WHERE vector IS NOT NULL"),
            }
        finally:
            connection.close()

    def describe(self) -> dict:
        return {"name": self.name, "root": str(self.root), "db": str(self.db),
                "queries": self.queries, "watched": self.watched,
                "indexed_at": pkm.last_index_run(self.db), **self.counts()}


class State:
    def __init__(self, vaults: list[Vault], token: str | None = None):
        self.vaults = {vault.name: vault for vault in vaults}
        self.default = vaults[0].name
        self.token = token
        self.warm = False
        self.started = time.time()
        self.last_query = 0.0

    def pick_many(self, name: str) -> list[Vault]:
        """Resolve a vault parameter, which may name several.

        The vault on this machine is two repositories by design: notes that stay
        private and notes that are published, kept apart so their histories are.
        An agent looking for a note does not care which half it is in, so `all`
        or a comma-separated list searches them together, while everything that
        writes still addresses one corpus by name.
        """
        if not name:
            return [self.vaults[self.default]]
        if name == "all":
            return list(self.vaults.values())
        names = [part.strip() for part in name.split(",") if part.strip()]
        unknown = [part for part in names if part not in self.vaults]
        if unknown or not names:
            raise KeyError(f"unknown vault {(unknown or [name])[0]!r}, have {sorted(self.vaults)}")
        return [self.vaults[part] for part in names]

    def pick(self, name: str) -> Vault:
        """One corpus, for the routes that only make sense against one."""
        return self.pick_many(name)[0]


STATE: State | None = None


def warm_up():
    """Pay the model load at startup so the first real query does not."""
    if not pkm.HAS_FASTEMBED:
        print("fastembed unavailable, lexical results only", flush=True)
        return
    began = time.perf_counter()
    model = pkm.get_embedding_model(pkm.QUERY_PROVIDERS, pkm.QUERY_THREADS)
    list(model.embed(["warm"]))  # the first encode allocates, do it before a user waits
    STATE.warm = True
    print(f"model warm in {time.perf_counter() - began:.2f}s "
          f"({(pkm.QUERY_PROVIDERS or pkm.get_embedding_providers())[0]})", flush=True)


def keepalive():
    """Encode a throwaway string on a timer so the model never goes cold.

    Warm, one encode costs 8.6ms at QUERY_THREADS. After a single idle second
    the same call costs 9.5-34.5ms, which was the largest remaining variance in
    a query, so the pipeline is kept saturated every 250ms. Skips a tick when a
    real query just ran, so it never makes a user wait.

    This loop is what made the idle burn visible: with the default ONNX pool it
    left 11.93 cores spinning between ticks. Capped, the daemon measures 0.00
    cores idle over 20s. See QUERY_THREADS in index_pkm_meta.
    """
    model = pkm.get_embedding_model(pkm.QUERY_PROVIDERS, pkm.QUERY_THREADS)
    while True:
        time.sleep(KEEPALIVE_S)
        if time.time() - STATE.last_query < KEEPALIVE_S:
            continue
        with LOCK:
            list(model.embed(["."]))


def rank(vault: Vault, query: str, limit: int, rerank: bool = False) -> list[dict]:
    with LOCK:
        rows = pkm.search_index(query, db_path=str(vault.db), limit=limit,
                                vectors=vault.matrix(), rerank=rerank)
        vault.queries += 1
    return [
        {
            "vault": vault.name,
            "path": row["path"],
            "heading": row["heading"],
            "line": row["start_line"],
            "score": round(row["score"], 6),
            "raw_sim": row["raw_sim"],
            "snippet": row["snippet"],
            **({"rerank_score": row["rerank_score"]} if "rerank_score" in row else {}),
        }
        for row in rows
    ]


def kick_reindex(vault: Vault) -> bool:
    """Start a reindex behind the search that noticed, at most one per corpus.

    The search itself is answered from the index as it stands rather than made
    to wait: a stale answer plus a list of what is missing is useful now, and
    the next query a minute later is complete. Two searches finding the same
    corpus stale must not start two passes over it, hence the flag.
    """
    with REINDEX_LOCK:
        if vault.reindexing:
            return True
        vault.reindexing = True

    def run():
        try:
            result = do_reindex(vault)
            print(f"stale {vault.name}: reindexed in {result['took_s']}s", flush=True)
        except Exception as error:
            print(f"stale {vault.name}: reindex failed, {type(error).__name__}: {error}", flush=True)
        finally:
            vault.stale_at = 0.0  # recheck rather than trust a cache the reindex invalidated
            vault.reindexing = False

    threading.Thread(target=run, daemon=True).start()
    return True


def do_search(vaults: list[Vault], query: str, limit: int, origin: str = "",
              rerank: bool = False, reindex: bool = True) -> dict:
    """Search one corpus or several, and say which files the answer could not see.

    Merging across corpora sorts on the fused score. Those scores are sums of
    `1/(k + rank)` on both sides, so sorting them interleaves the two rankings by
    rank, which is the only comparison between two separate indexes that means
    anything: a bm25 score from one corpus and a bm25 score from another are not
    on the same scale, their positions are.
    """
    began = time.perf_counter()
    STATE.last_query = time.time()
    results, stale, indexed_at = [], {}, {}
    for vault in vaults:
        results += rank(vault, query, limit, rerank)
        missing = vault.stale()
        indexed_at[vault.name] = missing["indexed_at"]
        if missing["count"] or missing.get("no_index"):
            stale[vault.name] = {**missing, "reindexing": reindex and kick_reindex(vault)}
    if len(vaults) > 1:
        results.sort(key=lambda row: row["score"], reverse=True)
        results = results[:limit]
    name = ",".join(vault.name for vault in vaults)
    payload = {
        "vault": name,
        "query": query,
        "took_ms": round((time.perf_counter() - began) * 1000, 1),
        "indexed_at": indexed_at,
        "stale": stale,
        "results": results,
    }
    log_query("search", name, query, limit, payload["took_ms"], payload["results"], origin)
    return payload


def do_links(vault: Vault, note: str) -> dict:
    with LOCK:
        found = pkm.query_links(note, db_path=str(vault.db))
    if not found:
        return {"error": f"no single indexed note matches {note!r}"}
    return {
        "vault": vault.name,
        "path": found["path"],
        "outbound": [
            {"target": resolved or raw, "resolved": bool(resolved), "line": line}
            for raw, resolved, line in found["outbound"]
        ],
        "inbound": [
            {"source": source, "raw_target": raw, "line": line}
            for source, raw, line in found["inbound"]
        ],
    }


def do_similar(vault: Vault, note: str, limit: int) -> dict:
    began = time.perf_counter()
    STATE.last_query = time.time()
    with LOCK:
        rows = pkm.find_similar_notes(note, db_path=str(vault.db), limit=limit, vectors=vault.matrix())
        vault.queries += 1
    if rows is None:
        return {"error": f"no single indexed note matches {note!r}"}
    payload = {
        "vault": vault.name,
        "note": note,
        "took_ms": round((time.perf_counter() - began) * 1000, 1),
        "results": [
            {
                "path": row["path"],
                "heading": row["heading"],
                "line": row["start_line"],
                "score": round(row["score"], 6),
                "raw_sim": row["raw_sim"],
                "snippet": row["snippet"],
            }
            for row in rows
        ],
    }
    # The note is both the query and the origin here, which is the co-retrieval
    # edge this log exists to collect.
    log_query("similar", vault.name, note, limit, payload["took_ms"], payload["results"], note)
    return payload


def do_unlinked(vault: Vault, note: str, limit: int) -> dict:
    began = time.perf_counter()
    with LOCK:
        found = pkm.find_unlinked_mentions(
            note, vault_path=str(vault.root), db_path=str(vault.db), limit=limit
        )
    if found is None:
        return {"error": f"no single indexed note matches {note!r}"}
    return {
        "vault": vault.name,
        "note": note,
        "took_ms": round((time.perf_counter() - began) * 1000, 1),
        "results": [
            {
                "path": row["path"],
                "heading": row["heading"],
                "line": row["start_line"],
                "score": round(row["score"], 6),
                "term": row["term"],
                "snippet": row["snippet"],
            }
            for row in found
        ],
    }


def do_reindex(vault: Vault) -> dict:
    began = time.perf_counter()
    with LOCK:
        pkm.build_index(vault_path=str(vault.root), db_path=str(vault.db), collect=vault.collect)
    vault.stale_at = 0.0  # whatever was missing is in now, do not report it again
    return {"vault": vault.name, "took_s": round(time.perf_counter() - began, 2), **vault.counts()}


def index_writes(path: str) -> bool:
    """True for a path the indexer itself writes.

    Without this a reindex writes the database inside the watched root, the
    watcher sees it and reindexes again, forever. Dotfiles go with it: the scan
    state file is one, and no note is named that way.
    """
    name = Path(path).name
    return name.startswith(".") or name.endswith(INDEX_SUFFIXES)


def catch_up(vaults):
    """Reindex once at startup, for whatever changed while nothing was watching.

    A watcher only sees what changes while it runs, so a daemon that was down
    over an edit would serve the index it was killed with and never find out.
    Catching up before the socket opens is what makes starting the daemon on
    demand as good as leaving it running: about 2.3s to warm plus a pass that is
    2.57s over 3,264 notes with nothing to re-embed, and nothing to keep alive
    across a reboot. A corpus with no index yet is skipped, since a first build
    is not a catch-up and the caller was already warned about it.
    """
    for vault in vaults:
        if not vault.db.exists():
            continue
        try:
            result = do_reindex(vault)
            print(f"catch-up {vault.name}: {result['took_s']}s", flush=True)
        except Exception as error:
            print(f"catch-up {vault.name} failed, {type(error).__name__}: {error}", flush=True)


def watch_vault(vault: Vault, stream=None):
    """Reindex one corpus whenever its files change.

    A pass is seconds now, so the index can follow writes instead of waiting
    for someone to remember. `watchfiles` batches by debounce, so a save that
    touches five files is one reindex. Errors print and the loop continues: a
    half-written file that fails to parse must not stop the watcher.
    """
    if stream is None:
        stream = watchfiles.watch(
            vault.root,
            watch_filter=lambda change, path: watchfiles.DefaultFilter()(change, path)
            and not index_writes(path),
            debounce=WATCH_DEBOUNCE_MS,
            step=WATCH_STEP_MS,
        )
    for batch in stream:
        try:
            result = do_reindex(vault)
            print(f"watch {vault.name}: {len(batch)} change(s), reindexed in "
                  f"{result['took_s']}s", flush=True)
        except Exception as error:
            print(f"watch {vault.name}: reindex failed, {type(error).__name__}: {error}",
                  flush=True)


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def reply(self, code: int, payload: dict):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def allowed(self) -> bool:
        """Localhost binding alone does not keep a browser out.

        Any page the user visits can POST to 127.0.0.1, and a DNS rebind can
        make a hostile name resolve here, so a loopback Host is required and
        anything carrying an Origin is rejected: a browser always sets Origin
        on a cross-site request and a real client here never does. When a token
        is configured the vault is reachable off this machine, so the Host
        check gives way to the token.
        """
        if self.headers.get("Origin") is not None:
            return False
        if STATE.token:
            sent = self.headers.get("X-PKM-Token") or ""
            return hmac.compare_digest(sent, STATE.token)
        host = (self.headers.get("Host") or "").rsplit(":", 1)[0]
        return host in LOOPBACK

    def handle_request(self, method: str):
        if not self.allowed():
            self.reply(403, {"error": "loopback clients only, or send X-PKM-Token"})
            return
        url = urlparse(self.path)
        params = parse_qs(url.query)
        first = lambda name: (params.get(name) or [""])[0].strip()
        try:
            if url.path == "/health":
                self.reply(200, {
                    "status": "ok",
                    "warm": STATE.warm,
                    "query_provider": (pkm.QUERY_PROVIDERS or pkm.get_embedding_providers())[0],
                    "index_provider": pkm.get_embedding_providers()[0],
                    "uptime_s": round(time.time() - STATE.started, 1),
                    "default_vault": STATE.default,
                    "vaults": [vault.describe() for vault in STATE.vaults.values()],
                })
                return
            if url.path == "/search" and method == "GET":
                query = first("q")
                if not query:
                    self.reply(400, {"error": "q is required"})
                    return
                limit = max(1, min(MAX_LIMIT, int(first("limit") or DEFAULT_LIMIT)))
                self.reply(200, do_search(STATE.pick_many(first("vault")), query, limit,
                                          first("origin"),
                                          first("rerank") in {"1", "true", "yes"},
                                          first("reindex") not in {"0", "false", "no"}))
                return
            vault = STATE.pick(first("vault"))
            if url.path == "/links" and method == "GET":
                note = first("note")
                if not note:
                    self.reply(400, {"error": "note is required"})
                    return
                self.reply(200, do_links(vault, note))
            elif url.path == "/similar" and method == "GET":
                note = first("note")
                if not note:
                    self.reply(400, {"error": "note is required"})
                    return
                limit = max(1, min(MAX_LIMIT, int(first("limit") or DEFAULT_LIMIT)))
                self.reply(200, do_similar(vault, note, limit))
            elif url.path == "/unlinked" and method == "GET":
                note = first("note")
                if not note:
                    self.reply(400, {"error": "note is required"})
                    return
                limit = max(1, min(MAX_LIMIT, int(first("limit") or DEFAULT_LIMIT)))
                self.reply(200, do_unlinked(vault, note, limit))
            elif url.path == "/reindex" and method == "POST":
                self.reply(200, do_reindex(vault))
            else:
                self.reply(404, {"error": f"no route for {method} {url.path}"})
        except KeyError as error:
            self.reply(404, {"error": str(error)})
        except ValueError:
            self.reply(400, {"error": "limit must be a number"})
        except Exception as error:  # a bad query must not take the daemon down
            self.reply(500, {"error": f"{type(error).__name__}: {error}"})

    def do_GET(self):
        self.handle_request("GET")

    def do_POST(self):
        self.handle_request("POST")

    def log_message(self, fmt, *args):
        print(f"{self.address_string()} {fmt % args}", flush=True)


def parse_vault(spec: str, db_override: str | None = None, collect=None) -> Vault:
    name, _, raw_path = spec.partition("=")
    if not raw_path:
        name, raw_path = "", name
    root = Path(raw_path).expanduser().resolve()
    db = Path(db_override).resolve() if db_override else pkm.default_db_path(root)
    return Vault(name or root.name, root, db, collect)


def load_module(name: str):
    """Import a scanner module by dotted name, or by path to its file.

    A corpus scanner usually lives in the repository holding the corpus rather
    than beside the daemon, and taking a path there is one argument where an
    importable name is a `PYTHONPATH` the caller has to remember to set.
    """
    if not name.endswith(".py"):
        return importlib.import_module(name)
    path = Path(name).expanduser().resolve()
    spec = importlib.util.spec_from_file_location(path.stem, path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"cannot load a scanner from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[path.stem] = module  # so the scanner can import its own siblings
    sys.path.insert(0, str(path.parent))
    spec.loader.exec_module(module)
    return module


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--vault", action="append", default=[],
                        help="Vault as PATH or NAME=PATH, repeatable. Defaults to the nearest vault above cwd")
    parser.add_argument("--sessions", action="append", default=[],
                        help="Agent transcript root as PATH or NAME=PATH, repeatable. Indexed as turns, not notes")
    parser.add_argument("--corpus", action="append", default=[],
                        help="Any other corpus as MODULE:FUNCTION=NAME=PATH, repeatable, where MODULE is an "
                             "importable name or a path to a .py file. The function "
                             "takes a root and returns collect_index_data's tuple")
    parser.add_argument("--db", default=None, help="Database for a single vault, otherwise <vault>/.obsidian/pkm_index.db")
    parser.add_argument("--bind", default=HOST, help="Interface to listen on, loopback unless a token is set")
    parser.add_argument("--port", type=int, default=PORT)
    parser.add_argument("--token", default=os.environ.get("PKM_SEARCHD_TOKEN"),
                        help="Shared secret required as X-PKM-Token, needed for any non-loopback bind")
    parser.add_argument("--watch", action="store_true",
                        help="Reindex a corpus when its files change, one watcher per corpus. "
                             "Needs watchfiles")
    parser.add_argument("--no-warm", action="store_true", help="Skip the startup model load")
    parser.add_argument("--no-keepalive", action="store_true",
                        help="Let the model go cold between queries, trading ~30ms on the first "
                             "query after idle. Keepalive costs ~0.00 cores now the ONNX pool is "
                             "capped at QUERY_THREADS, so there is rarely a reason to pass this")
    parser.add_argument("--query-log", default=str(QUERY_LOG),
                        help="JSON Lines file recording one row per /search and /similar: "
                             "the query text, the vault and the result paths")
    parser.add_argument("--no-query-log", action="store_true",
                        help="Record nothing. The log holds query strings and result paths in "
                             "plain text, which is the reason to turn it off")
    args = parser.parse_args()

    global LOG_PATH
    LOG_PATH = None if args.no_query_log else Path(args.query_log).expanduser()

    if args.bind not in LOOPBACK and not args.token:
        parser.error("a non-loopback --bind needs --token, otherwise the vault is served to the network unauthenticated")
    others = args.sessions + args.corpus
    if args.db and len(args.vault) + len(others) > 1:
        parser.error("--db applies to a single vault, give each vault its own .obsidian/pkm_index.db instead")

    specs = args.vault or ([] if others else [str(pkm.find_vault_root())])
    vaults = [parse_vault(spec, args.db) for spec in specs]
    if args.sessions:
        import index_sessions
        vaults += [parse_vault(spec, collect=index_sessions.scan_sessions) for spec in args.sessions]
    for spec in args.corpus:
        # First `=` and last `:`, so that `C:/x/scan.py:scan` parses as well as
        # `scan:scan` does.
        scanner, _, vault_spec = spec.partition("=")
        module_name, _, function_name = scanner.rpartition(":")
        if not (vault_spec and function_name and module_name):
            parser.error(f"--corpus wants MODULE:FUNCTION=NAME=PATH, got {spec!r}")
        vaults.append(parse_vault(vault_spec, collect=getattr(load_module(module_name), function_name)))

    global STATE
    STATE = State(vaults, args.token)
    for vault in vaults:
        print(f"vault {vault.name}\n  root {vault.root}\n  db   {vault.db}", flush=True)
        if not vault.db.exists():
            print(f"  warning: no index yet, POST /reindex?vault={vault.name}", flush=True)
    if args.watch and watchfiles is None:
        parser.error("--watch needs watchfiles, pip install watchfiles")
    if not args.no_warm:
        warm_up()
    if STATE.warm and not args.no_keepalive:
        threading.Thread(target=keepalive, daemon=True).start()
    if args.watch:
        catch_up(vaults)
        for vault in vaults:
            vault.watched = True
            threading.Thread(target=watch_vault, args=(vault,), daemon=True).start()
        print(f"watching {len(vaults)} corpus root(s)", flush=True)

    print(f"query log {LOG_PATH or 'off'}", flush=True)

    server = ThreadingHTTPServer((args.bind, args.port), Handler)
    print(f"listening on http://{args.bind}:{args.port}"
          f"{' (token required)' if args.token else ''}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("stopping", flush=True)
        server.shutdown()


if __name__ == "__main__":
    main()
