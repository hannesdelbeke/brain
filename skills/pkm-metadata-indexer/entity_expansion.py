"""Resolve short entity queries to indexed names, aliases, paths, and links."""

from __future__ import annotations

import json
import re
import sqlite3
from pathlib import Path


def _values(value: str | None) -> list[str]:
    try:
        parsed = json.loads(value or "[]")
    except ValueError:
        return []
    return [str(item) for item in parsed] if isinstance(parsed, list) else []


def _add(values: list[str], value: str | None) -> None:
    value = (value or "").strip()
    if value and value.casefold() not in {item.casefold() for item in values}:
        values.append(value)


def _tokens(text: str) -> set[str]:
    return {token.casefold() for token in re.findall(r"[\w']+", text or "", re.UNICODE)}


def _open(db_path: str | Path) -> sqlite3.Connection | None:
    database = Path(db_path)
    if not database.exists():
        return None
    connection = sqlite3.connect(f"file:{database.resolve()}?mode=ro", uri=True, timeout=0.05)
    connection.row_factory = sqlite3.Row
    return connection


def _load_notes(connection: sqlite3.Connection) -> list[sqlite3.Row]:
    """One pass over `notes`, shared by both expanders.

    `aliases` is read through a column check rather than assumed, because the
    column was added later and an index built before it still answers searches.
    """
    columns = {row[1] for row in connection.execute("PRAGMA table_info(notes)")}
    alias_column = "aliases" if "aliases" in columns else "'[]' AS aliases"
    return connection.execute(f"SELECT path, filename, tags, {alias_column} FROM notes").fetchall()


# Prepared notes, keyed by database path, holding the file stamp they were built
# from. One entry per corpus, replaced rather than accumulated.
_PREPARED: dict[str, tuple[tuple[int, int], list[dict], dict[str, int]]] = {}

# A query this long is describing a problem, not naming a thing. Expansion exists
# to turn `ec` into `Example Corporation`; there is no entity to resolve in a
# sentence, and every extra name it adds is read by the embedder and the
# cross-encoder as part of the question being asked.
MAX_ENTITY_TOKENS = 8
# How much of a corpus a token may appear in and still identify anything. A token
# in a tenth of the vault selects a tenth of the vault. Measured as a share rather
# than a fixed count so it holds on a 2-note test corpus and a 3,000-note one, and
# floored at one note so a small corpus still expands at all.
MAX_DOCUMENT_SHARE = 0.10
# How many of a query's identifying tokens one note must account for before its
# neighbours are worth adding. Below this the note shares a word with the query
# rather than naming what the query is about.
MIN_COVERAGE = 0.6


def _prepare(rows: list[sqlite3.Row]) -> list[dict]:
    """Do the JSON and regex work once per note instead of once per note per facet.

    Every row of `notes` was being decoded from JSON and tokenised on each call,
    and the tag tokens were rebuilt inside the per-facet loop -- so a five-facet
    query tokenised every tag in the vault five times. None of it varies with the
    query, which makes it exactly the work a cache is for.
    """
    prepared = []
    for row in rows:
        stem = Path(row["filename"]).stem
        aliases = _values(row["aliases"])
        tags = _values(row["tags"])
        name_tokens = _tokens(stem)
        for alias in aliases:
            name_tokens |= _tokens(alias)
        candidates = [stem, *[part for part in Path(row["path"]).parts if part],
                      *tags, *aliases]
        prepared.append({
            "path": row["path"],
            "stem": stem,
            "aliases": aliases,
            "tags": tags,
            "name_tokens": frozenset(name_tokens),
            "tag_tokens": [(tag, frozenset(_tokens(tag))) for tag in tags],
            "candidates": candidates,
            "candidate_tokens": frozenset(
                token for candidate in candidates for token in _tokens(candidate)),
        })
    return prepared


def _document_frequency(prepared: list[dict]) -> dict[str, int]:
    """How many notes each candidate token appears in.

    Which tokens are worth matching on is a property of the corpus, not something
    a stopword list can be written for once: `session` and `vault` identify a note
    in somebody else's vault and identify nothing in this one. Counting is cheap
    here because it happens once per reindex, beside the scan that already runs.
    """
    frequency: dict[str, int] = {}
    for row in prepared:
        for token in row["candidate_tokens"]:
            frequency[token] = frequency.get(token, 0) + 1
    return frequency


def identifying_tokens(query: str, db_path: str | Path) -> set[str]:
    """The query tokens that can select a note, dropping the ones that select many.

    Matching on any shared token is what made expansion return the vault: a
    fifteen-word question shares `the`, `files` or `command` with almost every
    note, so every note matched and the term list filled with whichever titles the
    scan reached first. A token common enough to do that is exactly the token that
    cannot identify an entity, which makes document frequency the test.
    """
    tokens = _tokens(query)
    if not tokens:
        return set()
    prepared = prepared_notes(db_path)
    if not prepared:
        return set()
    frequency = document_frequency(db_path)
    ceiling = max(1, int(len(prepared) * MAX_DOCUMENT_SHARE))
    return {token for token in tokens if 0 < frequency.get(token, 0) <= ceiling}


def document_frequency(db_path: str | Path) -> dict[str, int]:
    """Candidate-token document frequencies for a corpus, cached with its scan."""
    prepared_notes(db_path)
    cached = _PREPARED.get(str(Path(db_path)))
    return cached[2] if cached else {}


