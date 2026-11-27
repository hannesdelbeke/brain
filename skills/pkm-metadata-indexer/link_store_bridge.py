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

# Relations followed by expand_candidates, strongest evidence first.
EXPAND_RELS: tuple[str, ...] = (
    "documented_in",
    "continued_in",
    "derived_from",
    "handed_over_to",
    "child_of",
    "modified_file",
    "mentions_session",
)
# Node types worth showing as direct context, most informative first. Handovers
# are handed_over_to edges, so their neighbors are Sessions.
CONTEXT_TYPES: tuple[str, ...] = ("Session", "Branch", "Commit", "Url")
MIN_CONTEXT = 3
MAX_CONTEXT = 5
EXPANDED_TEXT_CHARS = 1500  # matches the `text` width searchd asks search_index for
SQL_BATCH = 500

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


def _direct_context(snap: GraphSnapshot, nid: str) -> list[dict[str, str]]:
    """Direct active neighbors of nid that explain a hit, excluding wikilinks."""
    found: list[tuple[int, str, dict[str, str]]] = []
    for nbr_id, rel in snap.adj.get(nid, ()):
        ntype, title = snap.nodes[nbr_id]
        if rel == "wikilinks_to" or ntype not in CONTEXT_TYPES:
            continue
        item = {"node_id": nbr_id, "node_type": ntype, "title": title, "rel": rel}
        found.append((CONTEXT_TYPES.index(ntype), nbr_id, item))
    found.sort(key=lambda entry: (entry[0], entry[1], entry[2]["rel"]))
    return [item for _, _, item in found]


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
                ctx = list(context_by_idx[idx].values())[:MAX_CONTEXT]
                results[idx]["cluster_id"] = cid
                results[idx]["cluster_size"] = size
                # Only shared evidence belongs to the cluster; backfill is per hit.
                for item in ctx:
                    shared_entities[item["node_id"]] = item
                if idx in resolved and len(ctx) < MIN_CONTEXT:
                    present = {item["node_id"] for item in ctx}
                    for item in _direct_context(snap, resolved[idx]):
                        if len(ctx) >= MAX_CONTEXT:
                            break
                        if item["node_id"] not in present:
                            present.add(item["node_id"])
                            ctx.append(item)
                results[idx]["link_context"] = ctx
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


def _node_documents(
    snap: GraphSnapshot, nid: str, corpora: list[str], transcripts: dict[str, list[str]]
) -> list[tuple[str, str]]:
    """(vault, path) pairs that could hold a node's text, best first.

    A Note is its own document. A Session is read through its transcript (the
    .jsonl alias) or, failing that, the notes that document it.
    """
    node_type = snap.nodes[nid][0]
    if node_type == "Note":
        vault, sep, path = nid.removeprefix("note:").partition("/")
        return [(vault, path)] if sep and vault in corpora else []
    if node_type != "Session":
        return []
    docs = [(vault, path) for path in transcripts.get(nid, ()) for vault in corpora]
    for nbr_id, rel in sorted(snap.adj.get(nid, ())):
        if rel == "documented_in" and snap.nodes[nbr_id][0] == "Note":
            docs += _node_documents(snap, nbr_id, corpora, transcripts)
    return docs


def _indexed_paths(db_path: Path, paths: list[str]) -> set[str]:
    """The subset of paths that have at least one section in this index."""
    if not db_path.exists():
        return set()
    try:
        conn = _connect_ro(db_path)
    except sqlite3.Error:
        return set()
    try:
        found: set[str] = set()
        for start in range(0, len(paths), SQL_BATCH):
            batch = paths[start : start + SQL_BATCH]
            placeholders = ",".join("?" * len(batch))
            found.update(
                str(row["path"])
                for row in conn.execute(
                    f"SELECT DISTINCT path FROM sections WHERE path IN ({placeholders})", batch
                )
            )
        return found
    except sqlite3.Error:
        return set()
    finally:
        conn.close()


