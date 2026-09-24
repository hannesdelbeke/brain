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


def expand_query(query: str, db_path: str | Path, max_terms: int = 24) -> list[str]:
    """Return ``query`` plus names connected to entities it identifies.

    The database is the source of truth, so this stays a cheap read-only lookup:
    no model, filesystem walk, or YAML parser is loaded on a search hot path.
    """
    terms = [query]
    database = Path(db_path)
    if not query.strip() or not database.exists():
        return terms
    tokens = {token.casefold() for token in re.findall(r"[\w']+", query, re.UNICODE)}
    if not tokens:
        return terms
    try:
        connection = sqlite3.connect(f"file:{database.resolve()}?mode=ro", uri=True, timeout=0.05)
        connection.row_factory = sqlite3.Row
        try:
            columns = {row[1] for row in connection.execute("PRAGMA table_info(notes)")}
            alias_column = "aliases" if "aliases" in columns else "'[]' AS aliases"
            rows = connection.execute(
                f"SELECT path, filename, tags, {alias_column} FROM notes"
            ).fetchall()
            matched_paths = set()
            for row in rows:
                filename = Path(row["filename"]).stem
                path_parts = [part for part in Path(row["path"]).parts if part]
                candidates = [filename, *path_parts, *_values(row["tags"]), *_values(row["aliases"])]
                candidate_tokens = {
                    token.casefold() for candidate in candidates
                    for token in re.findall(r"[\w']+", candidate, re.UNICODE)
                }
                if tokens & candidate_tokens:
                    matched_paths.add(row["path"])
                    for candidate in candidates:
                        _add(terms, candidate)
            if matched_paths:
                placeholders = ",".join("?" for _ in matched_paths)
                edges = connection.execute(
                    f"SELECT raw_target, resolved_target_path FROM edges WHERE source_path IN ({placeholders})",
                    tuple(matched_paths),
                ).fetchall()
                by_path = {row["path"]: row for row in rows}
                for edge in edges:
                    _add(terms, edge["raw_target"])
                    target = by_path.get(edge["resolved_target_path"])
                    if target:
                        _add(terms, Path(target["filename"]).stem)
                        for alias in _values(target["aliases"]):
                            _add(terms, alias)
        finally:
            connection.close()
    except sqlite3.Error:
        return terms
    return terms[:max_terms]
