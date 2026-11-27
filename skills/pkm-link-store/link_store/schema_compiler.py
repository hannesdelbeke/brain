"""Compile modular LinkML 1.x YAML schemas into SQLite DDL and edge validation rules."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import yaml

DEFAULT_SCHEMA_PATH = Path(__file__).resolve().parent.parent / "schema" / "linkstore.yaml"

DDL_STATEMENTS = (
    """
    CREATE TABLE IF NOT EXISTS nodes (
        id TEXT PRIMARY KEY,
        node_type TEXT NOT NULL,
        title TEXT,
        metadata_json TEXT,
        recorded_at TEXT NOT NULL,
        expired_at TEXT
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_nodes_active_type
    ON nodes(node_type)
    WHERE expired_at IS NULL
    """,
    """
    CREATE TABLE IF NOT EXISTS aliases (
        alias TEXT PRIMARY KEY,
        node_id TEXT NOT NULL REFERENCES nodes(id) ON DELETE CASCADE,
        recorded_at TEXT NOT NULL,
        alias_kind TEXT
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_aliases_node_id
    ON aliases(node_id)
    """,
    """
    CREATE TABLE IF NOT EXISTS edges (
        edge_id INTEGER PRIMARY KEY AUTOINCREMENT,
        src_id TEXT NOT NULL REFERENCES nodes(id) ON DELETE CASCADE,
        dst_id TEXT NOT NULL REFERENCES nodes(id) ON DELETE CASCADE,
        rel TEXT NOT NULL,
        valid_from TEXT,
        valid_to TEXT,
        recorded_at TEXT NOT NULL,
        expired_at TEXT,
        source_adapter TEXT NOT NULL,
        source_ref TEXT,
        confidence REAL DEFAULT 1.0,
        metadata_json TEXT
    )
    """,
    """
    CREATE UNIQUE INDEX IF NOT EXISTS idx_edges_active_unique
    ON edges(src_id, dst_id, rel, COALESCE(valid_from, ''))
    WHERE expired_at IS NULL
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_edges_active_src
    ON edges(src_id, rel)
    WHERE expired_at IS NULL
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_edges_active_dst
    ON edges(dst_id, rel)
    WHERE expired_at IS NULL
    """,
    """
    CREATE TABLE IF NOT EXISTS sync_state (
        adapter TEXT NOT NULL,
        source_key TEXT NOT NULL,
        byte_offset INTEGER NOT NULL DEFAULT 0,
        line_count INTEGER NOT NULL DEFAULT 0,
        prefix_sha256 TEXT,
        extra_json TEXT,
        updated_at TEXT NOT NULL,
        PRIMARY KEY (adapter, source_key)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS meta (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL
    )
    """,
)


@dataclass(frozen=True)
class CompiledSchema:
    """Compiled LinkML schema with concrete node types, edge rules, and SQLite DDL."""

    schema_name: str
    schema_version: str
    node_types: frozenset[str]
    edge_rules: frozenset[tuple[str, str, str]]
    ddl: tuple[str, ...]

    def validate_node_type(self, node_type: str) -> None:
        """Raise ValueError if node_type is not a concrete Entity class."""
        if node_type not in self.node_types:
            raise ValueError(
                f"Unknown node_type {node_type!r}; allowed: {sorted(self.node_types)}"
            )

    def validate_edge(self, rel: str, src_type: str, dst_type: str) -> None:
        """Raise ValueError if (rel, src_type, dst_type) violates domain/range rules."""
        self.validate_node_type(src_type)
        self.validate_node_type(dst_type)
        if (rel, src_type, dst_type) not in self.edge_rules:
            raise ValueError(
                f"Edge ({rel!r}, {src_type!r} -> {dst_type!r}) is not permitted by schema"
            )


def _load_yaml_recursive(
    path: Path,
    seen: set[Path],
    classes: dict[str, dict],
    slots: dict[str, dict],
) -> dict:
    resolved = path.resolve()
    if resolved in seen:
        return {}
    seen.add(resolved)

    with resolved.open("r", encoding="utf-8") as fh:
        doc = yaml.safe_load(fh) or {}

    for imp in doc.get("imports") or []:
        if not isinstance(imp, str) or ":" in imp:
            continue
        candidate = resolved.parent / f"{imp}.yaml"
        if candidate.exists():
            _load_yaml_recursive(candidate, seen, classes, slots)

    for cname, cdef in (doc.get("classes") or {}).items():
        classes[cname] = cdef or {}
    for sname, sdef in (doc.get("slots") or {}).items():
        slots[sname] = sdef or {}

    return doc


def _is_entity_subclass(name: str, classes: dict[str, dict]) -> bool:
    seen: set[str] = set()
    cur = name
    while cur and cur not in seen:
        seen.add(cur)
        cdef = classes.get(cur) or {}
        parent = cdef.get("is_a")
        if parent == "Entity":
            return True
        cur = parent
    return False


def compile_schema(schema_path: Path | str | None = None) -> CompiledSchema:
    """Parse modular LinkML YAML starting at schema_path and return a CompiledSchema."""
    root = Path(schema_path) if schema_path else DEFAULT_SCHEMA_PATH
    classes: dict[str, dict] = {}
    slots: dict[str, dict] = {}
    root_doc = _load_yaml_recursive(root, set(), classes, slots)

    node_types = frozenset(
        cname
        for cname, cdef in classes.items()
        if not cdef.get("abstract") and _is_entity_subclass(cname, classes)
    )

    rules: set[tuple[str, str, str]] = set()
    for slot_name, sdef in slots.items():
        domain = sdef.get("domain")
        rng = sdef.get("range")
        if not domain and not rng:
            continue
        annotations = sdef.get("annotations") or {}
        domains: Iterable[str] = annotations.get("allowed_domains") or (
            [domain] if domain else []
        )
        ranges: Iterable[str] = annotations.get("allowed_ranges") or (
            [rng] if rng else []
        )
        for src_type in domains:
            for dst_type in ranges:
                if src_type in node_types and dst_type in node_types:
                    rules.add((slot_name, src_type, dst_type))

    return CompiledSchema(
        schema_name=str(root_doc.get("name") or "linkstore"),
        schema_version=str(root_doc.get("version") or "0.1.0"),
        node_types=node_types,
        edge_rules=frozenset(rules),
        ddl=DDL_STATEMENTS,
    )
