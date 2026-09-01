"""Test shared-neighbor graph similarity (Adamic-Adar, Jaccard) against real
wikilinks, and measure overlap with vector similarity and co-commit.

Two notes that don't link to each other, but both link to (or are linked from)
the same third notes, are "co-cited" in the bibliographic-coupling sense —
mature link-prediction research (Liben-Nowell & Kleinberg, 2003/2007) on real
networks found Adamic-Adar beats plain Jaccard/common-neighbors because it
downweights shared neighbors that have high degree: a hub or MOC-style note
that links to everything contributes almost nothing to the Adamic-Adar score,
but would inflate a plain Jaccard count just as much as a genuinely narrow,
specific shared neighbor would.

    AdamicAdar(a, b) = sum over z in N(a) & N(b) of 1 / log(degree(z))
    Jaccard(a, b)    = |N(a) & N(b)| / |N(a) | N(b)|

N(x) is the undirected neighbor set: every note x links to, plus every note
that links to x. degree(z) = |N(z)|.

--direction splits that merge apart. Citation-analysis research has long
treated "shared outbound" and "shared inbound" as two distinct signals:
bibliographic coupling (Kessler, 1963) is shared OUTBOUND references between
two documents, co-citation (Small, 1973) is shared INBOUND references (both
cited by some later third document). --direction out builds N(x) as only
what x links to (coupling); --direction in builds N(x) as only what links to
x (co-citation); --direction both (default) is the original undirected merge
tested first. AA's log-degree downweighting still applies, but is always
computed against the undirected degree even in directional mode (see the
ponytail note on score_all), rather than a same-direction degree, which
would silently zero out most scores for notes with a low out/in degree in
the direction NOT being scored — not a hub-note bug, just an unrelated
quantity.

Same evaluation as recency_prior_experiment.py: explicit [[wikilinks]] as
ground truth (no LLM judge available), MRR against a vector-only baseline —
reuses that script's rank_of/wikilink_ground_truth/note_vectors rather than
redefining them.

    python skills/pkm-metadata-indexer/shared_neighbor_experiment.py --vault-dir <vault> --sample 500
    python skills/pkm-metadata-indexer/shared_neighbor_experiment.py --vault-dir <vault> --direction out --fuse-rrf-k 60
"""

from __future__ import annotations

import argparse
import math
import sqlite3
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
import index_pkm_meta as pkm
from recency_prior_experiment import rank_of, wikilink_ground_truth, note_vectors, rrf_fuse


def load_all_edges(db_path: Path) -> list[tuple[str, str]]:
    connection = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        return connection.execute(
            "SELECT DISTINCT source_path, resolved_target_path FROM edges "
            "WHERE resolved_target_path IS NOT NULL AND source_path != resolved_target_path"
        ).fetchall()
    finally:
        connection.close()


def build_neighbor_sets(edges: list[tuple[str, str]], direction: str = "both") -> dict[str, set[str]]:
    """direction="both" (default) is the original undirected merge: N(x) = what
    x links to, plus what links to x. direction="out" keeps only what x links
    to (bibliographic coupling, Kessler 1963); direction="in" keeps only what
    links to x (co-citation, Small 1973)."""
    neighbors: dict[str, set[str]] = defaultdict(set)
    for a, b in edges:
        if direction in ("both", "out"):
            neighbors[a].add(b)
        if direction in ("both", "in"):
            neighbors[b].add(a)
    return neighbors


def all_graph_nodes(edges: list[tuple[str, str]]) -> set[str]:
    """Every note touched by an edge, either end, independent of direction -
    the candidate pool for out/in modes needs to include a note with zero
    out-degree (or zero in-degree) too, the same way build_neighbor_sets("both")
    always did implicitly (both endpoints become keys there regardless)."""
    nodes: set[str] = set()
    for a, b in edges:
        nodes.add(a)
        nodes.add(b)
    return nodes


