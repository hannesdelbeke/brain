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
registered is the default when a request omits `vault`.

Endpoints, all accepting `?vault=name`:
    GET  /health           registered vaults, counts, provider, warm state
    GET  /search?q=&limit= hybrid FTS5 + vector results with RRF scores
    GET  /links?note=      inbound and outbound wikilink edges for one note
    POST /reindex          incremental rebuild, blocks until done

Off this machine, pass `--bind 0.0.0.0 --token <secret>` and send the secret as
`X-PKM-Token`. A non-loopback bind without a token is refused rather than
silently publishing the vault.
"""

import argparse
import hmac
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

HOST = "127.0.0.1"
PORT = 44771
DEFAULT_LIMIT = 20
MAX_LIMIT = 100
LOOPBACK = {"127.0.0.1", "localhost", "[::1]", "::1"}
KEEPALIVE_S = 0.25

# ponytail: one lock over the whole query path. The ONNX session is shared and
# queries are tens of milliseconds once warm, so serialising them costs nothing
# a single user can notice. Give the model its own lock if that stops being true.
LOCK = threading.Lock()



class Vault:
    def __init__(self, name: str, root: Path, db: Path):
        self.name = name
        self.root = root
        self.db = db
        self.queries = 0
        self.vectors = None
        self.vectors_version = None

    def matrix(self):
        """Keep the vector matrix resident, rebuilt only when the database changes.

        Re-reading 10 MB of blobs per query was the largest remaining cost. SQLite
        bumps `data_version` on any commit made through another connection, which
        is exactly how a reindex reaches us, so it is the invalidation signal.
        """
        if not self.db.exists():
            return [], None
        connection = sqlite3.connect(f"file:{self.db}?mode=ro", uri=True)
        try:
            cursor = connection.cursor()
            version = cursor.execute("PRAGMA data_version").fetchone()[0]
            if self.vectors is None or version != self.vectors_version:
                self.vectors = pkm.load_vectors(cursor)
                self.vectors_version = version
            return self.vectors
        finally:
            connection.close()

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
                "queries": self.queries, **self.counts()}


class State:
    def __init__(self, vaults: list[Vault], token: str | None = None):
        self.vaults = {vault.name: vault for vault in vaults}
        self.default = vaults[0].name
        self.token = token
        self.warm = False
        self.started = time.time()
        self.last_query = 0.0

    def pick(self, name: str) -> Vault:
        if not name:
            return self.vaults[self.default]
        if name not in self.vaults:
            raise KeyError(f"unknown vault {name!r}, have {sorted(self.vaults)}")
        return self.vaults[name]


STATE: State | None = None


def warm_up():
    """Pay the model load at startup so the first real query does not."""
    if not pkm.HAS_FASTEMBED:
        print("fastembed unavailable, lexical results only", flush=True)
        return
    began = time.perf_counter()
    model = pkm.get_embedding_model(pkm.QUERY_PROVIDERS)
    list(model.embed(["warm"]))  # the first encode allocates, do it before a user waits
    STATE.warm = True
    print(f"model warm in {time.perf_counter() - began:.2f}s "
          f"({(pkm.QUERY_PROVIDERS or pkm.get_embedding_providers())[0]})", flush=True)


def keepalive():
    """Encode a throwaway string on a timer so the model never goes cold.

    Warm, one encode costs 3.6-3.8ms. After a single idle second the same call
    costs 9.5-34.5ms, which was the largest remaining variance in a query, so
    the pipeline is kept saturated for about 4ms of one core every 250ms. Skips
    a tick when a real query just ran, so it never makes a user wait.
    """
    model = pkm.get_embedding_model(pkm.QUERY_PROVIDERS)
    while True:
        time.sleep(KEEPALIVE_S)
        if time.time() - STATE.last_query < KEEPALIVE_S:
            continue
        with LOCK:
            list(model.embed(["."]))


def do_search(vault: Vault, query: str, limit: int) -> dict:
    began = time.perf_counter()
    STATE.last_query = time.time()
    with LOCK:
        rows = pkm.search_index(query, db_path=str(vault.db), limit=limit, vectors=vault.matrix())
        vault.queries += 1
    return {
        "vault": vault.name,
        "query": query,
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


def do_reindex(vault: Vault) -> dict:
    began = time.perf_counter()
    with LOCK:
        pkm.build_index(vault_path=str(vault.root), db_path=str(vault.db))
    return {"vault": vault.name, "took_s": round(time.perf_counter() - began, 2), **vault.counts()}


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
            vault = STATE.pick(first("vault"))
            if url.path == "/search" and method == "GET":
                query = first("q")
                if not query:
                    self.reply(400, {"error": "q is required"})
                    return
                limit = max(1, min(MAX_LIMIT, int(first("limit") or DEFAULT_LIMIT)))
                self.reply(200, do_search(vault, query, limit))
            elif url.path == "/links" and method == "GET":
                note = first("note")
                if not note:
                    self.reply(400, {"error": "note is required"})
                    return
                self.reply(200, do_links(vault, note))
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


def parse_vault(spec: str, db_override: str | None = None) -> Vault:
    name, _, raw_path = spec.partition("=")
    if not raw_path:
        name, raw_path = "", name
    root = Path(raw_path).expanduser().resolve()
    db = Path(db_override).resolve() if db_override else root / ".obsidian" / "pkm_index.db"
    return Vault(name or root.name, root, db)


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--vault", action="append", default=[],
                        help="Vault as PATH or NAME=PATH, repeatable. Defaults to the nearest vault above cwd")
    parser.add_argument("--db", default=None, help="Database for a single vault, otherwise <vault>/.obsidian/pkm_index.db")
    parser.add_argument("--bind", default=HOST, help="Interface to listen on, loopback unless a token is set")
    parser.add_argument("--port", type=int, default=PORT)
    parser.add_argument("--token", default=os.environ.get("PKM_SEARCHD_TOKEN"),
                        help="Shared secret required as X-PKM-Token, needed for any non-loopback bind")
    parser.add_argument("--no-warm", action="store_true", help="Skip the startup model load")
    parser.add_argument("--no-keepalive", action="store_true",
                        help="Let the model go cold between queries, saving ~1.5%% of one core")
    args = parser.parse_args()

    if args.bind not in LOOPBACK and not args.token:
        parser.error("a non-loopback --bind needs --token, otherwise the vault is served to the network unauthenticated")
    if args.db and len(args.vault) > 1:
        parser.error("--db applies to a single vault, give each vault its own .obsidian/pkm_index.db instead")

    specs = args.vault or [str(pkm.find_vault_root())]
    vaults = [parse_vault(spec, args.db) for spec in specs]

    global STATE
    STATE = State(vaults, args.token)
    for vault in vaults:
        print(f"vault {vault.name}\n  root {vault.root}\n  db   {vault.db}", flush=True)
        if not vault.db.exists():
            print(f"  warning: no index yet, POST /reindex?vault={vault.name}", flush=True)
    if not args.no_warm:
        warm_up()
    if STATE.warm and not args.no_keepalive:
        threading.Thread(target=keepalive, daemon=True).start()

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
