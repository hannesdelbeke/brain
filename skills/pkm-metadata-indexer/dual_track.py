"""Structural search: facet coverage over FTS5, and a 2-hop walk over the link graph.

This is the second track. The first one embeds the query and ranks sections by
cosine, which is the right answer for a question and a poor one for the two query
shapes that turn up most in agent transcripts:

  many concepts at once   `stroke fatigue dopamine coding hyperfocus` scored 0.007,
                          because a cross-encoder rewards a unified paragraph and
                          penalises multi-topic sprawl. The note that answers the
                          query covers four of the five in four separate sections,
                          and a whole-query score cannot represent "four of five".
  one broad word          `sex`, `Sarah`, `HRV` scored ~0.42 against the vectors and
                          tripped the "nothing here answers this" cutoff, which is
                          false: the vault is full of them. One word is not a
                          question, so there is nothing for a semantic model to be
                          similar to -- but it is an excellent graph seed.

Neither failure is a tuning problem, so neither is fixed by a threshold. What this
module returns instead of a score is a count and a line number: which facets a note
covered, and where. That is cheap to produce, cheap to read, and it is the signal
the semantic track structurally cannot carry.

Nothing here imports numpy or fastembed. The whole module is SQLite and the
standard library, so it runs in the ~15 ms the daemon has left after its own work
and in a bare `python` with no model installed. The semantic track is injected as a
callable for exactly that reason -- see `dual_track_search`.
"""

from __future__ import annotations

import json
import math
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

# The RRF constant. 60 is the value from the original Cormack paper and the one
# `searchd.rank` already fuses with, so the two fusions stay comparable; it is
# large enough that the top few ranks are not pulled far apart by rank alone.
RRF_K = 60

# Where a note stops being a bridge and starts being an index. Measured on this
# vault: the 99th percentile of total degree is 23, and everything above it is a
# map-of-content whose links say "these are all notes" rather than "these two
# things are related". It is a soft cutoff -- see `graph_neighborhood`.
HUB_DEGREE = 25

# How many graph rows to carry back. Past 30 the outline stops fitting the token
# budget this module exists to respect, and a 2-hop neighbourhood ordered by
# weight has nothing useful at rank 31.
GRAPH_LIMIT = 30

# Slots of that limit held open for hop 2. Without a reserve the 2-hop half of a
# "1-2 hops" answer is unreachable rather than merely rare: a 2-hop weight is a
# product of two factors below 1, so every 2-hop row sorts under every 1-hop row,
# and one seed with thirty resolved links fills the limit on its own. Measured on
# this vault a 432-link seed returned 29 rows at hop 1 and 1 at hop 2. The reserve
# is what makes the second hop -- the only part of this that finds a note sharing
# no vocabulary with the query -- actually show up.
GRAPH_HOP2_RESERVE = 12

# How many notes to seed from when the best-coverage tier walks nowhere. Small on
# purpose: this is a fallback from an empty graph, not a widening of the normal
# case, and seeding from twenty weak matches is how a 2-hop walk becomes most of
# the vault. It buys attempts, not reach -- the coverage floor at the call site is
# what decides which notes are eligible at all.
GRAPH_SEED_WIDEN = 12

# Headings printed per note. A note that covered four facets in nine sections is
# answered by the first two or three; the rest are the same claim again, and they
# are what turns a 200-token outline into a 900-token one.
HEADINGS_PER_NOTE = 3

# How many notes reach the cross-encoder when one is asked for.
RERANK_GATE = 10


def connect(db_path: str | Path) -> sqlite3.Connection:
    """Open a short-lived read-only connection with the maths this module needs.

    Deliberately not the daemon's resident `Vault.reader`. That connection is
    shared across handler threads under one lock, and holding it for a recursive
    CTE plus one FTS query per facet would serialise every other search behind
    this one. A fresh read-only connection costs tens of microseconds, which is
    nothing against the query, and it lets the two tracks run genuinely in
    parallel rather than taking turns on the same handle.
    """
    connection = sqlite3.connect(f"file:{Path(db_path).resolve()}?mode=ro", uri=True, timeout=0.05)
    _ensure_ln(connection)
    return connection


