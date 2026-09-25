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
    python search_vault.py "gemini flash" --no-rerank  # fusion order, no cross-encoder

The cross-encoder rerank is on by default here, where the daemon leaves it off.
It won on both corpora it has been measured against: precision@10 39% against
32% on brain, 45% against 42% on vault-b over the same 13 hold-out questions,
with the first useful section at mean rank 1.7 against 2.2. This front end
answers agents and humans rather than other programs, and both pay more for a
wrong first result than for the wait.

The wait is one cross-encoder batch however many corpora the search spans:
the daemon merges first and scores the merged candidates once. It is still
most of the latency, because a process holding the DirectML index session
reranks 20 candidates in 2.4s where the same call in a process without it
takes 540ms, and the daemon holds that session by definition. `--no-rerank`
is the way out until that is fixed. See `2026-08-31 turning the rerank on by
default`.

Searches every registered corpus by default. The vault on this machine is two
repositories, private notes and published ones, kept apart so their git
histories are; nothing about looking for a note cares which half it is in.
Name one with `--vault` when it matters.

Each result header names the corpus that answered and when that corpus was last
indexed, and any file the index has not read yet is listed under the results.

Results carry the text of the section that matched, not just its path, and the
list is cut where the scores fall away. A path and a heading cannot be judged
without opening the note, and the note costs thousands of tokens against the few
hundred of the section; a third of everything read out of this vault was read to
find out the note was wrong. The cut is printed rather than applied, so the
weaker results are still listed by heading when it is wrong. A flat list says so
instead of inventing a boundary.
"""

import argparse
import json
import math
import sqlite3
import subprocess
import sys
import time
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
# The same argument as above, which the old 0.2s here contradicted. A liveness
# probe's timeout is only ever spent when something is listening: an absent daemon
# refuses the connection, measured at 0.4ms, and never reaches the timeout at all.
# So the only thing a tight budget buys is calling a live daemon dead.
#
# Measured over 25 calls against a healthy daemon: median 25.6ms, p95 45.6ms, and
# a 496ms tail -- so 0.2s failed roughly one call in twenty-five, and 0.5s would
# still have failed that one. The cost of being wrong is not symmetric: a false
# "offline" drops the caller into a direct search that loads the embedding model
# (~2s), answers from whatever database the working directory resolved to, and
# cannot honour `--vault` at all, so it silently searches a corpus the caller did
# not ask for. 1.0s sits above the measured tail and stays under the ~1.4s where
# waiting for the daemon stops being cheaper than the fallback it would trigger.
HEALTH_TIMEOUT_S = 1.0


def daemon_healthy(base: str) -> bool:
    """Check whether a local daemon can answer before waiting on a search.

    Asks for the cheap form of `/health`. The full route opens a read-only SQLite
    connection per vault and runs three `COUNT(*)`s plus a co-commit lookup on
    each one -- including a scan for non-null vectors over a table of hundreds of
    thousands of sections -- which is where the 496ms tail comes from. None of it
    is read here; this only needs to know something answered. `probe=1` is an
    unknown parameter to a daemon that predates it, and an unknown parameter is
    ignored rather than rejected, so an older daemon still replies 200 and is
    merely as slow as it was before.
    """
    try:
        with urllib.request.urlopen(f"{base.rstrip('/')}/health?probe=1",
                                    timeout=HEALTH_TIMEOUT_S) as response:
            return response.status == 200
    except (urllib.error.URLError, OSError, ValueError, TimeoutError):
        return False


def daemon_get(base: str, route: str, params: dict, vault: str | None,
               timeout: float = DAEMON_TIMEOUT_S, tolerate_missing_route: bool = False):
    """Ask the daemon, returning None only when there is no daemon to ask.

    An HTTP error is an answer: the daemon ran and refused. Catching it
    alongside the connection failures made a typo in `--vault` fall through to a
    direct search against whatever database the working directory resolved to,
    so the wrong corpus answered and the output said `(direct)` as if that were
    normal. Exit instead, since a search of a corpus the caller did not name is
    worse than no search.

    A 404 is the exception, and only for a caller that asks for the exception. It
    does not mean the daemon refused the question; it means this script is newer
    than the daemon answering it, which is the normal state of affairs between a
    `git pull` and the next restart of a process that never exits on its own. A
    route added here would otherwise be dead for as long as the old daemon stays
    up, and it would fail with a refusal rather than with anything that points at
    the real cause.

    The request itself is the liveness probe. A 1.0s precheck that ran here before
    the 30s request could only produce a false negative — calling a live daemon
    dead when it answered /health late during a reindex — and a false negative
    here means a silent wrong-corpus answer (the fallback resolves from the working
    directory) rather than a slow one. The exception path at the end already handles
    an absent daemon, measured at under 1ms to refuse the connection.
    """
    if vault:
        params = {**params, "vault": vault}
    url = f"{base.rstrip('/')}/{route}?{urlencode(params)}"
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            return json.load(response)
    except urllib.error.HTTPError as error:
        if error.code == 404 and tolerate_missing_route:
            print(f"[PKM Search: the daemon at {base} has no /{route} route, it predates "
                  f"this script -- answering locally. Restart it to get the fast path]",
                  file=sys.stderr)
            return None
        try:
            message = json.load(error).get("error", error.reason)
        except ValueError:
            message = error.reason
        raise SystemExit(f"daemon refused the request: {message}")
    except (urllib.error.URLError, OSError, ValueError, TimeoutError):
        return None


def default_database(db: str | None) -> Path:
    if db:
        return Path(db).resolve()
    current = Path.cwd().resolve()
    for candidate in (current, *current.parents):
        database = candidate / ".obsidian" / "pkm_index.db"
        if database.exists():
            return database
    return current / ".obsidian" / "pkm_index.db"


def auto_spawn_daemon(db: str | None, base: str = DEFAULT_DAEMON) -> int | None:
    """Start one local daemon behind the FTS answer when none is healthy.

    The base is a parameter because the caller may have been pointed at another
    daemon with --daemon, and health-checking the default instead answered about
    a daemon nobody asked for: a healthy daemon on the default port suppressed
    the spawn even though the daemon the search actually used was down.
    """
    if daemon_healthy(base):
        return None
    database = default_database(db)
    root = database.parent.parent if database.parent.name == ".obsidian" else database.parent
    command = [sys.executable, str(Path(__file__).with_name("searchd.py")), "--vault", f"brain={root}"]
    extra = {"creationflags": 0x00000008 | 0x00000200} if sys.platform == "win32" else {"start_new_session": True}
    try:
        process = subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, **extra)
        return process.pid
    except OSError:
        return None


def fast_fts_search(query: str, db_path: str | Path, top: int = 10, expand: bool = True) -> list[dict]:
    """Search FTS5 directly, without importing numpy or fastembed.

    `expand` still defaults True here while the CLI flag defaults False, which is
    deliberate rather than an oversight. The judged a/b that moved the CLI default
    measured the fused lexical+vector path, where expansion hurts because extra
    list memberships dominate rank position in the RRF sum. This function is
    lexical only, so that mechanism does not apply and nothing has measured it.
    Both call sites pass the flag explicitly, so this default is never exercised;
    it is left as it was rather than changed on the strength of a measurement of a
    different code path.
    """
    database = Path(db_path)
    if not database.exists():
        return []
    terms = [query]
    if expand:
        from entity_expansion import expand_query
        terms = expand_query(query, database)
    expression = " OR ".join(f'"{term.replace(chr(34), "")}"' for term in terms if term.strip())
    if not expression:
        return []
    connection = sqlite3.connect(f"file:{database.resolve()}?mode=ro", uri=True, timeout=0.05)
    try:
        cursor = connection.cursor()
        rows = cursor.execute(
            """
            SELECT sections.id, sections.path, sections.heading, sections.start_line,
                   snippet(sections_fts, 1, '[', ']', '...', 24)
            FROM sections_fts JOIN sections ON sections.id = sections_fts.section_id
            WHERE sections_fts MATCH ? ORDER BY bm25(sections_fts) LIMIT ?
            """, (expression, max(top * 3, top)),
        ).fetchall()
        title_rows = cursor.execute(
            """
            SELECT path, title FROM note_titles_fts
            WHERE note_titles_fts MATCH ? ORDER BY bm25(note_titles_fts) LIMIT ?
            """, (expression, max(top * 3, top)),
        ).fetchall()
    except sqlite3.Error:
        return []
    finally:
        connection.close()
    results = [
        {"path": row[1], "heading": row[2], "line": row[3], "score": 1.0 / (index + 1),
         "text": row[4], "snippet": row[4]}
        for index, row in enumerate(rows)
    ]
    known = {row["path"] for row in results}
    for path, title in title_rows:
        if path not in known:
            results.append({"path": path, "heading": title, "line": 1,
                            "score": 1.0 / (len(results) + 1), "text": title, "snippet": title})
    return dedupe_by_path(results)[:top]


def fast_session_search(query: str, db_path: str | Path, top: int = 10, touched: str = "any") -> list[dict]:
    """Read the session projection without importing the embedding indexer."""
    database = Path(db_path)
    if not database.exists():
        return []
    # When filtering by touched type, restrict to only touch matches (not title-only).
    # This is correct because title-only matches have no touch row, so filtering by
    # vault flag makes no sense for them.
    needle = f"%{query}%"
    if touched == "notes":
        where_clause = "WHERE session_touches.target_path LIKE ? AND session_touches.vault = 1"
        params = (needle, max(1, top))
    elif touched == "code":
        where_clause = "WHERE session_touches.target_path LIKE ? AND session_touches.vault = 0"
        params = (needle, max(1, top))
    else:
        where_clause = "WHERE sessions_idx.title LIKE ? OR session_touches.target_path LIKE ?"
        params = (needle, needle, max(1, top))
    connection = sqlite3.connect(f"file:{database.resolve()}?mode=ro", uri=True, timeout=0.05)
    try:
        rows = connection.execute(
            f"""
            SELECT DISTINCT sessions_idx.session_id, sessions_idx.title, sessions_idx.created,
                   sessions_idx.trace_path, sessions_idx.cost_usd, sessions_idx.repo,
                   sessions_idx.note_path
            FROM sessions_idx LEFT JOIN session_touches
              ON session_touches.session_id = sessions_idx.session_id
            {where_clause}
            ORDER BY sessions_idx.created DESC, sessions_idx.title
            LIMIT ?
            """,
            params,
        ).fetchall()
    except sqlite3.Error:
        return []
    finally:
        connection.close()
    keys = ("session_id", "title", "created", "trace_path", "cost_usd", "repo", "path")
    return [dict(zip(keys, row)) for row in rows]


def direct_search(query: str, top: int, db: str | None, rerank: bool = True):
    import index_pkm_meta as pkm  # numpy and fastembed cost ~1.3s to import, skip them for a daemon hit

    rows = pkm.search_index(query, db_path=db, limit=max(top * 3, top), rerank=rerank)
    results = [
        {"path": row["path"], "heading": row["heading"],
         "line": row["start_line"], "score": row["score"],
         "text": row.get("text", ""),
         **({"rerank_score": row["rerank_score"]} if "rerank_score" in row else {})}
        for row in rows
    ]
    return dedupe_by_path(results)[:top]


def dedupe_by_path(results: list[dict]) -> list[dict]:
    """Keep the best-scoring section per note, in rank order.

    The daemon does this for its own answers. Repeating it here keeps the two
    paths agreeing, which is the whole reason the ranking itself lives in one
    place: a direct search that returned a note three times would look like a
    different search rather than the same one without a daemon.
    """
    seen, kept = set(), []
    for row in results:
        key = (row.get("vault", ""), row["path"])
        if key in seen:
            continue
        seen.add(key)
        kept.append(row)
    return kept


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


# How far a result must fall below the best one before the list is called over.
# Below this the gap is noise: a fused score of 0.0328 against 0.0246 is rank 1
# against rank 2 on one side of the fusion instead of both, not a worse answer.
CUTOFF_DROP = 0.15
# Only the head of the list is searched for the cut. A drop at rank 9 is not a
# boundary worth reporting, because nobody was going to read rank 9 anyway.
CUTOFF_WINDOW = 8
# Where a cross-encoder logit stops meaning "this section answers the question".
# The sign is the model's own decision boundary and it holds across queries, which
# no other number here does: measured on this vault, every section above zero was
# on topic and the queries with nothing to find scored every section near -11.
# Mirrors `index_pkm_meta.ANSWER_LOGIT` rather than importing it, because that
# module pulls numpy and fastembed and costs 1.3s, which is most of the budget
# for a query answered by the daemon. Change both or neither.
ANSWER_LOGIT = 0.0


def sigmoid(value: float) -> float:
    return 1.0 / (1.0 + math.exp(-value))


def fused_cutoff(results: list[dict]) -> tuple[int, str]:
    """Find the cut from RRF scores alone, for when there is no rerank to read.

    A fused score is a sum of `1/(60 + rank)` capped at 0.0328, so it says nothing
    about whether a section answers anything -- only how the two retrievers ranked
    it relative to each other. The largest relative drop is all such a score can
    support, and when the list is flat the honest answer is that it is flat.
    """
    values = [max(row["score"], 0.0) for row in results]
    top = values[0]
    if top <= 0:
        return len(results), ""
    relative = [value / top for value in values]
    window = min(CUTOFF_WINDOW, len(relative) - 1)
    drops = [(relative[index] - relative[index + 1], index + 1) for index in range(window)]
    best_drop, cut = max(drops, default=(0.0, len(results)))
    if best_drop < CUTOFF_DROP:
        return len(results), ("no clear cutoff without rerank, these score within "
                              f"{round(best_drop * 100)}% of each other")
    return cut, f"results below {cut} score under {round(relative[cut] * 100)}% of the best"


def find_cutoff(results: list[dict]) -> tuple[int, str]:
    """Return how many results are worth reading, and why that is the number.

    An agent reading search output has no way to tell where the answers stop and
    the vocabulary matches start, so it reads all of them; that is where a third
    of the retrieval budget measured on this vault went.

    The cross-encoder logit is the only number in a result that means the same
    thing from one query to the next, because it is a judgement about this query
    and this section rather than a position in a list, and its sign is the model's
    own decision about whether the section answers the question. So the cut is the
    boundary the model already drew, and nothing more.

    Looking for a cliff among the sections that did qualify was tried and removed.
    It is the same mistake as reading a rank as a score: on a query where all eight
    results were genuinely on topic the widest gap fell between ranks 1 and 2 and
    cut seven good answers, because a gap between two strong scores separates very
    good from good, not answers from noise. Squashing the logits through a sigmoid
    to compare them has the mirror failure -- a real spread of 6.9 down to 4.3
    comes back as 0.9990 to 0.9860, so every list looks flat.

    Three outcomes, each of which the caller has to act on differently: nothing
    here answers the question, the answers stop at rank N, or all of these
    answer it and there is no boundary to report.
    """
    if not results:
        return 0, ""
    if not all("rerank_score" in row for row in results):
        return fused_cutoff(results)

    logits = [row["rerank_score"] for row in results]
    answers = [index for index, logit in enumerate(logits) if logit > ANSWER_LOGIT]
    if not answers:
        return 0, (f"nothing here answers this; the best section scored "
                   f"{sigmoid(logits[0]):.0%} and the rest lower. Rephrase, or accept "
                   "that the vault does not cover it -- reading these will not help")

    # Contiguous because the list is sorted by the same logit being tested.
    cut = answers[-1] + 1
    if cut >= len(results):
        return cut, ""
    return cut, (f"results below {cut} scored under {sigmoid(logits[cut]):.0%}, "
                 f"against {sigmoid(logits[cut - 1]):.0%} at {cut}")


def print_results(query: str, source: str, results: list[dict]):
    """Print the head with the text that matched and the tail with headings only.

    A path and a heading cannot be judged, so a caller given only those opens the
    note, and the note is thousands of tokens against the few hundred of the
    section that actually matched. Printing the section for the results that are
    worth reading and the heading for the ones that are not is the whole saving:
    the head can be judged without a read, and the tail is cheap to carry in case
    the cutoff was wrong.
    """
    print(f'\n--- Semantic Search Results for: "{query}" ({source}) ---')
    cut, reason = find_cutoff(results)
    if cut == 0 and reason:
        # Before the list rather than after it, because the point of the line is
        # that the list below is not worth reading and a warning underneath it
        # arrives after the caller has already read it.
        print(f"\n   ! {reason}\n")
    for index, row in enumerate(results, 1):
        where = f"{row['vault']}/" if "vault" in row else ""
        # Whichever number put the list in this order. Printing the fused score
        # beside a rerank ordering gave a column that ran 0.025, 0.031, 0.031 --
        # readable as the ranking being broken rather than as two different scores.
        score = sigmoid(row["rerank_score"]) if "rerank_score" in row else row["score"]
        print(f"{index}. [{score:.3f}] {where}{row['path']} "
              f"(line {row['line']}) -> {row['heading']}")
        if index <= cut and row.get("text"):
            print(f"      {row['text']}")
        if index == cut and cut < len(results):
            print(f"\n   --- stop here: {reason}. "
                  f"{len(results) - cut} weaker result(s) follow, headings only ---")
    if reason and 0 < cut >= len(results):
        print(f"\n   ! {reason}")


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


def outline_search(args, direct: bool, vault: str | None):
    """Answer structurally: facet coverage, headings, line numbers, link neighbours.

    Prefers the daemon, which has the vectors resident and so can put a real
    semantic track beside the structural one. Falls back to running both tracks
    here with FTS5 standing in for track 1, which is a weaker first track but
    leaves the facet counts and the graph walk -- the two signals this mode exists
    for -- exactly as good, because neither one needs a model.
    """
    began = time.perf_counter()
    facets = [term for term in (args.facets or "").split(",") if term.strip()] or None
    params = {"q": args.query, "limit": args.top, "hops": args.hops}
    if facets:
        params["facets"] = ",".join(facets)
    if args.semantic:
        params["semantic"] = "1"
    payload = None if direct else daemon_get(args.daemon, "outline", params, vault,
                                             tolerate_missing_route=True)
    if payload is not None:
        print(f"[PKM Search: daemon active @ {args.daemon.rsplit(':', 1)[-1]} | "
              f"{payload.get('took_ms', 0)}ms | outline]", file=sys.stderr)
        for name, outline in payload["outlines"].items():
            print(f"\n--- {name} ---")
            print(outline)
        print_stale(payload.get("stale") or {})
        return

    import dual_track

    database = default_database(args.db)
    if not Path(database).exists():
        raise SystemExit(f"no index at {database}; run index_pkm_meta.py first")
    if args.vault and args.vault != "all" and not args.db:
        print(f"[PKM Search: --vault {args.vault} cannot be honoured without the daemon, "
              f"answering from {database}]", file=sys.stderr)
    payload = dual_track.dual_track_search(
        database, args.query,
        semantic=lambda query: fast_fts_search(query, database, args.top, args.expand),
        hops=args.hops, top=args.top, facets=facets,
        gate_semantic=not args.semantic,
    )
    print(f"[PKM Search: daemon offline | dual-track outline answered in "
          f"{(time.perf_counter() - began) * 1000:.1f}ms]", file=sys.stderr)
    print(dual_track.render_outline(payload))


def build_parser():
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
    parser.add_argument("--no-spawn", action="store_true",
                        help="Answer from FTS5 without starting a daemon behind the answer")
    parser.add_argument("--no-reindex", action="store_true",
                        help="Report files missing from the index without starting a pass over them")
    parser.add_argument("--unlinked", action="store_true",
                        help="Treat the query as a note title and list unlinked mentions of it")
    parser.add_argument("--no-rerank", action="store_true",
                        help="Return the fused order instead of reordering the top with the "
                        "cross-encoder. Saves a second or two and loses precision")
    parser.add_argument("--expand", action=argparse.BooleanOptionalAction, default=False,
                        help="Resolve matching titles, aliases, paths, and outbound links "
                             "before searching. Off by default: over 20 judged questions it "
                             "cost 39 points of precision@10 (20.5%% against 59.5%%) and 360ms "
                             "at p50, and it left first-useful rank unchanged, so it degrades "
                             "results 2-10 without improving the top hit")
    parser.add_argument("--sessions", action="store_true",
                        help="Search indexed session rollup titles and touched files")
    parser.add_argument("--touched", choices=("any", "notes", "code"), default="any",
                        help="Filter --sessions results to sessions that edited vault notes (notes) "
                             "or repository code (code). Defaults to any")
    parser.add_argument("--outline", "--headers-only", dest="outline", action="store_true",
                        help="Structural answer: which facets each note covered, the heading "
                             "and line each was found on, and the 1-2 hop link neighbourhood. "
                             "Suppresses section text, so a multi-concept query costs a few "
                             "hundred tokens instead of several whole notes")
    parser.add_argument("--facets", default=None,
                        help="Override facet clustering with a comma-separated list, e.g. "
                             "--facets \"stroke,fatigue,coding\". Each entry is one facet, "
                             "verbatim, stop list and tokenizer skipped")
    parser.add_argument("--hops", type=int, default=2, choices=(1, 2),
                        help="How far to walk the link graph from the facet winners (default 2)")
    parser.add_argument("--semantic", action="store_true",
                        help="Force the semantic track on for an --outline query that "
                             "would otherwise skip it. Off by default above two facets, "
                             "where it was measured to add about 140ms and rank worse "
                             "than the facet counts on their own")
    parser.add_argument("--test-healing", action="store_true", help=argparse.SUPPRESS)
    return parser


def main():
    args = build_parser().parse_args()

    # --db names one database and the daemon answers from the corpora it was
    # started with, so honouring both meant printing results from one and the
    # name of the other. The flag wins, because it is the more specific request.
    direct = args.direct or bool(args.db)
    vault = None if direct else args.vault

    if args.sessions:
        began = time.perf_counter()
        payload = None if direct else daemon_get(
            args.daemon, "sessions", {"q": args.query, "limit": args.top, "touched": args.touched}, vault
        )
        if payload is not None:
            results = payload["results"]
            print(f"[PKM Search: daemon active @ {args.daemon.rsplit(':', 1)[-1]} | {payload.get('took_ms', 0)}ms]",
                  file=sys.stderr)
        else:
            database = default_database(args.db)
            results = fast_session_search(args.query, database, args.top, touched=args.touched)
            print(f"[PKM Search: daemon offline | SQLite session fallback answered in "
                  f"{(time.perf_counter() - began) * 1000:.1f}ms]", file=sys.stderr)
        for index, row in enumerate(results, 1):
            print(f"{index}. {row['title']} ({row['session_id']}) -> {row['path']}")
            if row.get("trace_path"):
                print(f"   trace: {row['trace_path']}")
        return

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

    if args.outline:
        outline_search(args, direct, vault)
        return

    rerank = not args.no_rerank
    params = {"q": args.query, "limit": args.top, "expand": "1" if args.expand else "0"}
    if rerank:
        params["rerank"] = "1"
    if args.no_reindex:
        params["reindex"] = "0"
    began = time.perf_counter()
    payload = None if direct else daemon_get(args.daemon, "search", params, vault)
    order = "rerank" if rerank else "fused"
    if payload is not None:
        results, stale = payload["results"], payload["stale"]
        indexed = ", ".join(f"{name} @ {(at or 'never')[:19]}"
                            for name, at in payload["indexed_at"].items())
        source = f"daemon, {order}: {indexed}"
        print(f"[PKM Search: daemon active @ {args.daemon.rsplit(':', 1)[-1]} | "
              f"{payload.get('took_ms', 0)}ms]", file=sys.stderr)
    else:
        if direct:
            expanded_query = args.query
            if args.expand:
                from entity_expansion import expand_query
                expanded_query = " ".join(expand_query(args.query, default_database(args.db)))
            results = direct_search(expanded_query, args.top, args.db, rerank)
            missing = direct_stale(args.db, not args.no_reindex)
            stale = {"vault": missing} if missing["count"] or missing.get("no_index") else {}
            source = f"direct, {order} @ {(missing['indexed_at'] or 'never')[:19]}"
            print(f"[PKM Search: direct semantic search | {(time.perf_counter() - began) * 1000:.1f}ms]",
                  file=sys.stderr)
        else:
            pid = None if args.no_spawn else auto_spawn_daemon(args.db, args.daemon)
            database = default_database(args.db)
            # The fallback resolves its database from the working directory,
            # because only the daemon holds the name-to-root mapping that
            # --vault is written against. Say so out loud when the caller named
            # a corpus: answering a question asked of one named corpus out of
            # whichever index the current directory sits in is the silent
            # wrong-corpus answer that daemon_get above refuses to give.
            if args.vault and args.vault != "all" and not args.db:
                print(f"[PKM Search: --vault {args.vault} cannot be honoured without the daemon, "
                      f"answering from {database}]", file=sys.stderr)
            results = fast_fts_search(args.query, database, args.top, args.expand)
            stale = {}
            source = f"FTS5 fallback @ {database}"
            action = f" -> auto-spawned PID {pid}" if pid else ""
            print(f"[PKM Search: daemon offline{action} | FTS5 fallback answered in "
                  f"{(time.perf_counter() - began) * 1000:.1f}ms]", file=sys.stderr)

    print_results(args.query, source, results)
    print_stale(stale)


if __name__ == "__main__":
    main()
