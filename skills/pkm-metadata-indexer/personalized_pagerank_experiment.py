"""Test Personalized PageRank / Random Walk with Restart (PPR/RWR) against real
wikilinks, and measure overlap with vector similarity - the last untested
candidate named in the "wider prior art" section of `2026-08-31 other
candidate relatedness signals for search reranking.md`.

Adamic-Adar/Jaccard (shared_neighbor_experiment.py) only sees candidates that
share at least one 1-hop neighbour with the anchor - a pair with zero shared
neighbours scores exactly 0, which the density-ablation section of that note
found is exactly why AA fails on sparse wikilink graphs (this vault avg
degree 4.87, kepano/bramses ~2.1: both reject AA hard). PPR/RWR is built for
that case specifically: a random walker seeded at the anchor, restarting at
the anchor with probability `alpha` each step, assigns SOME visit probability
to every node reachable by any path, however long, not just 1-hop neighbours.

    pi = alpha * e_seed + (1 - alpha) * P^T @ pi

P is the row-stochastic transition matrix over the undirected wikilink graph
(P[i,j] = 1/degree(i) for each edge i-j); pi is the stationary visit-
probability vector, found by power iteration. alpha=0.15 is the common
default in the PageRank/PPR literature (Brin & Page's own damping factor is
1-0.85=0.15 restart-equivalent).

LEAVE-ONE-OUT IS NOT OPTIONAL HERE, unlike every other experiment in this
folder. `wikilink_ground_truth()` and `load_all_edges()` run the IDENTICAL
SQL query - the (source, target) pair being scored is itself an edge in the
very graph PPR walks on. Adamic-Adar's formula never directly credits a
1-hop edge (it only sums shared SECOND-order neighbours), so the same
duplication is harmless there. PPR's first power-iteration step sends a
walker at the anchor directly to every 1-hop neighbour with probability
1/degree(anchor) - if the target is already a direct wikilink, that alone
makes it one of the biggest scores in the whole graph, before the walk has
done anything path-related at all. An early, uncorrected run of this exact
script got standalone MRR +124% that way - not a real relatedness signal,
just PPR rediscovering a link already visible in the note's own text. Every
scored pair here therefore has its own (source, target) edge removed from
the graph before the walk runs, so the only way PPR can find the target is
via some OTHER, longer path - the actual question this experiment exists to
answer, matching AA's own standalone framing ("not a fair comparison to
vector-only ranking, the overlap number and the ability to reach a
zero-shared-neighbour target are what matter").

Same evaluation as shared_neighbor_experiment.py otherwise: explicit
[[wikilinks]] as ground truth, standalone MRR vs a vector-only baseline,
RRF-fusion swept over k, and a standalone overlap-with-vector-neighbours
check - reuses that script's load_all_edges/build_neighbor_sets/hub_notes/
rrf_fuse_scores and recency_prior_experiment's rank_of/wikilink_ground_truth/
note_vectors rather than redefining any of them.

    python skills/pkm-metadata-indexer/personalized_pagerank_experiment.py --vault-dir <vault> --sample 500
    python skills/pkm-metadata-indexer/personalized_pagerank_experiment.py --vault-dir <vault> --fuse-rrf-k 5
    python skills/pkm-metadata-indexer/personalized_pagerank_experiment.py --vault-dir <vault> --include-direct-edge  # the leaky, for-comparison-only mode
"""

from __future__ import annotations

import argparse
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
import scipy.sparse as sp
import index_pkm_meta as pkm
import shared_neighbor_experiment as sne
from recency_prior_experiment import rank_of, wikilink_ground_truth, note_vectors

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def edge_index_arrays(neighbors: dict[str, set[str]], paths: list[str]) -> tuple[np.ndarray, np.ndarray, dict]:
    """Directed (both-ways) edge index arrays over `paths`, built ONCE per
    graph and reused by every leave-one-out rebuild via boolean masking -
    avoids re-walking a Python adjacency dict per evaluated pair, which
    leave-one-out otherwise needs one of (a fresh graph per pair) instead of
    shared_neighbor_experiment.py's "build the structure once, reuse for
    every anchor" shape.

    # ponytail: scipy is already installed in this environment (used nowhere
    # else in this folder yet) and up to --sample pairs each need their OWN
    # transition matrix (the excluded edge differs per pair), so a vectorized
    # numpy boolean-mask rebuild (microseconds) beats re-walking a Python
    # dict per pair by orders of magnitude at the scale tested tonight
    # (52-3,039 nodes, 100-7,401 edges across 4 vaults).
    """
    index_of = {p: i for i, p in enumerate(paths)}
    row, col = [], []
    for i, path in enumerate(paths):
        for other in neighbors.get(path, ()):
            j = index_of.get(other)
            if j is not None:
                row.append(i)
                col.append(j)
    return np.array(row, dtype=np.intp), np.array(col, dtype=np.intp), index_of