def prepared_notes(db_path: str | Path) -> list[dict]:
    """`notes`, prepared and cached until the database file changes.

    Keyed on the index's mtime and size rather than a version counter, because a
    reindex rewrites the file and nothing else does: the daemon holds this across
    thousands of queries and must not answer from a stale corpus after one. Two
    threads racing here both build the same value and one assignment wins, which
    costs a duplicated scan and never a wrong answer.
    """
    database = Path(db_path)
    try:
        stat = database.stat()
    except OSError:
        return []
    stamp = (stat.st_mtime_ns, stat.st_size)
    cached = _PREPARED.get(str(database))
    if cached is not None and cached[0] == stamp:
        return cached[1]
    connection = _open(database)
    if connection is None:
        return []
    try:
        rows = _load_notes(connection)
    finally:
        connection.close()
    prepared = _prepare(rows)
    _PREPARED[str(database)] = (stamp, prepared, _document_frequency(prepared))
    return prepared


def expand_query(query: str, db_path: str | Path, max_terms: int = 24) -> list[str]:
    """Return ``query`` plus names connected to entities it identifies.

    The database is the source of truth, so this stays a cheap read-only lookup:
    no model, filesystem walk, or YAML parser is loaded on a search hot path.

    Returns the query alone when there is no entity to resolve, which is most
    queries. Expansion used to fire on any single shared token, so a sentence
    matched most of the vault and came back with two dozen unrelated titles
    appended -- and because the caller hands the result to `search_index` whole,
    those titles were embedded and cross-encoded as part of the question. On this
    vault that cost symptom recall@5 about sixty points. A term is only added now
    when the query names something: see `MAX_ENTITY_TOKENS`, `MAX_DOCUMENT_SHARE`
    and `MIN_COVERAGE`.
    """
    terms = [query]
    if not query.strip():
        return terms
    tokens = _tokens(query)
    if not tokens or len(tokens) > MAX_ENTITY_TOKENS:
        return terms
    try:
        rows = prepared_notes(db_path)
        tokens = identifying_tokens(query, db_path)
        if not tokens:
            return terms
        needed = max(1, round(len(tokens) * MIN_COVERAGE))
        # Best-covering notes first. Ordering by the scan instead meant the term
        # budget was spent on whichever note sqlite happened to return first,
        # which on a date-named vault is the oldest note that shares a word.
        matches = []
        for row in rows:
            covered = len(tokens & row["candidate_tokens"])
            if covered >= needed:
                matches.append((covered, row))
        matches.sort(key=lambda match: -match[0])
        matched_paths = set()
        for _, row in matches:
            matched_paths.add(row["path"])
            for candidate in row["candidates"]:
                _add(terms, candidate)
            if len(terms) >= max_terms:
                break
        if matched_paths:
            connection = _open(db_path)
            if connection is None:
                return terms[:max_terms]
            try:
                placeholders = ",".join("?" for _ in matched_paths)
                edges = connection.execute(
                    f"SELECT raw_target, resolved_target_path FROM edges WHERE source_path IN ({placeholders})",
                    tuple(matched_paths),
                ).fetchall()
            finally:
                connection.close()
            by_path = {row["path"]: row for row in rows}
            for edge in edges:
                _add(terms, edge["raw_target"])
                target = by_path.get(edge["resolved_target_path"])
                if target:
                    _add(terms, target["stem"])
                    for alias in target["aliases"]:
                        _add(terms, alias)
    except sqlite3.Error:
        return terms
    return terms[:max_terms]


def expand_facets(facets: list[str], db_path: str | Path,
                  per_facet_limit: int = 4) -> dict[str, list[str]]:
    """Synonyms for several facets at once, in one pass over `notes`.

    Two differences from `expand_query`, both of which a facet needs and a
    single-entity lookup does not.

    It is one scan for N facets rather than N scans. `expand_query` reads every
    row of `notes` per call, which is the right trade once per query and the wrong
    one five times: on this vault that pass is most of the latency budget the
    structural track has to fit inside.

    And it is much narrower about what counts as a synonym. `expand_query` also
    returns path components and the name of every outbound link, which widens a
    one-word lookup usefully and destroys a facet: a facet that has absorbed a
    dozen loosely-related names matches most of the vault, every note's coverage
    count then rises by the same one, and the count stops discriminating -- the
    exact flattening that facet coverage exists to avoid. So only two things get
    in. An alias of a note this facet already names, which is what an alias is
    for; and a tag whose own text contains the facet term, so `stroke` picks up
    `post-stroke` and not the `health` sitting beside it.
    """
    wanted = {facet: _tokens(facet) for facet in facets if _tokens(facet)}
    found: dict[str, list[str]] = {facet: [] for facet in facets}
    if not wanted:
        return found
    try:
        rows = prepared_notes(db_path)
    except sqlite3.Error:
        return found

    for row in rows:
        for facet, tokens in wanted.items():
            bucket = found[facet]
            if len(bucket) >= per_facet_limit:
                continue
            if tokens & row["name_tokens"]:
                for alias in row["aliases"]:
                    _add(bucket, alias)
            for tag, tag_tokens in row["tag_tokens"]:
                if tokens & tag_tokens:
                    _add(bucket, tag)
    for facet in found:
        lowered = facet.casefold()
        found[facet] = [name for name in found[facet] if name.casefold() != lowered][:per_facet_limit]
    return found