def _best_sections(db_path: Path, paths: list[str], terms: set[str]) -> dict[str, dict[str, Any]]:
    """The section of each indexed path that matches the query best, else its first."""
    try:
        conn = _connect_ro(db_path)
    except sqlite3.Error:
        return {}
    try:
        placeholders = ",".join("?" * len(paths))
        rows = conn.execute(
            f"SELECT id, path, heading, start_line FROM sections "
            f"WHERE path IN ({placeholders}) ORDER BY path, start_line, chunk_index",
            paths,
        ).fetchall()
        # section_id is unindexed in FTS5, so read all candidates in one pass.
        texts = {
            row["section_id"]: str(row["content"] or "")
            for row in conn.execute(
                f"SELECT section_id, content FROM sections_fts WHERE section_id IN "
                f"(SELECT id FROM sections WHERE path IN ({placeholders}))",
                paths,
            )
        }
    except sqlite3.Error:
        return {}
    finally:
        conn.close()

    best: dict[str, tuple[tuple[int, int], dict[str, Any]]] = {}
    for row in rows:
        text = texts.get(row["id"], "")
        words = [w for w in re.findall(r"\w+", text.lower()) if w in terms]
        score = (len(set(words)), len(words))
        path = str(row["path"])
        if path in best and score <= best[path][0]:
            continue
        flat = " ".join(text.split())
        if len(flat) > EXPANDED_TEXT_CHARS:
            flat = flat[:EXPANDED_TEXT_CHARS].rsplit(" ", 1)[0] + " ..."
        best[path] = (
            score,
            {
                "path": path,
                "heading": row["heading"],
                "line": row["start_line"],
                "section_id": row["id"],
                "text": flat,
            },
        )
    return {path: section for path, (_, section) in best.items()}


def expand_candidates(
    results: list[dict[str, Any]],
    link_stores: dict[str, Path],
    vaults_by_name: dict[str, Any],
    max_seeds: int = 5,
    max_extra: int = 8,
    query: str = "",
) -> list[dict[str, Any]]:
    """Return up to max_extra new rows for 1-hop graph neighbors of the top results.

    The rows are unscored, so the caller must rerank them with the originals.
    A neighbor stays inside its seed's link-store DB, and only vaults in
    vaults_by_name (anything with a `.db` index path) are read. Seeds take turns,
    so one heavily linked hit cannot use every slot. `results` is not modified.
    """
    if not results or not link_stores or max_extra <= 0:
        return []

    # One queue of neighbors per seed: [(rel, candidate documents, seed row)]
    queues: list[list[tuple[str, list[tuple[str, str]], dict[str, Any]]]] = []
    wanted: dict[str, set[str]] = defaultdict(set)
    transcripts_by_db: dict[Path, dict[str, list[str]]] = {}
    for row in results[:max_seeds]:
        vname = str(row.get("vault") or "")
        if vname not in link_stores:
            continue
        db_path = link_stores[vname].expanduser().resolve()
        snap = _load_snapshot(db_path)
        if snap is None:
            continue
        seed = resolve_node_id(snap, vname, str(row.get("path") or ""))
        if not seed:
            continue
        corpora = sorted(
            name
            for name, path in link_stores.items()
            if name in vaults_by_name and path.expanduser().resolve() == db_path
        )
        transcripts = transcripts_by_db.get(db_path)
        if transcripts is None:
            transcripts = transcripts_by_db[db_path] = defaultdict(list)
            for alias, target in sorted(snap.aliases.items()):
                if alias.endswith(".jsonl"):
                    transcripts[target].append(alias)
        neighbors = sorted(
            (EXPAND_RELS.index(rel), nbr_id, rel)
            for nbr_id, rel in snap.adj.get(seed, ())
            if rel in EXPAND_RELS
        )
        queue = []
        for _, nbr_id, rel in neighbors:
            docs = _node_documents(snap, nbr_id, corpora, transcripts)
            if docs:
                queue.append((rel, docs, row))
                for vault, path in docs:
                    wanted[vault].add(path)
        if queue:
            queues.append(queue)

    indexed = {
        (vault, path)
        for vault, paths in wanted.items()
        for path in _indexed_paths(Path(vaults_by_name[vault].db), sorted(paths))
    }

    seen = {(row.get("vault"), row.get("path")) for row in results}
    chosen: list[tuple[tuple[str, str], str, dict[str, Any]]] = []
    pending = [iter(queue) for queue in queues]
    while pending and len(chosen) < max_extra:
        for queue_iter in list(pending):
            if len(chosen) >= max_extra:
                break
            for rel, docs, seed_row in queue_iter:
                # The first indexed document stands for the node; if that's
                # already a candidate, the neighbor is represented.
                doc = next((d for d in docs if d in indexed), None)
                if doc is None or doc in seen:
                    continue
                seen.add(doc)
                chosen.append((doc, rel, seed_row))
                break
            else:
                pending.remove(queue_iter)

    by_vault: dict[str, list[str]] = defaultdict(list)
    for (vault, path), _, _ in chosen:
        by_vault[vault].append(path)
    terms = set(re.findall(r"\w+", query.lower()))
    sections = {
        (vault, path): section
        for vault, paths in by_vault.items()
        for path, section in _best_sections(Path(vaults_by_name[vault].db), paths, terms).items()
    }

    return [
        {
            "vault": doc[0],
            **sections[doc],
            "score": 0.0,
            "raw_sim": None,
            "snippet": None,
            "expanded_from": {
                "vault": seed_row.get("vault"),
                "path": seed_row.get("path"),
                "rel": rel,
            },
        }
        for doc, rel, seed_row in chosen
        if doc in sections
    ]


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