# (avg wikilink-graph degree, AA fusion MRR change at k=1) for the 4 real
# vaults measured so far - see "why the Adamic-Adar verdict flipped" and
# "more test vaults" in 2026-08-31 other candidate relatedness signals for
# search reranking.md. n=4, one positive example: not enough to fit a real
# threshold, only enough to see a rough direction, and bramses scoring less
# negative than kepano despite lower degree shows degree isn't the whole
# story - the vault's own density-ablation experiment already found density
# explains "part of it, not all of it". Treat any recommendation from this
# as a starting point for a human decision, not a threshold to switch on
# automatically.
AA_DEGREE_CALIBRATION = [
    ("bramses", 2.115, -19.82),
    ("kepano", 2.156, -34.91),
    ("this vault (brain)", 4.87, -8.24),
    ("obsidianmd/obsidian-help", 8.32, 15.96),
]


def recommend_aa_weight(avg_degree: float) -> str:
    """Human-readable, non-binding read on whether AA fusion is likely to help
    at this vault's measured wikilink-graph density - not an on/off switch.
    """
    lines = [f"measured average wikilink-graph degree: {avg_degree:.3f}",
             "",
             "calibration points so far (degree -> AA fusion MRR change at k=1):"]
    for name, degree, change in sorted(AA_DEGREE_CALIBRATION, key=lambda row: row[1]):
        lines.append(f"  {degree:5.3f}  {change:+6.2f}%  {name}")
    lines.append("")
    if avg_degree < 4.87:
        lines.append("below every vault that has rejected AA fusion so far (n=2 negative in this "
                      "range) - AA fusion has not helped on any vault this sparse yet.")
    elif avg_degree < 8.32:
        lines.append("between this vault's own rejection point and obsidian-help's validation "
                      "point - no real calibration data in this range, direction only.")
    else:
        lines.append("at or above the one vault where AA fusion validated (n=1) - a plausible "
                      "candidate to try, not a confirmed win.")
    lines.append("")
    lines.append("n=4 total, one positive example: this is a starting point for a human decision "
                 "to try --fuse-metric aa and check the real result, not a rule to automate.")
    return "\n".join(lines)


def hub_notes(neighbors: dict[str, set[str]], degree_threshold: int) -> set[str]:
    """Notes with more than `degree_threshold` distinct wikilink neighbours -
    the wikilink-graph analogue of co_commit.py's hub_notes(), a hard cutoff on
    a note's own raw degree. This is a genuinely different mechanism than
    Adamic-Adar's log-degree downweighting of a *shared* neighbour z: that
    softens z's contribution to a score, this removes a hub note from the
    candidate pool entirely, the same all-or-nothing exclusion co_commit.py
    applies to a hub associated note."""
    return {note for note, ns in neighbors.items() if len(ns) > degree_threshold}


