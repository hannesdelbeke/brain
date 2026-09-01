"""Scratch, read-only analysis to assemble judging candidates. Not committed.

Builds three of the four sample categories automatically (fusion-promoted,
hub-target, AA-disagrees); the fourth (plain wikilinked baseline) is sampled
directly from wikilink_ground_truth(). Prints everything needed to judge by
hand -- does not call any LLM judge itself.
"""
from __future__ import annotations

import json
import os
import sys
import urllib.request
from pathlib import Path
from urllib.parse import urlencode

sys.path.insert(0, str(Path(__file__).resolve().parent))

from shared_neighbor_experiment import load_all_edges, build_neighbor_sets, hub_notes, score_all
from recency_prior_experiment import wikilink_ground_truth

# Index paths come from the environment, so no machine layout is baked in here.
BRAIN_DB = Path(os.environ.get("BRAIN_DB", ".obsidian/pkm_index.db"))
OTHER_DB = Path(os.environ["OTHER_DB"]) if os.environ.get("OTHER_DB") else None
DAEMON = "http://127.0.0.1:44771"


def fetch_similar(vault: str, note: str, fusion: bool, limit: int = 15):
    params = {"note": note, "vault": vault, "limit": limit}
    if fusion:
        params["fusion"] = 1
    url = f"{DAEMON}/similar?{urlencode(params)}"
    try:
        with urllib.request.urlopen(url, timeout=30) as r:
            body = json.load(r)
    except Exception as e:
        print(f"  ERROR {url}: {e}", file=sys.stderr)
        return []
    return [row["path"] for row in body.get("results", [])]


def fusion_promoted(vault: str, anchors: list[str], limit=15, min_jump=4):
    """For each anchor, find candidates ranked much higher under &fusion=1 than
    plain vector, or present in fusion top-N but absent from vector top-N."""
    out = []
    for anchor in anchors:
        vec = fetch_similar(vault, anchor, fusion=False, limit=limit)
        fus = fetch_similar(vault, anchor, fusion=True, limit=limit)
        vec_rank = {p: i for i, p in enumerate(vec)}
        for i, cand in enumerate(fus):
            vrank = vec_rank.get(cand, limit + 5)  # absent -> just outside window
            jump = vrank - i
            if jump >= min_jump:
                out.append((anchor, cand, i, vrank, jump))
    out.sort(key=lambda x: -x[4])
    return out


def hub_target_pairs(db_path: Path, hub_degree=20, n=8):
    edges = load_all_edges(db_path)
    neighbors = build_neighbor_sets(edges, direction="both")
    hubs = hub_notes(neighbors, hub_degree)
    pairs = []
    for a, b in edges:
        if b in hubs and a not in hubs:
            pairs.append((a, b, len(neighbors[b])))
        elif a in hubs and b not in hubs:
            pairs.append((b, a, len(neighbors[a])))
    pairs.sort(key=lambda x: -x[2])
    # dedup by source note
    seen = set()
    result = []
    for a, b, deg in pairs:
        if a in seen:
            continue
        seen.add(a)
        result.append((a, b, deg))
        if len(result) >= n:
            break
    return result, hubs


def aa_disagrees(db_path: Path, n=8, hub_degree=20):
    edges = load_all_edges(db_path)
    neighbors = build_neighbor_sets(edges, direction="both")
    hubs = hub_notes(neighbors, hub_degree)
    linked = set()
    for a, b in edges:
        linked.add((a, b))
        linked.add((b, a))
    paths = sorted(neighbors.keys())
    # sample anchors with decent degree, not hubs
    anchors = [p for p in paths if 2 <= len(neighbors[p]) <= 15 and p not in hubs]
    import random
    random.seed(0)
    random.shuffle(anchors)
    found = []
    for anchor in anchors[:60]:
        scores = score_all(neighbors, paths, anchor, "aa")
        ranked = sorted(zip(paths, scores), key=lambda x: -x[1])
        for cand, score in ranked[:3]:
            if score <= 0 or cand == anchor:
                continue
            if (anchor, cand) in linked:
                continue
            found.append((anchor, cand, score))
        if len(found) >= n * 3:
            break
    found.sort(key=lambda x: -x[2])
    return found[:n]


def plain_wikilink_sample(db_path: Path, n=6, seed=0):
    pairs = wikilink_ground_truth(db_path)
    import random
    random.seed(seed)
    random.shuffle(pairs)
    return pairs[:n]


def main():
    vault = sys.argv[1] if len(sys.argv) > 1 else "brain"
    db = BRAIN_DB if vault == "brain" else OTHER_DB
    if db is None:
        sys.exit("set OTHER_DB to the index path of the vault named %r" % vault)
    mode = sys.argv[2] if len(sys.argv) > 2 else "all"

    if mode in ("all", "hub"):
        print(f"\n=== {vault}: hub-target pairs ===")
        pairs, hubs = hub_target_pairs(db)
        print(f"{len(hubs)} hub notes (degree>20)")
        for a, b, deg in pairs:
            print(f"  {a}  ->  {b}  (hub degree {deg})")

    if mode in ("all", "aa"):
        print(f"\n=== {vault}: AA-disagrees-with-wikilinks candidates ===")
        for a, b, score in aa_disagrees(db):
            print(f"  {a}  ~~  {b}  (AA={score:.3f}, no wikilink)")

    if mode in ("all", "wiki"):
        print(f"\n=== {vault}: plain wikilink baseline sample ===")
        for a, b in plain_wikilink_sample(db):
            print(f"  {a}  ->  {b}")

    if mode == "fusion":
        anchors = sys.argv[3:]
        print(f"\n=== {vault}: fusion-promoted, anchors={anchors} ===")
        for anchor, cand, frank, vrank, jump in fusion_promoted(vault, anchors):
            print(f"  anchor={anchor}\n    candidate={cand}  fusion_rank={frank} vector_rank={vrank} jump={jump}")


if __name__ == "__main__":
    main()