def transition_from_edges(row: np.ndarray, col: np.ndarray, n: int,
                          exclude: tuple[int, int] | None = None) -> sp.csr_matrix:
    """Row-stochastic transition matrix's TRANSPOSE (P^T, csr), built from
    directed edge-index arrays, optionally excluding one undirected edge
    (`exclude=(i, j)`) - the leave-one-out case that forces PPR to find a
    wikilinked target via a path other than the direct link itself. Degree is
    recomputed from whatever edges remain, so removing a node's only edge
    correctly leaves it a dangling (all-zero out-degree) node rather than
    dividing by zero."""
    if exclude is not None:
        i, j = exclude
        keep = ~(((row == i) & (col == j)) | ((row == j) & (col == i)))
        row, col = row[keep], col[keep]
    degree = np.bincount(row, minlength=n)
    weight = 1.0 / degree[row]
    # Building at (col, row) directly yields P^T: entry [col, row] = P[row, col] = weight.
    return sp.csr_matrix((weight, (col, row)), shape=(n, n))


def personalized_pagerank(transition_t: sp.csr_matrix, seed_index: int, n: int,
                          alpha: float = 0.15, max_iter: int = 100,
                          tol: float = 1e-10) -> np.ndarray:
    """Power-iteration PPR/RWR stationary visit-probability vector seeded at
    `seed_index`: pi = alpha*e_seed + (1-alpha)*P^T @ pi, iterated to
    convergence (or `max_iter`, whichever comes first - (1-alpha)^max_iter is
    already ~1e-8 at the default alpha=0.15/max_iter=100, so this virtually
    always converges on `tol` first)."""
    e = np.zeros(n, dtype=np.float64)
    e[seed_index] = 1.0
    v = e.copy()
    for _ in range(max_iter):
        v_new = alpha * e + (1 - alpha) * (transition_t @ v)
        if np.abs(v_new - v).sum() < tol:
            v = v_new
            break
        v = v_new
    return v


def ppr_for_pair(row: np.ndarray, col: np.ndarray, n: int, seed_index: int,
                 target_index: int, alpha: float, max_iter: int, tol: float,
                 leave_one_out: bool) -> np.ndarray:
    """PPR vector seeded at `seed_index`, with the (seed, target) edge removed
    first unless `leave_one_out` is False - see the module docstring for why
    this is the default rather than an opt-in flag."""
    exclude = (seed_index, target_index) if leave_one_out else None
    transition_t = transition_from_edges(row, col, n, exclude=exclude)
    return personalized_pagerank(transition_t, seed_index, n, alpha, max_iter, tol)


