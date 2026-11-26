"""Read-only SQLite bridge from pkm-metadata-indexer/searchd.py to pkm-link-store DBs.

Uses only Python stdlib + numpy, with zero imports from pkm-link-store.
All DB access is strictly read-only (?mode=ro) with graceful fallback on
missing, unconfigured, or corrupt databases.
"""

from __future__ import annotations

import json
import math
import posixpath
import re
import sqlite3
import threading
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np  # noqa: F401  (kept available for vector/matrix extensions)

Z_HUB_DEGREE: dict[str, int] = {
    "Branch": 50,
    "Url": 40,
    "Session": 80,
    "Note": 100,
    "File": 80,
    "Commit": 50,
    "Repo": 20,
}
DEFAULT_HUB_DEGREE = 80

_UUID_RE = re.compile(r"([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})")


@dataclass
class GraphSnapshot:
    db_path: Path
    mtime_ns: int
    size: int
    nodes: dict[str, tuple[str, str]]  # node_id -> (node_type, title)
    aliases: dict[str, str]  # alias -> node_id
    adj: dict[str, list[tuple[str, str]]]  # node_id -> [(neighbor_id, rel)]
    degree: dict[str, int]


_CACHE_LOCK = threading.Lock()
_SNAPSHOT_CACHE: dict[Path, GraphSnapshot] = {}