def score_all(neighbors: dict[str, set[str]], paths: list[str], anchor: str,
             metric: str, degree_neighbors: dict[str, set[str]] | None = None,
             z_hub_degree: int | None = None) -> np.ndarray:
    """`neighbors` supplies the anchor/candidate sets being intersected - this
    is what --direction changes. `degree_neighbors` supplies the degree(z) used
    to downweight a shared neighbor z in the AA sum; defaults to `neighbors`
    itself (the original, direction="both" behaviour, unchanged).

    `z_hub_degree`: a hard cutoff on the shared neighbor z itself, AA-only.
    This is a different axis than `hub_notes()`/`--exclude-hubs` below, which
    drops a hub NOTE from the candidate pool (it can't be suggested as a
    related result) but never touches whether that same note can still act as
    the bridging z between two OTHER candidates - two notes with no real
    relationship, but a shared wikilink to a same-day catalog/index note,
    still get a nonzero AA score today no matter how aggressively
    --exclude-hubs is set, because z is read from the unfiltered `neighbors`
    dict regardless. Confirmed on real data: a same-day batch of game-portfolio
    portfolio notes (`game-a.md`, `game-d.md`, ...) whose only wikilinks
    are to a handful of shared same-session overview/catalog notes (degree
    34-77) scores AA(game-a, game-d) = 1.03 even though the two share no
    real topic - `--exclude-hubs` at threshold 20 does nothing for this pair
    since neither endpoint is itself a hub. `z_hub_degree` fixes this by
    zeroing out z's whole term (not just log-downweighting it) once
    degree(z) exceeds the threshold, same 20-default convention as
    `hub_notes()`. Jaccard has no per-z term to cut (it only counts
    `len(shared)`), and Jaccard already lost to AA in every test tonight, so
    this is AA-only rather than a parallel Jaccard change nothing asked for.

    # ponytail: when neighbors is a directional (out/in) set, degree_neighbors
    # is always passed in as the undirected/"both" set by run_experiment rather
    # than the matching directional degree (in-degree for coupling's shared z,
    # out-degree for co-citation's shared z, which is the theoretically exact
    # analogue - a reference cited by many papers is a weak coupling signal
    # regardless of how many papers *it itself* cites). Using the same-direction
    # degree instead would silently zero out most AA scores, since a shared z
    # under "out" is typically a pure link target with 0 out-degree of its own.
    # Upgrade to the cross-direction degree if this variant looks promising
    # enough to refine further.
    """
    if degree_neighbors is None:
        degree_neighbors = neighbors
    anchor_set = neighbors.get(anchor, set())
    scores = np.zeros(len(paths), dtype=np.float64)
    if not anchor_set:
        return scores
    for index, path in enumerate(paths):
        other_set = neighbors.get(path, set())
        shared = anchor_set & other_set
        if not shared:
            continue
        if metric == "aa":
            scores[index] = sum(
                1.0 / math.log(len(degree_neighbors[z])) for z in shared
                if len(degree_neighbors[z]) > 1
                and (z_hub_degree is None or len(degree_neighbors[z]) <= z_hub_degree)
            )
        else:  # jaccard
            union = len(anchor_set | other_set)
            scores[index] = len(shared) / union if union else 0.0
    return scores


def rrf_fuse_scores(score_a: np.ndarray, score_b: np.ndarray, k: float) -> np.ndarray:
    """RRF over two higher-is-better score arrays (unlike recency_prior_experiment's
    rrf_fuse, which pairs a score with a lower-is-better time gap)."""
    n = len(score_a)
    rank_a = np.empty(n, dtype=np.float64)
    rank_a[np.argsort(-score_a)] = np.arange(n)
    rank_b = np.empty(n, dtype=np.float64)
    rank_b[np.argsort(-score_b)] = np.arange(n)
    return 1.0 / (k + rank_a) + 1.0 / (k + rank_b)