def run_fusion(usable, vec_paths, vec_index_of, pooled, row, col, n_graph, graph_paths,
              path_in_graph_index, k: float, alpha: float, max_iter: int, tol: float,
              leave_one_out: bool) -> dict:
    """RRF-fuse PPR's rank list with the vector-rank list - the fair test of
    whether adding this signal to vector search improves on vector search
    alone, same methodology as shared_neighbor_experiment.py's run_fusion."""
    candidates = sorted(set(vec_paths) | set(graph_paths))
    cand_index = {p: i for i, p in enumerate(candidates)}
    vec_to_cand = np.array([cand_index.get(p, -1) for p in vec_paths])
    graph_to_cand = np.array([cand_index.get(p, -1) for p in graph_paths])

    baseline_ranks, fused_ranks = [], []
    for source, target in usable:
        if source not in path_in_graph_index or target not in path_in_graph_index:
            continue
        anchor_v_index, target_v_index = vec_index_of[source], vec_index_of[target]
        vector_scores = pooled @ pooled[anchor_v_index]
        baseline_rank = rank_of(vector_scores, vec_index_of, anchor_v_index, target_v_index)
        if baseline_rank is None:
            continue

        src_g, tgt_g = path_in_graph_index[source], path_in_graph_index[target]
        graph_scores = ppr_for_pair(row, col, n_graph, src_g, tgt_g, alpha, max_iter, tol, leave_one_out)

        v_full = np.full(len(candidates), -1.0, dtype=np.float64)
        v_full[vec_to_cand] = vector_scores
        g_full = np.zeros(len(candidates), dtype=np.float64)
        g_full[graph_to_cand] = graph_scores

        fused = sne.rrf_fuse_scores(v_full, g_full, k)
        anchor_c_index, target_c_index = cand_index[source], cand_index[target]
        fused_rank = rank_of(fused, cand_index, anchor_c_index, target_c_index)
        if fused_rank is None:
            continue
        baseline_ranks.append(baseline_rank)
        fused_ranks.append(fused_rank)

    n = len(baseline_ranks)
    if n == 0:
        return {"error": "no usable pairs"}
    mrr_baseline = float(np.mean([1 / r for r in baseline_ranks]))
    mrr_fused = float(np.mean([1 / r for r in fused_ranks]))
    improved = sum(1 for b, r in zip(baseline_ranks, fused_ranks) if r < b)
    worsened = sum(1 for b, r in zip(baseline_ranks, fused_ranks) if r > b)
    return {
        "metric": "ppr", "rrf_k": k, "alpha": alpha, "leave_one_out": leave_one_out, "pairs": n,
        "improved": improved, "worsened": worsened, "unchanged": n - improved - worsened,
        "mean_rank_baseline": round(float(np.mean(baseline_ranks)), 2),
        "mean_rank_fused": round(float(np.mean(fused_ranks)), 2),
        "mrr_baseline": round(mrr_baseline, 4),
        "mrr_fused": round(mrr_fused, 4),
        "mrr_change_pct": round((mrr_fused / mrr_baseline - 1) * 100, 2) if mrr_baseline else None,
    }