def _connect_ro(db_path: Path) -> sqlite3.Connection:
    uri = f"file:{db_path.resolve().as_posix()}?mode=ro"
    conn = sqlite3.connect(uri, uri=True, timeout=5.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=5000")
    return conn


def _load_snapshot(db_path: Path) -> GraphSnapshot | None:
    resolved = db_path.expanduser().resolve()
    try:
        st = resolved.stat()
    except OSError:
        return None

    with _CACHE_LOCK:
        cached = _SNAPSHOT_CACHE.get(resolved)
        if cached and cached.mtime_ns == st.st_mtime_ns and cached.size == st.st_size:
            return cached

    try:
        conn = _connect_ro(resolved)
    except sqlite3.Error:
        return None

    try:
        nodes: dict[str, tuple[str, str]] = {}
        default_branches: set[str] = set()
        for row in conn.execute(
            "SELECT id, node_type, title, metadata_json FROM nodes WHERE expired_at IS NULL"
        ):
            nid = str(row["id"])
            ntype = str(row["node_type"])
            title = str(row["title"] or nid)
            if ntype == "Branch" and row["metadata_json"]:
                try:
                    meta = json.loads(row["metadata_json"])
                    if isinstance(meta, dict) and meta.get("is_default"):
                        default_branches.add(nid)
                        continue
                except (ValueError, TypeError):
                    pass
            nodes[nid] = (ntype, title)

        aliases: dict[str, str] = {}
        for row in conn.execute("SELECT alias, node_id FROM aliases"):
            nid = str(row["node_id"])
            if nid in nodes:
                aliases[str(row["alias"])] = nid

        adj: dict[str, list[tuple[str, str]]] = defaultdict(list)
        for row in conn.execute(
            "SELECT src_id, dst_id, rel FROM edges WHERE expired_at IS NULL AND rel != 'in_repo'"
        ):
            src = str(row["src_id"])
            dst = str(row["dst_id"])
            rel = str(row["rel"])
            if src in default_branches or dst in default_branches:
                continue
            if src not in nodes or dst not in nodes:
                continue
            adj[src].append((dst, rel))
            adj[dst].append((src, rel))

        degree = {nid: len(nbrs) for nid, nbrs in adj.items()}
        snap = GraphSnapshot(
            db_path=resolved,
            mtime_ns=st.st_mtime_ns,
            size=st.st_size,
            nodes=nodes,
            aliases=aliases,
            adj=dict(adj),
            degree=degree,
        )
    except sqlite3.Error:
        return None
    finally:
        conn.close()

    with _CACHE_LOCK:
        _SNAPSHOT_CACHE[resolved] = snap
    return snap


def resolve_node_id(snap: GraphSnapshot, vault_name: str, rel_path: str) -> str | None:
    """Map (vault_name, rel_path) to an active canonical node ID in snap."""
    norm = posixpath.normpath(rel_path.replace("\\", "/").lstrip("/"))
    if norm in snap.aliases:
        return snap.aliases[norm]

    if norm.endswith(".jsonl"):
        name = posixpath.basename(norm)
        if name in snap.aliases:
            return snap.aliases[name]
        uuid_m = _UUID_RE.search(norm)
        if uuid_m:
            uid = uuid_m.group(1)
            if name.startswith("agent-"):
                cand = f"session:{uid}:{name[:-6]}"
                if cand in snap.nodes:
                    return cand
            cand = f"session:{uid}"
            if cand in snap.nodes:
                return cand
    else:
        cand = f"note:{vault_name}/{norm}"
        if cand in snap.nodes:
            return cand
        if norm in snap.nodes:
            return norm
    return None


def _pair_adamic_adar(snap: GraphSnapshot, u: str, v: str) -> tuple[float, list[dict[str, str]]]:
    nbrs_u = {nid: rel for nid, rel in snap.adj.get(u, ())}
    nbrs_v = {nid: rel for nid, rel in snap.adj.get(v, ())}
    score = 0.0
    shared: list[dict[str, str]] = []

    if v in nbrs_u:
        score += 1.0
        v_type, v_title = snap.nodes[v]
        shared.append({"node_id": v, "node_type": v_type, "title": v_title, "rel": nbrs_u[v]})

    for z in set(nbrs_u).intersection(nbrs_v):
        deg = snap.degree.get(z, 0)
        z_type, z_title = snap.nodes[z]
        hub_cap = Z_HUB_DEGREE.get(z_type, DEFAULT_HUB_DEGREE)
        if deg < 2 or deg > hub_cap:
            continue
        score += 1.0 / math.log(deg)
        shared.append({"node_id": z, "node_type": z_type, "title": z_title, "rel": nbrs_u[z]})

    return score, shared


def cluster_results(
    results: list[dict[str, Any]],
    link_stores: dict[str, Path],
    threshold: float = 0.15,
) -> list[dict[str, Any]]:
    """Annotate merged results in-place with cluster_id/cluster_size/link_context and return clusters.

    Results are grouped by resolved link_store DB path so corpora sharing a DB
    (e.g. brain + traces -> personal.db) cluster together while separate DBs stay isolated.
    Result ordering is strictly preserved.
    """
    if not results or not link_stores:
        return []

    by_db: dict[Path, list[int]] = defaultdict(list)
    for idx, row in enumerate(results):
        vname = row.get("vault")
        if vname and vname in link_stores:
            by_db[link_stores[vname].expanduser().resolve()].append(idx)

    clusters_out: list[dict[str, Any]] = []
    cluster_counter = 0

    for db_path, indices in by_db.items():
        snap = _load_snapshot(db_path)
        if snap is None:
            continue

        resolved: dict[int, str] = {}
        for idx in indices:
            row = results[idx]
            nid = resolve_node_id(snap, str(row.get("vault") or ""), str(row.get("path") or ""))
            if nid:
                resolved[idx] = nid

        parent = {idx: idx for idx in indices}

        def find(x: int) -> int:
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        def union(a: int, b: int) -> None:
            ra, rb = find(a), find(b)
            if ra != rb:
                parent[rb] = ra

        context_by_idx: dict[int, dict[str, dict[str, str]]] = defaultdict(dict)
        res_indices = list(resolved.keys())
        for i in range(len(res_indices)):
            ia = res_indices[i]
            na = resolved[ia]
            for j in range(i + 1, len(res_indices)):
                ib = res_indices[j]
                nb = resolved[ib]
                if na == nb:
                    union(ia, ib)
                    continue
                score, shared = _pair_adamic_adar(snap, na, nb)
                if score >= threshold:
                    union(ia, ib)
                    for item in shared:
                        context_by_idx[ia][item["node_id"]] = item
                        context_by_idx[ib][item["node_id"]] = item

        groups: dict[int, list[int]] = defaultdict(list)
        for idx in indices:
            groups[find(idx)].append(idx)

        for _, member_indices in groups.items():
            cid = f"c{cluster_counter}"
            cluster_counter += 1
            size = len(member_indices)
            shared_entities: dict[str, dict[str, str]] = {}
            for idx in member_indices:
                ctx = list(context_by_idx[idx].values())[:5]
                results[idx]["cluster_id"] = cid
                results[idx]["cluster_size"] = size
                results[idx]["link_context"] = ctx
                for item in ctx:
                    shared_entities[item["node_id"]] = item
            clusters_out.append(
                {
                    "cluster_id": cid,
                    "size": size,
                    "members": [
                        {"vault": results[idx].get("vault"), "path": results[idx].get("path")}
                        for idx in member_indices
                    ],
                    "shared_entities": list(shared_entities.values())[:10],
                }
            )

    return clusters_out


def entity_links(db_path: Path, vault_name: str, note_path: str, limit: int = 50) -> list[dict[str, Any]]:
    """Return active entity links for a note/session from the read-only link store."""
    snap = _load_snapshot(db_path)
    if snap is None:
        return []
    nid = resolve_node_id(snap, vault_name, note_path)
    if not nid:
        return []
    out: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for nbr_id, rel in snap.adj.get(nid, ()):
        if (nbr_id, rel) in seen:
            continue
        seen.add((nbr_id, rel))
        ntype, title = snap.nodes.get(nbr_id, ("Unknown", nbr_id))
        out.append({"node_id": nbr_id, "node_type": ntype, "title": title, "rel": rel})
        if len(out) >= limit:
            break
    return out


def status(link_stores: dict[str, Path]) -> dict[str, Any]:
    """Return non-raising health status for each configured vault link store."""
    out: dict[str, Any] = {}
    for vault_name, db_path in sorted(link_stores.items()):
        resolved = db_path.expanduser().resolve()
        snap = _load_snapshot(resolved)
        if snap is None:
            out[vault_name] = {"db": str(resolved), "ok": False}
        else:
            edge_count = sum(len(v) for v in snap.adj.values()) // 2
            out[vault_name] = {
                "db": str(resolved),
                "ok": True,
                "nodes": len(snap.nodes),
                "edges": edge_count,
            }
    return out