def _ensure_ln(connection: sqlite3.Connection) -> None:
    """Guarantee `ln()` exists, whoever built this Python's SQLite.

    The Adamic-Adar weight needs a natural log in SQL. SQLite only has one when it
    was compiled with SQLITE_ENABLE_MATH_FUNCTIONS, which the macOS venv's 3.53.4
    was and a system Python may not be. Probing and registering a Python fallback
    only when it is missing keeps the fast native path on the machines that have it
    and stops the whole graph track raising `no such function: ln` on the ones that
    do not, which would have been a crash rather than a degraded answer.
    """
    try:
        connection.execute("SELECT ln(2.0)").fetchone()
    except sqlite3.OperationalError:
        connection.create_function("ln", 1, lambda value: math.log(value) if value and value > 0 else 0.0)


# Adamic-Adar is conventionally written with a natural log, and the specification's
# `log` is read that way here rather than as SQLite's base-10 `log`. The difference
# is not cosmetic: the weight of a 2-hop path is a product of two factors, so
# switching base scales 1-hop weights by 1/ln(10) and 2-hop weights by 1/ln(10)^2 --
# it reorders 1-hop against 2-hop results rather than rescaling the list.
_FACET_SQL = """
SELECT sections.path AS path, sections.heading AS heading, sections.start_line AS start_line,
       bm25(sections_fts) AS score, 0 AS is_title
  FROM sections_fts
  JOIN sections ON sections.id = sections_fts.section_id
 WHERE sections_fts MATCH ?
 ORDER BY score
 LIMIT ?
"""

_TITLE_SQL = """
SELECT path, title AS heading, 1 AS start_line, bm25(note_titles_fts) AS score, 1 AS is_title
  FROM note_titles_fts
 WHERE note_titles_fts MATCH ?
 ORDER BY score
 LIMIT ?
"""

# One row per note reached, best path kept. The bare `start_node`, `path_str` and
# `hop` beside `MAX(weight)` are SQLite's documented min/max bare-column rule: they
# come from the row that produced the maximum, which is the path worth printing.
_GRAPH_SQL = """
WITH RECURSIVE
  node_degrees AS (
    SELECT node, SUM(n) AS degree FROM (
      SELECT source_path AS node, COUNT(*) AS n FROM edges GROUP BY source_path
      UNION ALL
      SELECT resolved_target_path AS node, COUNT(*) AS n FROM edges
       WHERE resolved_target_path IS NOT NULL AND resolved_target_path <> ''
       GROUP BY resolved_target_path
    ) GROUP BY node
  ),
  paths(start_node, current_node, path_str, hop, weight) AS (
    SELECT e.source_path,
           e.resolved_target_path,
           ' -> ' || e.source_path || ' -> ' || e.resolved_target_path || ' -> ',
           1,
           1.0 / ln(max(2, COALESCE(nd.degree, 2)))
      FROM edges e
      LEFT JOIN node_degrees nd ON nd.node = e.source_path
     WHERE e.source_path IN (SELECT value FROM json_each(:seeds))
       AND e.resolved_target_path IS NOT NULL AND e.resolved_target_path <> ''

    UNION ALL

    SELECT p.start_node,
           e.resolved_target_path,
           p.path_str || e.resolved_target_path || ' -> ',
           p.hop + 1,
           p.weight * (1.0 / ln(max(2, COALESCE(nd.degree, 2))))
      FROM paths p
      JOIN edges e ON e.source_path = p.current_node
      LEFT JOIN node_degrees nd ON nd.node = p.current_node
     WHERE p.hop < :hops
       AND e.resolved_target_path IS NOT NULL AND e.resolved_target_path <> ''
       AND instr(p.path_str, ' -> ' || e.resolved_target_path || ' -> ') = 0
       AND (COALESCE(nd.degree, 2) <= :hub_degree
            OR p.current_node IN (SELECT value FROM json_each(:facet_paths)))
  )
SELECT start_node, current_node, path_str, hop, weight FROM (
  SELECT start_node, current_node, path_str, hop, weight,
         ROW_NUMBER() OVER (PARTITION BY hop ORDER BY weight DESC) AS rank_in_hop
    FROM (
      SELECT start_node, current_node, path_str, hop, MAX(weight) AS weight
        FROM paths
       WHERE current_node NOT IN (SELECT value FROM json_each(:seeds))
       GROUP BY current_node
    )
)
 WHERE (hop = 1 AND rank_in_hop <= :hop1_slots)
    OR (hop > 1 AND rank_in_hop <= :hop2_slots)
 ORDER BY hop, weight DESC
"""