def run_experiment(vault_dir: Path, db_path: Path, sample: int, seed: int,
                   alpha: float = 0.15, fuse_rrf_k: float | None = None,
                   exclude_hubs: bool = False, hub_degree: int = 20,
                   max_iter: int = 100, tol: float = 1e-10,
                   leave_one_out: bool = True) -> dict:
    """Standalone mode (fuse_rrf_k=None): how well PPR alone ranks the true
    target, and how much its top neighbours overlap with vector's - same
    "not a fair standalone comparison, the overlap number is what matters"
    caveat as shared_neighbor_experiment.py's own standalone mode.

    Fusion mode (fuse_rrf_k set): RRF-fuse PPR's rank list with vector rank.

    `leave_one_out=True` (default) removes each pair's own (source, target)
    edge before scoring that pair - see the module docstring for why this is
    not optional the way it would be for AA.
    """
    connection = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        meta, matrix = pkm.load_vectors(connection.cursor())
    finally:
        connection.close()
    if matrix is None:
        return {"error": "no vectors in this index"}
    vec_paths, vec_index_of, pooled = note_vectors(meta, matrix)

    edges = sne.load_all_edges(db_path)
    neighbors = sne.build_neighbor_sets(edges)
    graph_paths = sorted(neighbors)  # every note that appears in the link graph at all
    hubs_excluded = 0
    if exclude_hubs:
        hubs = sne.hub_notes(neighbors, hub_degree)
        graph_paths = [p for p in graph_paths if p not in hubs]
        hubs_excluded = len(hubs)
    path_in_graph_index = {p: i for i, p in enumerate(graph_paths)}
    row, col, _ = edge_index_arrays(neighbors, graph_paths)
    n_graph = len(graph_paths)

    links = wikilink_ground_truth(db_path)
    usable = [(a, b) for a, b in links
             if a in vec_index_of and b in vec_index_of and a in path_in_graph_index]
    rng = np.random.default_rng(seed)
    if len(usable) > sample:
        usable = [usable[i] for i in rng.choice(len(usable), size=sample, replace=False)]

    if fuse_rrf_k is not None:
        result = run_fusion(usable, vec_paths, vec_index_of, pooled, row, col, n_graph, graph_paths,
                            path_in_graph_index, fuse_rrf_k, alpha, max_iter, tol, leave_one_out)
        if exclude_hubs:
            result["hubs_excluded"] = hubs_excluded
            result["hub_degree"] = hub_degree
        return result

    ranks, baseline = [], []
    vector_neighbor_sets, ppr_neighbor_sets = {}, {}
    for source, target in usable:
        anchor_v_index, target_v_index = vec_index_of[source], vec_index_of[target]
        vector_scores = pooled @ pooled[anchor_v_index]
        baseline_rank = rank_of(vector_scores, vec_index_of, anchor_v_index, target_v_index)
        if baseline_rank is None:
            continue
        top_vector = set(np.array(vec_paths)[np.argsort(-vector_scores)[:11]]) - {source}
        vector_neighbor_sets[source] = top_vector

        if source not in path_in_graph_index or target not in path_in_graph_index:
            continue
        anchor_g_index, target_g_index = path_in_graph_index[source], path_in_graph_index[target]
        scores = ppr_for_pair(row, col, n_graph, anchor_g_index, target_g_index,
                              alpha, max_iter, tol, leave_one_out)
        rank = rank_of(scores, path_in_graph_index, anchor_g_index, target_g_index)
        if rank is not None:
            ranks.append(rank)
            baseline.append(baseline_rank)
        top_ppr = set(np.array(graph_paths)[np.argsort(-scores)[:11]]) - {source}
        ppr_neighbor_sets[source] = top_ppr

    overlaps = [
        len(vector_neighbor_sets[a] & ppr_neighbor_sets[a]) / max(1, len(ppr_neighbor_sets[a]))
        for a in ppr_neighbor_sets if ppr_neighbor_sets[a]
    ]
    out = {"pairs_sampled": len(usable), "alpha": alpha, "leave_one_out": leave_one_out,
           "mean_vector_ppr_overlap_pct":
           round(100 * float(np.mean(overlaps)), 1) if overlaps else None}
    if exclude_hubs:
        out["hubs_excluded"] = hubs_excluded
        out["hub_degree"] = hub_degree
    if not ranks:
        out["ppr"] = {"error": "no usable pairs"}
        return out
    mrr = float(np.mean([1 / r for r in ranks]))
    mrr_baseline = float(np.mean([1 / r for r in baseline]))
    out["ppr"] = {
        "pairs": len(ranks),
        "mean_rank": round(float(np.mean(ranks)), 2),
        "mrr": round(mrr, 4),
        "mrr_vs_vector_baseline_pct": round((mrr / mrr_baseline - 1) * 100, 2) if mrr_baseline else None,
    }
    return out


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--vault-dir", help="required unless --self-check")
    parser.add_argument("--db", default=None, help="defaults to <vault>/.obsidian/pkm_index.db")
    parser.add_argument("--sample", type=int, default=500)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--alpha", type=float, default=0.15,
                        help="restart probability - the common PPR/PageRank default")
    parser.add_argument("--fuse-rrf-k", type=float, default=None,
                        help="RRF-fuse PPR with vector rank at this k, instead of the "
                             "standalone PPR-vs-vector report")
    parser.add_argument("--exclude-hubs", action="store_true",
                        help="Drop notes with more wikilink neighbours than --hub-degree from "
                             "the candidate pool, mirroring shared_neighbor_experiment.py's own "
                             "hub exclusion")
    parser.add_argument("--hub-degree", type=int, default=20,
                        help="A note with more wikilink neighbours than this counts as a hub")
    parser.add_argument("--include-direct-edge", action="store_true",
                        help="Score with the (source, target) edge left IN the graph - the leaky, "
                             "inflated mode kept only to document why leave-one-out is the default; "
                             "see the module docstring")
    parser.add_argument("--max-iter", type=int, default=100)
    parser.add_argument("--tol", type=float, default=1e-10)
    parser.add_argument("--self-check", action="store_true")
    args = parser.parse_args()

    if args.self_check:
        return self_check()
    if not args.vault_dir:
        parser.error("--vault-dir is required unless --self-check")

    vault_dir = Path(args.vault_dir).resolve()
    db_path = Path(args.db).resolve() if args.db else pkm.default_db_path(vault_dir)
    import json
    result = run_experiment(vault_dir, db_path, args.sample, args.seed, args.alpha,
                            args.fuse_rrf_k, args.exclude_hubs, args.hub_degree,
                            args.max_iter, args.tol, leave_one_out=not args.include_direct_edge)
    print(json.dumps(result, indent=1))