def run_experiment(vault_dir: Path, db_path: Path, sample: int, seed: int,
                   fuse_rrf_k: float | None = None, fuse_metric: str = "aa",
                   exclude_hubs: bool = False, hub_degree: int = 20,
                   direction: str = "both", z_hub_degree: int | None = None) -> dict:
    """Standalone mode (fuse_rrf_k=None): how well AA/Jaccard alone rank the
    true target, and how much their top neighbours overlap with vector's -
    NOT a fair comparison to vector-only ranking (a dedicated embedding model
    should always win alone), the overlap number is what matters here, the
    same way co-commit was judged by overlap rather than standalone accuracy.

    Fusion mode (fuse_rrf_k set): RRF-fuse `fuse_metric`'s rank list with the
    vector-rank list, the fair test of whether adding this signal to vector
    search actually helps, the same methodology recency_prior_experiment.py's
    rrf combine mode uses.

    `direction`: "both" (default, undirected merge), "out" (bibliographic
    coupling - only what the anchor links to), or "in" (co-citation - only
    what links to the anchor). See build_neighbor_sets/score_all.

    `z_hub_degree`: passed straight through to `score_all` - a hard cutoff on
    the shared-neighbor z itself (AA-only), not to be confused with
    `exclude_hubs`/`hub_degree` above which filters the candidate POOL. See
    `score_all`'s docstring for why these are two different mechanisms.
    """
    connection = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        meta, matrix = pkm.load_vectors(connection.cursor())
    finally:
        connection.close()
    if matrix is None:
        return {"error": "no vectors in this index"}
    vec_paths, vec_index_of, pooled = note_vectors(meta, matrix)

    edges = load_all_edges(db_path)
    neighbors = build_neighbor_sets(edges, direction)
    # Degree source for AA's log-degree downweighting is always the undirected
    # merge, even in directional mode - see the ponytail note on score_all.
    degree_neighbors = neighbors if direction == "both" else build_neighbor_sets(edges, "both")
    # Candidate pool is every note touched by an edge at all, direction-independent,
    # so a note with e.g. zero out-degree is still a valid "out"-mode candidate
    # (it just always scores 0) rather than silently missing from the pool -
    # build_neighbor_sets("both") always had this property implicitly (both
    # edge endpoints become keys there), out/in modes don't without this.
    graph_paths = sorted(all_graph_nodes(edges))
    hubs_excluded = 0
    if exclude_hubs:
        hubs = hub_notes(neighbors, hub_degree)
        # ponytail: one filtered list serves both the candidate pool and the
        # anchor-eligibility check below (`a in path_in_graph_index`), so a hub
        # note is dropped as a possible ANCHOR too, not just as a candidate the
        # way co_commit.py's own exclude-hubs only strips hubs from returned
        # results for a query note that is itself never excluded. Stricter than
        # co_commit's version, but the two lists would otherwise duplicate the
        # same sort/enumerate for a one-off stress-test script.
        graph_paths = [p for p in graph_paths if p not in hubs]
        hubs_excluded = len(hubs)
    path_in_graph_index = {p: i for i, p in enumerate(graph_paths)}

    links = wikilink_ground_truth(db_path)
    usable = [(a, b) for a, b in links
             if a in vec_index_of and b in vec_index_of and a in path_in_graph_index]
    rng = np.random.default_rng(seed)
    if len(usable) > sample:
        usable = [usable[i] for i in rng.choice(len(usable), size=sample, replace=False)]

    if fuse_rrf_k is not None:
        result = run_fusion(usable, vec_paths, vec_index_of, pooled, neighbors,
                            graph_paths, path_in_graph_index, fuse_rrf_k, fuse_metric,
                            degree_neighbors=degree_neighbors, z_hub_degree=z_hub_degree)
        if exclude_hubs:
            result["hubs_excluded"] = hubs_excluded
            result["hub_degree"] = hub_degree
        return result

    results = {"aa": {"ranks": [], "baseline": []}, "jaccard": {"ranks": [], "baseline": []}}
    vector_neighbor_sets, aa_neighbor_sets = {}, {}
    for source, target in usable:
        anchor_v_index, target_v_index = vec_index_of[source], vec_index_of[target]
        vector_scores = pooled @ pooled[anchor_v_index]
        baseline_rank = rank_of(vector_scores, vec_index_of, anchor_v_index, target_v_index)
        if baseline_rank is None:
            continue
        # top-10 vector neighbours, for the overlap check below
        top_vector = set(np.array(vec_paths)[np.argsort(-vector_scores)[:11]]) - {source}
        vector_neighbor_sets[source] = top_vector

        if source not in path_in_graph_index or target not in path_in_graph_index:
            continue
        target_g_index = path_in_graph_index[target]
        for graph_metric in ("aa", "jaccard"):
            scores = score_all(neighbors, graph_paths, source, graph_metric,
                               degree_neighbors=degree_neighbors, z_hub_degree=z_hub_degree)
            anchor_g_index = path_in_graph_index[source]
            rank = rank_of(scores, path_in_graph_index, anchor_g_index, target_g_index)
            if rank is not None:
                results[graph_metric]["ranks"].append(rank)
                results[graph_metric]["baseline"].append(baseline_rank)
            if graph_metric == "aa":
                top_aa = set(np.array(graph_paths)[np.argsort(-scores)[:11]]) - {source}
                aa_neighbor_sets[source] = top_aa

    overlaps = [
        len(vector_neighbor_sets[a] & aa_neighbor_sets[a]) / max(1, len(aa_neighbor_sets[a]))
        for a in aa_neighbor_sets if aa_neighbor_sets[a]
    ]

    out = {"pairs_sampled": len(usable), "mean_vector_aa_overlap_pct":
           round(100 * float(np.mean(overlaps)), 1) if overlaps else None}
    if exclude_hubs:
        out["hubs_excluded"] = hubs_excluded
        out["hub_degree"] = hub_degree
    for metric in ("aa", "jaccard"):
        ranks, baseline = results[metric]["ranks"], results[metric]["baseline"]
        if not ranks:
            out[metric] = {"error": "no usable pairs"}
            continue
        mrr = float(np.mean([1 / r for r in ranks]))
        mrr_baseline = float(np.mean([1 / r for r in baseline]))
        out[metric] = {
            "pairs": len(ranks),
            "mean_rank": round(float(np.mean(ranks)), 2),
            "mrr": round(mrr, 4),
            "mrr_vs_vector_baseline_pct": round((mrr / mrr_baseline - 1) * 100, 2) if mrr_baseline else None,
        }
    return out


