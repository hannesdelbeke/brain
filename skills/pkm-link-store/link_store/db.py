"""SQLite bitemporal storage engine for pkm-link-store."""

from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .schema_compiler import CompiledSchema, compile_schema


def utc_now_iso() -> str:
    """Return current UTC timestamp in ISO-8601 format."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class LinkStoreDB:
    """Bitemporal SQLite graph store with schema-validated nodes and edges."""

    def __init__(
        self,
        db_path: Path | str,
        schema: CompiledSchema | None = None,
        schema_path: Path | str | None = None,
    ) -> None:
        self.db_path = Path(db_path).expanduser()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            os.chmod(self.db_path.parent, 0o700)
        except OSError:
            pass

        self.schema = schema or compile_schema(schema_path)
        self.conn = sqlite3.connect(str(self.db_path), timeout=60.0)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA busy_timeout=60000")
        self.conn.execute("PRAGMA foreign_keys=ON")
        self._init_schema()
        try:
            os.chmod(self.db_path, 0o600)
        except OSError:
            pass

    def _init_schema(self) -> None:
        with self.conn:
            for stmt in self.schema.ddl:
                self.conn.execute(stmt)
            self.conn.execute(
                "INSERT OR REPLACE INTO meta(key, value) VALUES (?, ?)",
                ("schema_name", self.schema.schema_name),
            )
            self.conn.execute(
                "INSERT OR REPLACE INTO meta(key, value) VALUES (?, ?)",
                ("schema_version", self.schema.schema_version),
            )

    def close(self) -> None:
        """Close the underlying SQLite connection."""
        self.conn.close()

    def __enter__(self) -> "LinkStoreDB":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def upsert_node(
        self,
        node_id: str,
        node_type: str,
        title: str | None = None,
        metadata: dict[str, Any] | None = None,
        recorded_at: str | None = None,
    ) -> None:
        """Insert or update an entity node after validating node_type."""
        self.schema.validate_node_type(node_type)
        now = recorded_at or utc_now_iso()
        meta_json = json.dumps(metadata, sort_keys=True) if metadata is not None else None
        with self.conn:
            self.conn.execute(
                """
                INSERT INTO nodes(id, node_type, title, metadata_json, recorded_at, expired_at)
                VALUES (?, ?, ?, ?, ?, NULL)
                ON CONFLICT(id) DO UPDATE SET
                    node_type = excluded.node_type,
                    title = COALESCE(excluded.title, nodes.title),
                    metadata_json = COALESCE(excluded.metadata_json, nodes.metadata_json),
                    expired_at = NULL
                """,
                (node_id, node_type, title, meta_json, now),
            )

    def expire_node(self, node_id: str, expired_at: str | None = None) -> None:
        """Mark a node as expired at the given UTC timestamp."""
        ts = expired_at or utc_now_iso()
        with self.conn:
            self.conn.execute(
                "UPDATE nodes SET expired_at = ? WHERE id = ? AND expired_at IS NULL",
                (ts, node_id),
            )

    def get_node(self, node_id: str) -> dict[str, Any] | None:
        """Fetch a node row by ID, or None if missing."""
        row = self.conn.execute(
            "SELECT * FROM nodes WHERE id = ?", (node_id,)
        ).fetchone()
        return dict(row) if row else None

    def upsert_alias(
        self, alias: str, node_id: str, recorded_at: str | None = None
    ) -> None:
        """Map an alias string to a canonical node_id."""
        now = recorded_at or utc_now_iso()
        with self.conn:
            self.conn.execute(
                """
                INSERT INTO aliases(alias, node_id, recorded_at)
                VALUES (?, ?, ?)
                ON CONFLICT(alias) DO UPDATE SET
                    node_id = excluded.node_id,
                    recorded_at = excluded.recorded_at
                """,
                (alias, node_id, now),
            )

    def resolve_alias(self, alias: str) -> str | None:
        """Resolve an alias to its canonical node_id, or None."""
        row = self.conn.execute(
            "SELECT node_id FROM aliases WHERE alias = ?", (alias,)
        ).fetchone()
        return str(row["node_id"]) if row else None

    def upsert_edge(
        self,
        src_id: str,
        dst_id: str,
        rel: str,
        source_adapter: str,
        valid_from: str | None = None,
        valid_to: str | None = None,
        source_ref: str | None = None,
        confidence: float = 1.0,
        metadata: dict[str, Any] | None = None,
        recorded_at: str | None = None,
    ) -> None:
        """Insert or update an active edge after validating schema domain/range."""
        src_row = self.conn.execute(
            "SELECT node_type FROM nodes WHERE id = ?", (src_id,)
        ).fetchone()
        dst_row = self.conn.execute(
            "SELECT node_type FROM nodes WHERE id = ?", (dst_id,)
        ).fetchone()
        if not src_row:
            raise ValueError(f"Source node does not exist: {src_id!r}")
        if not dst_row:
            raise ValueError(f"Destination node does not exist: {dst_id!r}")

        self.schema.validate_edge(rel, src_row["node_type"], dst_row["node_type"])
        now = recorded_at or utc_now_iso()
        meta_json = json.dumps(metadata, sort_keys=True) if metadata is not None else None
        vf_key = valid_from or ""

        with self.conn:
            existing = self.conn.execute(
                """
                SELECT edge_id FROM edges
                WHERE src_id = ? AND dst_id = ? AND rel = ?
                  AND COALESCE(valid_from, '') = ?
                  AND expired_at IS NULL
                """,
                (src_id, dst_id, rel, vf_key),
            ).fetchone()
            if existing:
                self.conn.execute(
                    """
                    UPDATE edges
                    SET valid_to = COALESCE(?, valid_to),
                        source_ref = COALESCE(?, source_ref),
                        confidence = ?,
                        metadata_json = COALESCE(?, metadata_json)
                    WHERE edge_id = ?
                    """,
                    (valid_to, source_ref, confidence, meta_json, existing["edge_id"]),
                )
            else:
                self.conn.execute(
                    """
                    INSERT INTO edges(
                        src_id, dst_id, rel, valid_from, valid_to,
                        recorded_at, expired_at, source_adapter, source_ref,
                        confidence, metadata_json
                    )
                    VALUES (?, ?, ?, ?, ?, ?, NULL, ?, ?, ?, ?)
                    """,
                    (
                        src_id,
                        dst_id,
                        rel,
                        valid_from,
                        valid_to,
                        now,
                        source_adapter,
                        source_ref,
                        confidence,
                        meta_json,
                    ),
                )

    def expire_edge(
        self,
        src_id: str,
        dst_id: str,
        rel: str,
        valid_from: str | None = None,
        expired_at: str | None = None,
    ) -> None:
        """Mark matching active edge(s) as expired."""
        ts = expired_at or utc_now_iso()
        with self.conn:
            if valid_from is None:
                self.conn.execute(
                    """
                    UPDATE edges SET expired_at = ?
                    WHERE src_id = ? AND dst_id = ? AND rel = ? AND expired_at IS NULL
                    """,
                    (ts, src_id, dst_id, rel),
                )
            else:
                self.conn.execute(
                    """
                    UPDATE edges SET expired_at = ?
                    WHERE src_id = ? AND dst_id = ? AND rel = ?
                      AND COALESCE(valid_from, '') = ? AND expired_at IS NULL
                    """,
                    (ts, src_id, dst_id, rel, valid_from),
                )

    def get_sync_state(self, adapter: str, source_key: str) -> dict[str, Any] | None:
        """Retrieve incremental ingestion cursor state for a source key."""
        row = self.conn.execute(
            "SELECT * FROM sync_state WHERE adapter = ? AND source_key = ?",
            (adapter, source_key),
        ).fetchone()
        return dict(row) if row else None

    def set_sync_state(
        self,
        adapter: str,
        source_key: str,
        byte_offset: int = 0,
        line_count: int = 0,
        prefix_sha256: str | None = None,
        extra: dict[str, Any] | None = None,
    ) -> None:
        """Persist incremental ingestion cursor state for a source key."""
        now = utc_now_iso()
        extra_json = json.dumps(extra, sort_keys=True) if extra is not None else None
        with self.conn:
            self.conn.execute(
                """
                INSERT INTO sync_state(
                    adapter, source_key, byte_offset, line_count,
                    prefix_sha256, extra_json, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(adapter, source_key) DO UPDATE SET
                    byte_offset = excluded.byte_offset,
                    line_count = excluded.line_count,
                    prefix_sha256 = excluded.prefix_sha256,
                    extra_json = excluded.extra_json,
                    updated_at = excluded.updated_at
                """,
                (adapter, source_key, byte_offset, line_count, prefix_sha256, extra_json, now),
            )
