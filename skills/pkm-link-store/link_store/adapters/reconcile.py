"""Fold short-id Session stubs (session:<8hex>) into their full session nodes."""

from __future__ import annotations

import json

from ..db import SHORT_ID_KIND, SHORT_SESSION_RE, LinkStoreDB, utc_now_iso

_PREFIX = "session:"


def _move_edges(db: LinkStoreDB, stub: str, full: str) -> tuple[int, int]:
    """Re-point the stub's active edges at full; expire the originals."""
    moved = dropped = 0
    rows = db.conn.execute(
        "SELECT * FROM edges WHERE expired_at IS NULL AND (src_id = ? OR dst_id = ?)",
        (stub, stub),
    ).fetchall()
    for row in rows:
        src = full if row["src_id"] == stub else row["src_id"]
        dst = full if row["dst_id"] == stub else row["dst_id"]
        duplicate = db.conn.execute(
            """
            SELECT 1 FROM edges
            WHERE src_id = ? AND dst_id = ? AND rel = ?
              AND COALESCE(valid_from, '') = ? AND expired_at IS NULL
            """,
            (src, dst, row["rel"], row["valid_from"] or ""),
        ).fetchone()
        if src == dst or duplicate:
            dropped += 1
        else:
            db.upsert_edge(
                src,
                dst,
                row["rel"],
                row["source_adapter"],
                valid_from=row["valid_from"],
                valid_to=row["valid_to"],
                source_ref=row["source_ref"],
                confidence=row["confidence"],
                metadata=json.loads(row["metadata_json"]) if row["metadata_json"] else None,
            )
            moved += 1
        # By edge_id: expire_edge() would also hit sibling edges sharing the triple.
        with db.conn:
            db.conn.execute(
                "UPDATE edges SET expired_at = ? WHERE edge_id = ?",
                (utc_now_iso(), row["edge_id"]),
            )
    return moved, dropped


def reconcile_sessions(db: LinkStoreDB) -> dict[str, int]:
    """Merge each active stub into the one full session sharing its prefix.

    Stubs with no match or several are left untouched. Merged stubs and their
    edges are expired, not deleted, so history stays queryable.
    """
    totals = {"stubs": 0, "merged": 0, "ambiguous": 0, "unmatched": 0, "moved_edges": 0, "dropped_edges": 0}
    stubs = [
        row["id"]
        for row in db.conn.execute(
            "SELECT id FROM nodes WHERE node_type = 'Session' AND expired_at IS NULL "
            "AND length(id) = ? ORDER BY id",
            (len(_PREFIX) + 8,),
        )
        if row["id"].startswith(_PREFIX) and SHORT_SESSION_RE.fullmatch(row["id"][len(_PREFIX):])
    ]
    totals["stubs"] = len(stubs)
    for stub in stubs:
        short = stub[len(_PREFIX):]
        matches = db.find_sessions_by_prefix(short)
        if len(matches) != 1:
            totals["ambiguous" if matches else "unmatched"] += 1
            continue
        full = matches[0]
        moved, dropped = _move_edges(db, stub, full)
        with db.conn:
            db.conn.execute("UPDATE aliases SET node_id = ? WHERE node_id = ?", (full, stub))
        # Later syncs that still see the short form must land on the full node.
        for alias in {short, short.lower()}:
            if db.resolve_alias(alias) in (None, full):
                db.upsert_alias(alias, full, alias_kind=SHORT_ID_KIND)
        db.expire_node(stub)
        totals["merged"] += 1
        totals["moved_edges"] += moved
        totals["dropped_edges"] += dropped
    return totals