def run_fusion(usable, vec_paths, vec_index_of, pooled, neighbors, graph_paths,
               path_in_graph_index, k: float, metric: str, degree_neighbors=None,
               z_hub_degree: int | None = None) -> dict:
    """RRF-fuse a graph-structural signal's rank list with the vector-rank list.

    The fair test: not "does AA/Jaccard alone beat vector search" (it won't -
    a dedicated embedding model should always win alone), but "does adding
    this signal to vector search improve on vector search alone."
    """
    # Both signals need one shared, fixed candidate ordering to fuse against -
    # the union of what each side even has an opinion about. A note absent
    # from one side (e.g. never linked, so no graph score) gets that side's
    # worst possible rank rather than being dropped, the same way an unknown
    # creation date got a sentinel gap in the recency experiment. Built once,
    # since vec_paths/graph_paths don't change per anchor.
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

        graph_scores = score_all(neighbors, graph_paths, source, metric,
                                 degree_neighbors=degree_neighbors, z_hub_degree=z_hub_degree)
        v_full = np.full(len(candidates), -1.0, dtype=np.float64)
        v_full[vec_to_cand] = vector_scores
        g_full = np.zeros(len(candidates), dtype=np.float64)
        g_full[graph_to_cand] = graph_scores

        fused = rrf_fuse_scores(v_full, g_full, k)
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
        "metric": metric, "rrf_k": k, "pairs": n,
        "improved": improved, "worsened": worsened, "unchanged": n - improved - worsened,
        "mean_rank_baseline": round(float(np.mean(baseline_ranks)), 2),
        "mean_rank_fused": round(float(np.mean(fused_ranks)), 2),
        "mrr_baseline": round(mrr_baseline, 4),
        "mrr_fused": round(mrr_fused, 4),
        "mrr_change_pct": round((mrr_fused / mrr_baseline - 1) * 100, 2) if mrr_baseline else None,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--vault-dir", help="required unless --self-check")
    parser.add_argument("--db", default=None, help="defaults to <vault>/.obsidian/pkm_index.db")
    parser.add_argument("--sample", type=int, default=500)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--fuse-rrf-k", type=float, default=None,
                        help="RRF-fuse --fuse-metric with vector rank at this k, "
                             "instead of the standalone AA-vs-Jaccard-vs-vector report")
    parser.add_argument("--fuse-metric", choices=["aa", "jaccard"], default="aa")
    parser.add_argument("--exclude-hubs", action="store_true",
                        help="Drop notes with more wikilink neighbours than --hub-degree from "
                             "the candidate pool, mirroring co_commit.py's hub exclusion")
    parser.add_argument("--hub-degree", type=int, default=20,
                        help="A note with more wikilink neighbours than this counts as a hub")
    parser.add_argument("--z-hub-degree", type=int, default=None,
                        help="AA-only: zero out a shared neighbour z's whole contribution "
                             "(not just log-downweight it) once degree(z) exceeds this. "
                             "Different axis than --exclude-hubs/--hub-degree, which filters "
                             "the candidate pool, not the bridging z - see score_all's docstring. "
                             "Off (None) by default for backward compatibility.")
    parser.add_argument("--direction", choices=["both", "out", "in"], default="both",
                        help="both (default): undirected merge, this script's original baseline. "
                             "out: bibliographic coupling, only what the anchor links to (Kessler 1963). "
                             "in: co-citation, only what links to the anchor (Small 1973).")
    parser.add_argument("--self-check", action="store_true")
    parser.add_argument("--recommend-aa-weight", action="store_true",
                        help="Print a non-binding read on whether AA fusion is likely to help "
                             "here, based on this vault's measured wikilink-graph density "
                             "against the 4 real vaults calibrated so far, then exit - does not "
                             "run the experiment or change any live behavior.")
    args = parser.parse_args()
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    if args.self_check:
        return self_check()
    if not args.vault_dir:
        parser.error("--vault-dir is required unless --self-check")

    vault_dir = Path(args.vault_dir).resolve()
    db_path = Path(args.db).resolve() if args.db else pkm.default_db_path(vault_dir)

    if args.recommend_aa_weight:
        neighbors = build_neighbor_sets(load_all_edges(db_path), args.direction)
        avg_degree = sum(len(n) for n in neighbors.values()) / len(neighbors) if neighbors else 0.0
        print(recommend_aa_weight(avg_degree))
        return
    import json
    result = run_experiment(vault_dir, db_path, args.sample, args.seed,
                            args.fuse_rrf_k, args.fuse_metric,
                            args.exclude_hubs, args.hub_degree, args.direction,
                            args.z_hub_degree)
    print(json.dumps(result, indent=1))


