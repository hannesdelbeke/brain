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
_PREPARED: dict[str, tuple[tuple[int, int], list[dict]]] = {}


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
    _PREPARED[str(database)] = (stamp, prepared)
    return prepared


def expand_query(query: str, db_path: str | Path, max_terms: int = 24) -> list[str]:
    """Return ``query`` plus names connected to entities it identifies.

    The database is the source of truth, so this stays a cheap read-only lookup:
    no model, filesystem walk, or YAML parser is loaded on a search hot path.
    """
    terms = [query]
    if not query.strip():
        return terms
    tokens = _tokens(query)
    if not tokens:
        return terms
    try:
        rows = prepared_notes(db_path)
        matched_paths = set()
        for row in rows:
            if tokens & row["candidate_tokens"]:
                matched_paths.add(row["path"])
                for candidate in row["candidates"]:
                    _add(terms, candidate)
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
                    if len(bucket) < per_facet_limit:
                        _add(bucket, alias)
            for tag, tag_tokens in row["tag_tokens"]:
                if len(bucket) < per_facet_limit and tokens & tag_tokens:
                    _add(bucket, tag)
    for facet in found:
        lowered = facet.casefold()
        found[facet] = [name for name in found[facet] if name.casefold() != lowered][:per_facet_limit]
    return found
