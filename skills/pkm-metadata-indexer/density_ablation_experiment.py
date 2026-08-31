"""Test whether the wikilink graph's DENSITY, not vault "type," explains why
shared_neighbor_experiment.py's Adamic-Adar/Jaccard verdict flips sign between
this vault (rejected, -8.24% fused) and obsidian-help (validated, +19.61%
fused) - see the "generalization check" and "why the Adamic-Adar verdict
flipped" sections of `2026-08-31 other candidate relatedness signals for
search reranking.md`.

Common-neighbor link-prediction methods (Adamic-Adar among them) are
documented as density-sensitive in the link-prediction literature: a 2025
arXiv paper on graph density and link prediction, and a 2025 Springer study
using Facebook network data, both report common-neighbor methods performing
well on dense graphs (lots of shared neighbors to find) and poorly on sparse
ones. This vault's wikilink graph and obsidian-help's differ in average
degree and, more sharply, in average clustering coefficient - this script
measures both directly rather than asserting "dense vs sparse" by vault type,
then ABLATES it: randomly remove edges from the denser graph until its
average degree matches the sparser vault's, and rerun the exact same AA
standalone/fused test on the sparsified graph. If AA's result reverts toward
negative once density is matched, density is real causal evidence, not a
vault-type confound. If it stays strongly positive, density is not the (whole)
explanation.

Reuses shared_neighbor_experiment.py's build_neighbor_sets/score_all/
run_experiment/run_fusion by MONKEYPATCHING its load_all_edges (a name looked
up in that module's globals at call time, so replacing it there is enough) to
serve a synthetic, sparsified edge list instead of a fresh SQL read - no
reimplementation of the scoring or evaluation logic.

    python skills/pkm-metadata-indexer/density_ablation_experiment.py --density-report \
        --vault-dir <brain vault> --other-db <obsidian-help clone>/.pkm_index.db

    python skills/pkm-metadata-indexer/density_ablation_experiment.py --ablate \
        --vault-dir <obsidian-help clone> --target-avg-degree 4.871 --seeds 0 1 2
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
import index_pkm_meta as pkm
import shared_neighbor_experiment as sne


def graph_density_stats(neighbors: dict[str, set[str]]) -> dict:
    """Node/edge counts, average degree, and average clustering coefficient
    (fraction of possible edges between a node's neighbours that actually
    exist, averaged over nodes with degree >= 2 - undefined below that). The
    2025 arXiv paper on graph density and link prediction recommends
    clustering coefficient specifically because "dense vs sparse" otherwise
    has no standard threshold; average degree alone can look similar between
    two graphs whose local neighbourhoods are shaped very differently.
    """
    nodes = list(neighbors)
    n = len(nodes)
    edge_count = sum(len(v) for v in neighbors.values()) // 2  # symmetric, so halve
    avg_degree = (2 * edge_count / n) if n else 0.0

    coeffs = []
    for node in nodes:
        ns = neighbors[node]
        k = len(ns)
        if k < 2:
            continue
        ns_list = list(ns)
        links = 0
        for i in range(len(ns_list)):
            ni_neighbors = neighbors.get(ns_list[i], ())
            for j in range(i + 1, len(ns_list)):
                if ns_list[j] in ni_neighbors:
                    links += 1
        possible = k * (k - 1) / 2
        coeffs.append(links / possible)

    return {
        "nodes": n,
        "edges": edge_count,
        "avg_degree": round(avg_degree, 4),
        "nodes_with_degree_ge2": len(coeffs),
        "avg_clustering_coefficient": round(float(np.mean(coeffs)), 4) if coeffs else None,
    }


def density_report(db_path: Path, label: str) -> dict:
    edges = sne.load_all_edges(db_path)
    neighbors = sne.build_neighbor_sets(edges)
    stats = graph_density_stats(neighbors)
    stats["label"] = label
    stats["db"] = str(db_path)
    return stats


def sparsify_edges(edges: list[tuple[str, str]], keep_fraction: float, seed: int) -> list[tuple[str, str]]:
    """Uniformly-at-random remove edges (not nodes) until `keep_fraction` remain.

    Uniform-at-random removal, not degree-targeted removal, is the honest
    ablation: it changes density without hand-picking which structure survives,
    so a reverted result can't be blamed on "which edges you chose to keep."
    """
    rng = np.random.default_rng(seed)
    edges = list(edges)
    n_keep = round(len(edges) * keep_fraction)
    n_keep = max(0, min(len(edges), n_keep))
    keep_idx = rng.choice(len(edges), size=n_keep, replace=False)
    return [edges[i] for i in sorted(keep_idx)]


def run_with_edges(vault_dir: Path, db_path: Path, edges: list[tuple[str, str]], **kwargs) -> dict:
    """Run shared_neighbor_experiment.run_experiment against a substituted edge
    list instead of a fresh SQL read, by monkeypatching load_all_edges for the
    duration of the call. run_experiment still reads vectors and wikilink
    ground truth from `db_path` normally - only the wikilink GRAPH used for
    AA/Jaccard scoring is swapped."""
    original = sne.load_all_edges
    sne.load_all_edges = lambda _db_path: edges
    try:
        return sne.run_experiment(vault_dir, db_path, **kwargs)
    finally:
        sne.load_all_edges = original


def find_keep_fraction_for_target_degree(edges: list[tuple[str, str]], neighbors_full: dict,
                                         target_avg_degree: float) -> float:
    """Removing edges uniformly at random also shrinks the node count (an
    isolated node drops out of the neighbour-set graph entirely), so
    avg_degree = 2E/N is not linear in keep_fraction. Binary-search the
    fraction instead of solving it in closed form."""
    lo, hi = 0.0, 1.0
    for _ in range(30):
        mid = (lo + hi) / 2
        rng = np.random.default_rng(0)  # search itself is deterministic; only used to size the fraction
        n_keep = round(len(edges) * mid)
        idx = rng.choice(len(edges), size=n_keep, replace=False) if n_keep else np.array([], dtype=int)
        kept = [edges[i] for i in idx]
        nb = sne.build_neighbor_sets(kept)
        n = len(nb)
        e = sum(len(v) for v in nb.values()) // 2
        deg = (2 * e / n) if n else 0.0
        if deg > target_avg_degree:
            hi = mid
        else:
            lo = mid
    return (lo + hi) / 2


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--vault-dir", help="required unless --self-check")
    parser.add_argument("--db", default=None, help="defaults to <vault>/.obsidian/pkm_index.db")
    parser.add_argument("--density-report", action="store_true",
                        help="Print node/edge/avg-degree/clustering-coefficient for --vault-dir "
                             "(and --other-db if given) and exit; no ablation.")
    parser.add_argument("--other-db", default=None, help="A second index to report density for, side by side")
    parser.add_argument("--ablate", action="store_true",
                        help="Sparsify --vault-dir's wikilink graph to --target-avg-degree and "
                             "rerun the standalone+fused AA test, once per --seeds value")
    parser.add_argument("--target-avg-degree", type=float, default=4.871)
    parser.add_argument("--seeds", type=int, nargs="+", default=[0, 1, 2])
    parser.add_argument("--sample", type=int, default=1000)
    parser.add_argument("--fuse-rrf-k", type=float, default=5.0,
                        help="fusion RRF k to test at (5 = the docs-vault's own reported peak k)")
    parser.add_argument("--self-check", action="store_true")
    args = parser.parse_args()
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    if args.self_check:
        return self_check()
    if not args.vault_dir:
        parser.error("--vault-dir is required unless --self-check")

    vault_dir = Path(args.vault_dir).resolve()
    db_path = Path(args.db).resolve() if args.db else pkm.default_db_path(vault_dir)

    import json

    if args.density_report:
        out = [density_report(db_path, "vault-dir")]
        if args.other_db:
            out.append(density_report(Path(args.other_db).resolve(), "other-db"))
        print(json.dumps(out, indent=1))
        return

    if args.ablate:
        edges = sne.load_all_edges(db_path)
        neighbors_full = sne.build_neighbor_sets(edges)
        full_stats = graph_density_stats(neighbors_full)
        keep_fraction = find_keep_fraction_for_target_degree(edges, neighbors_full, args.target_avg_degree)

        results = {"full_graph": full_stats, "target_avg_degree": args.target_avg_degree,
                   "keep_fraction": round(keep_fraction, 4), "runs": []}
        for seed in args.seeds:
            sparse_edges = sparsify_edges(edges, keep_fraction, seed)
            sparse_neighbors = sne.build_neighbor_sets(sparse_edges)
            sparse_stats = graph_density_stats(sparse_neighbors)

            standalone = run_with_edges(vault_dir, db_path, sparse_edges,
                                        sample=args.sample, seed=seed)
            fused = run_with_edges(vault_dir, db_path, sparse_edges,
                                   sample=args.sample, seed=seed,
                                   fuse_rrf_k=args.fuse_rrf_k, fuse_metric="aa")
            results["runs"].append({
                "seed": seed,
                "fraction_removed": round(1 - len(sparse_edges) / len(edges), 4),
                "sparsified_graph": sparse_stats,
                "standalone_aa": standalone.get("aa"),
                "fused_aa_mrr_change_pct": fused.get("mrr_change_pct"),
                "fused_aa_full": fused,
            })
        print(json.dumps(results, indent=1))
        return

    parser.error("pass --density-report or --ablate")


def self_check():
    # A 4-cycle a-b-c-d-a: every node has degree 2, no neighbour pair among a
    # node's own neighbours is itself linked, so clustering coefficient is 0.
    edges = [("a", "b"), ("b", "c"), ("c", "d"), ("d", "a")]
    neighbors = sne.build_neighbor_sets(edges)
    stats = graph_density_stats(neighbors)
    assert stats["nodes"] == 4 and stats["edges"] == 4
    assert abs(stats["avg_degree"] - 2.0) < 1e-9
    assert stats["avg_clustering_coefficient"] == 0.0

    # A triangle a-b-c plus a pendant d-a: a has degree 3 (b, c, d), and b/c
    # (a's neighbours) ARE linked to each other, so a's own coefficient is
    # 1/3 (1 of the 3 possible pairs among {b,c,d} exists); b and c have
    # degree 2 each with their only neighbour-pair (a and the other) linked,
    # coefficient 1.0 each; d has degree 1, excluded.
    edges2 = [("a", "b"), ("b", "c"), ("c", "a"), ("a", "d")]
    neighbors2 = sne.build_neighbor_sets(edges2)
    stats2 = graph_density_stats(neighbors2)
    assert stats2["nodes_with_degree_ge2"] == 3  # a, b, c (d has degree 1)
    assert abs(stats2["avg_clustering_coefficient"] - (1 / 3 + 1.0 + 1.0) / 3) < 1e-3  # rounded to 4dp in output

    # sparsify_edges keeps exactly the requested count, deterministically per seed
    many_edges = [(f"n{i}", f"n{i+1}") for i in range(100)]
    kept = sparsify_edges(many_edges, 0.3, seed=0)
    assert len(kept) == 30
    kept_again = sparsify_edges(many_edges, 0.3, seed=0)
    assert kept == kept_again, "same seed must reproduce the same kept edge set"
    kept_other_seed = sparsify_edges(many_edges, 0.3, seed=1)
    assert kept != kept_other_seed, "different seeds should (almost certainly) differ"

    print("self-check ok")


if __name__ == "__main__":
    main()