def self_check():
    edges = [("a", "z"), ("b", "z"), ("c", "z"), ("a", "y"), ("b", "y")]
    neighbors = build_neighbor_sets(edges)
    # a and b share both y and z; a and c share only z. AA must rank a~b above a~c
    # since z has degree 3 (weak signal) while y has degree 2 (stronger signal).
    paths = ["a", "b", "c", "y", "z"]
    scores_from_a = score_all(neighbors, paths, "a", "aa")
    index_of = {p: i for i, p in enumerate(paths)}
    assert scores_from_a[index_of["b"]] > scores_from_a[index_of["c"]], \
        "sharing two neighbours (one of them lower-degree) should score higher than sharing one"
    jaccard_from_a = score_all(neighbors, paths, "a", "jaccard")
    assert jaccard_from_a[index_of["b"]] > jaccard_from_a[index_of["c"]]
    # z has degree 3 (a, b, c all link to it) - a threshold of 2 makes it a hub,
    # a threshold of 3 does not.
    assert hub_notes(neighbors, 2) == {"z"}
    assert hub_notes(neighbors, 3) == set()

    # z_hub_degree: a and c share ONLY z (degree 3); a and b share z AND y
    # (degree 2). At z_hub_degree=2, z's whole term must drop to 0 (3 > 2)
    # while y's term survives (2 <= 2) - a~c should go to exactly 0, a~b
    # should stay positive but shrink (loses z's contribution too). This is
    # the game-portfolio-portfolio false positive in miniature: two notes whose
    # only connection is a shared same-session catalog/hub note should not
    # score above zero just because that hub's degree is high.
    aa_c_no_cutoff = score_all(neighbors, paths, "a", "aa")[index_of["c"]]
    assert aa_c_no_cutoff > 0, "sanity: a~c does score positive without a cutoff"
    aa_c_cutoff = score_all(neighbors, paths, "a", "aa", z_hub_degree=2)[index_of["c"]]
    assert aa_c_cutoff == 0.0, "z_hub_degree=2 must zero out a~c's only shared neighbour (degree 3 > 2)"
    aa_b_no_cutoff = score_all(neighbors, paths, "a", "aa")[index_of["b"]]
    aa_b_cutoff = score_all(neighbors, paths, "a", "aa", z_hub_degree=2)[index_of["b"]]
    assert 0 < aa_b_cutoff < aa_b_no_cutoff, "a~b keeps y's contribution but loses z's under the cutoff"

    # Directional split: bibliographic coupling (out) vs co-citation (in),
    # Kessler 1963 / Small 1973. Built so the merged/undirected view (the
    # baseline above, and the one tested first tonight) sees a and b as
    # related AND a and c as related, but a direction-aware view should see
    # only one relationship each - a clean divergence by construction:
    #   p1 -> a, p1 -> b, p2 -> a, p2 -> b   (a and b are co-cited by p1, p2)
    #   a -> x, c -> x                        (a and c both cite/reference x)
    # b has no outbound edges at all, and c has no inbound edges at all, so
    # each direction's "no shared neighbour" case is exercised too.
    directed_edges = [("p1", "a"), ("p1", "b"), ("p2", "a"), ("p2", "b"),
                       ("a", "x"), ("c", "x")]
    out_neighbors = build_neighbor_sets(directed_edges, "out")
    in_neighbors = build_neighbor_sets(directed_edges, "in")
    both_neighbors = build_neighbor_sets(directed_edges, "both")
    dpaths = ["a", "b", "c", "p1", "p2", "x"]
    d_index = {p: i for i, p in enumerate(dpaths)}

    # out (coupling): a and c both link to x - out must see this, and must not
    # invent a match between a and b, since b links to nothing at all.
    out_scores = score_all(out_neighbors, dpaths, "a", "aa", degree_neighbors=both_neighbors)
    assert out_scores[d_index["c"]] > 0, "a and c both link to x - coupling should see this"
    assert out_scores[d_index["b"]] == 0, "b has no outbound links - coupling must not invent a match"

    # in (co-citation): a and b are both linked-to by p1 and p2 - in must see
    # this, and must not invent a match between a and c, since c is linked
    # to by nobody.
    in_scores = score_all(in_neighbors, dpaths, "a", "aa", degree_neighbors=both_neighbors)
    assert in_scores[d_index["b"]] > 0, "a and b are both cited by p1 and p2 - co-citation should see this"
    assert in_scores[d_index["c"]] == 0, "nobody links to c - co-citation must not invent a match"

    # both (the undirected merge, tonight's earlier baseline) blurs the two
    # relationships together, seeing both where out/in each saw only one.
    both_scores = score_all(both_neighbors, dpaths, "a", "aa", degree_neighbors=both_neighbors)
    assert both_scores[d_index["b"]] > 0 and both_scores[d_index["c"]] > 0, \
        "merging directions should surface both relationships the directional views kept separate"

    # recommend_aa_weight is advisory text, not a rule - just check it names
    # the right band and never claims more certainty than the n=4 data has.
    assert "below" in recommend_aa_weight(2.0).lower()
    assert "no real calibration data" in recommend_aa_weight(6.0)
    assert "n=1" in recommend_aa_weight(9.0)
    assert "not a rule to automate" in recommend_aa_weight(5.0)

    print("self-check ok")


if __name__ == "__main__":
    main()