def facet_intersection(connection: sqlite3.Connection, facets: list[dict],
                       limit_per_facet: int = 200) -> dict[str, dict]:
    """Match each facet on its own and count how many of them each note covered.

    Keyed by note path, because coverage is a property of the note and not of a
    section: the whole point is that four facets found in four different sections
    of one note is a strong answer, which is invisible to anything ranking sections
    independently.

    `bm25()` returns a negative number and returns a more negative one for a better
    match, which is a trap worth neutralising here rather than in three callers --
    scores are flipped to positive-is-better on the way out, so `sum(bm25)` as the
    secondary sort means what it reads like.
    """
    found: dict[str, dict] = {}
    for facet in facets:
        expression = facet["expression"]
        rows = []
        for sql in (_FACET_SQL, _TITLE_SQL):
            try:
                rows += connection.execute(sql, (expression, limit_per_facet)).fetchall()
            except sqlite3.OperationalError:
                # A malformed MATCH expression is one facet's problem, not the
                # query's. Losing a facet lowers every coverage count by at most
                # one; raising would lose the answer altogether.
                continue
        for path, heading, start_line, score, is_title in rows:
            entry = found.setdefault(path, {"facets": set(), "score": 0.0,
                                            "headings": [], "titled": False})
            entry["facets"].add(facet["term"])
            entry["score"] += -float(score)
            if is_title:
                entry["titled"] = True
            else:
                entry["headings"].append({"heading": heading, "line": start_line,
                                          "score": -float(score), "facet": facet["term"]})
    for entry in found.values():
        entry["coverage"] = len(entry["facets"])
        # A list, not the set it was accumulated in: this dict goes out over the
        # daemon's JSON wire, and a set reaches `json.dumps` as a TypeError that
        # would surface as a 500 on a route that had already done all its work.
        entry["facets"] = sorted(entry["facets"])
        # Best-scoring sections first, then trimmed, so the ones kept are the ones
        # worth reading rather than the ones that happened to come back first.
        entry["headings"].sort(key=lambda row: row["score"], reverse=True)
        seen, unique = set(), []
        for row in entry["headings"]:
            if row["line"] in seen:
                continue
            seen.add(row["line"])
            unique.append(row)
        entry["headings"] = unique[:HEADINGS_PER_NOTE]
    return found


def rank_facet_matches(found: dict[str, dict]) -> list[dict]:
    """Order notes by facets covered first, summed relevance second.

    Coverage leads because it is the only one of the two that is comparable across
    notes: a note covering 4 of 5 concepts beats a note that mentions 1 of them
    forty times, and bm25 says the opposite.
    """
    ranked = [{"path": path, **entry} for path, entry in found.items()]
    ranked.sort(key=lambda row: (row["coverage"], row["score"]), reverse=True)
    return ranked