def self_check():
    # Path graph a-b-c-d-e, seeded at a. PPR mass should decay MONOTONICALLY
    # with hop distance from the seed - the property a random walk with
    # restart is built to have, and the thing worth actually asserting since
    # "some nonzero score everywhere" alone would also be true of noise.
    edges = [("a", "b"), ("b", "c"), ("c", "d"), ("d", "e")]
    neighbors = sne.build_neighbor_sets(edges)
    paths = ["a", "b", "c", "d", "e"]
    row, col, index_of = edge_index_arrays(neighbors, paths)
    n = len(paths)
    transition_t = transition_from_edges(row, col, n)
    pi = personalized_pagerank(transition_t, index_of["a"], n, alpha=0.15)
    assert pi[index_of["b"]] > pi[index_of["c"]] > pi[index_of["d"]] > pi[index_of["e"]], \
        "PPR mass must decay monotonically with hop distance from the seed"

    # The exact case Adamic-Adar cannot handle: a and d share ZERO 1-hop
    # neighbours (N(a)={b}, N(d)={c,e}, no overlap) - AA(a,d) is exactly 0 by
    # construction. PPR must still assign d a nonzero score via the a-b-c-d
    # path, which is the entire point of testing PPR as an AA alternative.
    aa_scores = sne.score_all(neighbors, paths, "a", "aa")
    assert aa_scores[index_of["d"]] == 0.0, "sanity: AA really does score this pair 0"
    assert pi[index_of["d"]] > 0.0, "PPR must reach a 2+-hop node AA scores as zero"

    # Stationary distribution over a graph with no dangling nodes sums to 1:
    # pi = alpha*e + (1-alpha)*P^T@pi, and P is row-stochastic, so at the
    # fixed point sum(pi) = alpha + (1-alpha)*sum(pi) => sum(pi) = 1.
    assert abs(float(pi.sum()) - 1.0) < 1e-6

    # Higher alpha (more frequent restart) must concentrate mass CLOSER to the
    # seed - the walk has less chance to wander before teleporting home, so a
    # far node's share should shrink as alpha rises.
    pi_low_alpha = personalized_pagerank(transition_t, index_of["a"], n, alpha=0.05)
    pi_high_alpha = personalized_pagerank(transition_t, index_of["a"], n, alpha=0.5)
    assert pi_high_alpha[index_of["e"]] < pi_low_alpha[index_of["e"]], \
        "a higher restart probability should reach the farthest node less, not more"

    # transition_from_edges is row-stochastic: every row (of P, i.e. every
    # COLUMN of P^T) with out-edges sums to 1.
    row_sums = np.asarray(transition_t.transpose().sum(axis=1)).ravel()
    for i, path in enumerate(paths):
        if neighbors.get(path):
            assert abs(row_sums[i] - 1.0) < 1e-9, f"row for {path} must sum to 1"

    # Leave-one-out: a direct edge a-d PLUS an alternate longer path a-b-c-d.
    # Excluding the direct edge must not zero out d's score (reachable via
    # the alternate path) but must lower it relative to keeping the direct
    # edge in - the exact mechanism the real experiment's default relies on
    # to avoid rediscovering the ground-truth edge itself.
    edges_loo = [("a", "d"), ("a", "b"), ("b", "c"), ("c", "d")]
    neighbors_loo = sne.build_neighbor_sets(edges_loo)
    paths_loo = ["a", "b", "c", "d"]
    row_l, col_l, idx_l = edge_index_arrays(neighbors_loo, paths_loo)
    n_l = len(paths_loo)
    t_full = transition_from_edges(row_l, col_l, n_l)
    pi_full = personalized_pagerank(t_full, idx_l["a"], n_l, alpha=0.15)
    t_loo = transition_from_edges(row_l, col_l, n_l, exclude=(idx_l["a"], idx_l["d"]))
    pi_loo = personalized_pagerank(t_loo, idx_l["a"], n_l, alpha=0.15)
    assert pi_loo[idx_l["d"]] > 0.0, \
        "removing the direct edge must not zero out a node reachable by another path"
    assert pi_loo[idx_l["d"]] < pi_full[idx_l["d"]], \
        "removing the direct edge must lower d's score vs leaving it in"

    print("self-check ok")


if __name__ == "__main__":
    main()