def graph_neighborhood(connection: sqlite3.Connection, seeds: list[str],
                       facet_paths: list[str] | None = None, hops: int = 2,
                       limit: int = GRAPH_LIMIT) -> list[dict]:
    """Walk out from `seeds` up to `hops` edges, discounting paths through hubs.

    A hard degree cutoff was tried first and is wrong: it severs the bridges worth
    crossing. A "Neuroscience MOC" with 40 links is exactly how `stroke` reaches
    `dopamine`, and a rule that drops every node over 25 links drops that route
    along with the junk. So the cutoff is soft in two ways. Every step is weighted
    by Adamic-Adar, `1/ln(degree(u))`, which makes a path through a well-connected
    node worth less without making it worth nothing; and a hub may be traversed
    regardless of degree when the hub itself matched a query facet, because a hub
    that is *on topic* is a bridge and not a switchboard.

    Degree is the node's total degree, in plus out. The specification computed it
    over `raw_target` and joined it against `resolved_target_path` -- one is
    wikilink text, the other a repo-relative path, so they never match, every
    degree came back NULL, every weight collapsed to the same constant and the hub
    filter could never fire. Out-degree has to be in the sum for the same reason:
    a map-of-content is a hub because it *links* to forty notes, and an in-degree
    count would score it 1 and wave it through.

    The gate reads the degree of the node being traversed *through*, which is
    `p.current_node` at hop 2 and the seed at hop 1 -- that is what `W(u -> v) =
    1/log(degree(u))` says, `u` being the source of the edge.
    """
    if not seeds:
        return []
    limit = max(2, limit)
    hop2 = min(GRAPH_HOP2_RESERVE, limit // 2) if hops > 1 else 0
    parameters = {
        "seeds": json.dumps(list(dict.fromkeys(seeds))),
        "facet_paths": json.dumps(list(dict.fromkeys(facet_paths or []))),
        "hops": max(1, min(2, hops)),
        "hub_degree": HUB_DEGREE,
        "hop1_slots": limit - hop2,
        "hop2_slots": hop2,
    }
    try:
        rows = connection.execute(_GRAPH_SQL, parameters).fetchall()
    except sqlite3.OperationalError:
        # No `edges` table, or a SQLite too old for the recursive form. The
        # structural track still has its facet half, so degrade rather than fail.
        return []
    neighbours = []
    for seed, path, path_str, hop, weight in rows:
        # The stored form is delimiter-wrapped so the cycle check can test for an
        # exact node rather than a substring: without the wrapping, `a.md` matches
        # inside `folder/a.md` and a legitimate step gets pruned as a revisit.
        route = [node for node in path_str.split(" -> ") if node]
        neighbours.append({
            "seed": seed, "path": path, "hop": hop, "weight": weight,
            "route": " -> ".join(route),
            # The node the path passed through, which is the part a reader needs to
            # judge whether a 2-hop result is a real connection or a coincidence.
            "via": route[-2] if hop > 1 and len(route) > 2 else "",
        })
    return neighbours


def reciprocal_rank_fusion(*rankings: list[str], k: int = RRF_K) -> dict[str, float]:
    """Fuse ranked path lists into one score per path.

    A path missing from a ranking contributes nothing from it rather than a penalty,
    which is the same as treating its rank as infinite. That asymmetry is the point:
    appearing in both tracks should beat appearing high in one, because the two
    tracks fail on different query shapes and agreement between them is the only
    evidence available that neither is failing here.
    """
    scores: dict[str, float] = {}
    for ranking in rankings:
        for index, path in enumerate(ranking):
            scores[path] = scores.get(path, 0.0) + 1.0 / (k + index + 1)
    return scores


def structural_search(db_path: str | Path, parsed: dict, hops: int = 2,
                      seeds: list[str] | None = None,
                      connection: sqlite3.Connection | None = None) -> dict:
    """Track 2 whole: facet intersection, then a graph walk seeded from its winners.

    The graph is seeded from the facet winners rather than from the semantic track
    when no seeds are handed in, so the structural track is self-sufficient and can
    answer on a machine with no embedding model at all.
    """
    owned = connection is None
    connection = connection or connect(db_path)
    try:
        found = facet_intersection(connection, parsed["facets"])
        ranked = rank_facet_matches(found)
        # Only notes that covered the most facets are worth walking from. Seeding
        # from all of them turned a 2-hop walk into most of the vault.
        best = ranked[0]["coverage"] if ranked else 0
        facet_paths = [row["path"] for row in ranked]
        graph_seeds = seeds or [row["path"] for row in ranked if row["coverage"] == best][:10]
        graph = graph_neighborhood(connection, graph_seeds, facet_paths, hops)
        if not graph and seeds is None and ranked:
            # The best tier is often a dead end, and silently so. A wikilink only
            # becomes an edge when its target resolves to a note, and the links in a
            # top-coverage note are frequently to scripts or people -- `search_vault.py`,
            # `Sarah` -- which resolve to nothing at all. Measured on the real vault:
            # the query this whole module was built for seeded exactly one 4/5 note
            # whose three links all resolved to None, so the graph section rendered
            # empty while a 2/5 note two rows down had a live neighbourhood sitting
            # right there. Reporting "no neighbourhood" in that case is a lie about
            # the graph rather than a fact about the query, so the walk gets one more
            # attempt from a wider seed set. It costs one more CTE, ~3ms, and only in
            # the case that would otherwise have returned nothing.
            #
            # The floor is what keeps that from being worse than silence. Widening to
            # every match walks from whatever happened to match one facet: the first
            # version of this fix seeded a 1/5 activity log and answered a query about
            # stroke and dopamine with three notes about wifi passwords, correctly
            # labelled and completely useless -- and worse than an empty section,
            # because an agent reading the outline will go and fetch them. So a
            # multi-facet query never seeds from a single-facet match. If nothing
            # covers two facets, staying silent is the honest answer.
            floor = min(best, 2) if len(parsed["facets"]) > 1 else best
            widened = [row["path"] for row in ranked
                       if row["coverage"] >= floor][:GRAPH_SEED_WIDEN]
            if widened != graph_seeds:
                graph_seeds = widened
                graph = graph_neighborhood(connection, graph_seeds, facet_paths, hops)
    finally:
        if owned:
            connection.close()
    return {"facets": ranked, "graph": graph, "seeds": graph_seeds}


def dual_track_search(db_path: str | Path, query: str, semantic=None, hops: int = 2,
                      top: int = 10, facets: list[str] | None = None, rerank=None) -> dict:
    """Run both tracks at once and fuse them.

    `semantic` is injected rather than imported. Track 1 lives behind a model that
    costs ~1.3 s to import and is already resident in the daemon, so the caller
    that has one passes it in and the caller that does not passes a lexical
    stand-in or nothing at all. Importing it here would have put numpy in the
    dependency path of a function whose whole claim is that it is cheap.

    The two tracks are genuinely concurrent: track 2 is SQLite and releases the GIL
    in the C extension while track 1 is either an HTTP call or a matrix multiply
    that does the same, so a thread pool of two is the right shape and not a
    decorative one.

    `rerank` is injected on the same terms and defaults to off, which is a
    deliberate departure from the specification's "gated cross-encoder, total
    latency < 50 ms". Those two cannot both hold: `search_vault`'s own header
    records the cross-encoder at 540 ms for 20 candidates in a bare process and
    2.4 s in one holding the DirectML session, which is every daemon by
    definition. The 50 ms budget is the one worth keeping, because the thing this
    module is for is giving an agent a cheap structural map instead of eight full
    reads; a caller that wants the model's opinion and will wait for it passes one
    in and pays for it knowingly.
    """
    from query_parser import parse_query_facets

    parsed = parse_query_facets(query, db_path, override=facets)

    with ThreadPoolExecutor(max_workers=2) as pool:
        structural_future = pool.submit(structural_search, db_path, parsed, hops)
        semantic_future = pool.submit(semantic, query) if semantic else None
        structural = structural_future.result()
        semantic_rows = []
        if semantic_future is not None:
            try:
                semantic_rows = semantic_future.result() or []
            except Exception:
                # The structural track is the one this module promises. A failed
                # semantic track costs precision on one query; raising costs the
                # answer.
                semantic_rows = []

    semantic_order = [row["path"] for row in semantic_rows]
    structural_order = [row["path"] for row in structural["facets"]]
    graph_order = [row["path"] for row in structural["graph"]]
    fused = reciprocal_rank_fusion(semantic_order, structural_order, graph_order)
    ordered = sorted(fused.items(), key=lambda item: item[1], reverse=True)[:top]

    by_path = {row["path"]: row for row in structural["facets"]}
    semantic_by_path = {row["path"]: row for row in semantic_rows}

    if rerank is not None and ordered:
        # Gated: the model reads the top RERANK_GATE notes and nothing below them,
        # which is the whole saving over reranking the candidate set. A failure here
        # leaves the fused order standing rather than losing the answer.
        gate = [path for path, _ in ordered[:RERANK_GATE]]
        try:
            scored = rerank(query, gate) or {}
            for path, score in scored.items():
                if path in by_path:
                    by_path[path]["rerank_score"] = score
            ordered = sorted(
                ordered,
                key=lambda item: (scored.get(item[0], float("-inf")), item[1]),
                reverse=True,
            )
        except Exception:
            pass

    return {
        "query": query,
        "parsed": parsed,
        "facet_count": len(parsed["facets"]),
        "semantic": semantic_rows,
        "structural": structural["facets"],
        "graph": structural["graph"],
        "seeds": structural["seeds"],
        "fused": [
            {"path": path, "score": score,
             "coverage": by_path.get(path, {}).get("coverage", 0),
             "headings": by_path.get(path, {}).get("headings", []),
             "semantic_score": semantic_by_path.get(path, {}).get("score"),
             **({"rerank_score": by_path[path]["rerank_score"]}
                if path in by_path and "rerank_score" in by_path[path] else {})}
            for path, score in ordered
        ],
    }


def stem(path: str) -> str:
    """A note's name, for the one place the full path is noise rather than signal."""
    return Path(path).stem or path


def stratify_hops(graph: list[dict], budget: int) -> list[dict]:
    """Split a display budget across hop distances instead of spending it on hop 1.

    Hop 1 keeps the larger share because a direct link is the stronger signal; hop 2
    keeps a guaranteed share because it is the only one that can reach a note the
    query has no words in common with, and a weight-ordered truncation gives it
    nothing. Unused slots fall back to the other hop, so a seed with no second hop
    still fills the budget.
    """
    if budget <= 0 or not graph:
        return []
    first = [row for row in graph if row["hop"] == 1]
    second = [row for row in graph if row["hop"] > 1]
    take_second = min(len(second), max(1, budget // 3)) if second else 0
    take_first = min(len(first), budget - take_second)
    take_second = min(len(second), budget - take_first)
    return first[:take_first] + second[:take_second]


def render_outline(payload: dict, top: int = 5, graph_top: int = 5) -> str:
    """The compact form: titles, headings and line numbers, no bodies.

    The measured failure this replaces is an agent reading eight whole notes to
    find out which one it wanted -- 135,000 tokens across eight sessions with over
    70% of it redundant. A heading and a line number is enough to choose, and the
    choice is what the read was for. So the body never appears here except for the
    single best semantic hit, which is the one result the caller is most likely to
    act on without a second call.
    """
    lines: list[str] = []
    facet_count = payload["facet_count"]

    best = (payload.get("semantic") or [None])[0]
    if best:
        score = best.get("rerank_score", best.get("score", 0.0))
        lines.append(f"=== Semantic Best Match (Score: {score:.3f}) ===")
        end = best.get("end_line") or best.get("line")
        span = f"[L{best['line']}-L{end}]" if end and end != best["line"] else f"[L{best['line']}]"
        lines.append(f"{best['path']} {span}")
        text = (best.get("text") or best.get("snippet") or "").strip().replace("\n", " ")
        if text:
            lines.append(f'   "{text[:160]}"')

    ranked = [row for row in payload["structural"] if row["coverage"]][:top]
    if ranked:
        lines.append("")
        lines.append("=== Facet Intersections (Titles & Headings) ===")
        for row in ranked:
            mark = " (title)" if row.get("titled") else ""
            lines.append(f"[{row['coverage']}/{facet_count} facets] {row['path']}{mark}")
            for heading in row["headings"]:
                lines.append(f"   └─ L{heading['line']}: {heading['heading']}")

    # Stratified rather than truncated, for the same reason the SQL reserves slots:
    # the 2-hop rows are the ones that found a note sharing no vocabulary with the
    # query, and sorting by weight and taking the first five buries every one of
    # them under a well-connected seed's direct links.
    graph = stratify_hops(payload["graph"], graph_top)
    if graph:
        # The heading names the depth actually walked rather than the default. Under
        # `--hops 1` a "(1-2 Hops)" heading over a list with no 2-hop row in it
        # reads as the second hop having found nothing, which is a different and
        # more interesting claim than not having been asked for.
        deepest = max(row["hop"] for row in graph)
        span = "1 Hop" if deepest == 1 else f"1-{deepest} Hops"
        lines.append("")
        lines.append(f"=== Graph Neighborhood ({span}) ===")
        for row in graph:
            hop = "1-hop" if row["hop"] == 1 else f"{row['hop']}-hops"
            via = f" via '{row['via']}'" if row.get("via") else ""
            lines.append(f"[{hop} from '{stem(row['seed'])}'{via}] {row['path']}")

    dropped = payload["parsed"].get("dropped")
    if dropped:
        lines.append("")
        lines.append(f"! {len(dropped)} term(s) past the facet cap were not searched: "
                     f"{', '.join(dropped)}")
    if not ranked and not graph and not best:
        lines.append(f'no facet or graph match for "{payload["query"]}"')
    return "\n".join(lines)
