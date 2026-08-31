"""Test shared-frontmatter-tag Jaccard similarity against real wikilinks, and
measure overlap with vector similarity.

Candidate #3 in "other candidate relatedness signals for search reranking":
`notes.tags` is already extracted by the indexer, so a tag-similarity score is
almost free to compute. The weak hypothesis under test, in the research
note's own words: "tags track topic, and topic is exactly what the embeddings
already capture, so expected marginal value over vector similarity is low."
That has only ever been guessed at - this settles it with real numbers.

    Jaccard(a, b) = |tags(a) & tags(b)| / |tags(a) | tags(b)|

# ponytail: plain Jaccard only, no TF-IDF/IDF-weighted tag scoring (which
# would downweight a tag like "technical" that half the vault carries the
# same way Adamic-Adar downweights a high-degree shared neighbour). The
# research note's own convention is "simplest thing that could settle the
# question" - upgrade to a weighted variant only if plain Jaccard's result
# is ambiguous enough to need it.

Same evaluation as shared_neighbor_experiment.py, which itself reuses
recency_prior_experiment.py's rank_of/wikilink_ground_truth/note_vectors:
explicit [[wikilinks]] as ground truth (no LLM judge available), MRR against
a vector-only baseline, RRF-fusion against vector rank (swept over k by
invoking this script with different --fuse-rrf-k values, the same way
shared_neighbor_experiment.py's k-sweep was driven), and a standalone overlap
% with vector's top neighbours - the number that actually decided candidate
#1 (22.5% redundancy, not its standalone MRR), not just a headline MRR.

    python skills/pkm-metadata-indexer/tags_overlap_experiment.py --vault-dir <vault> --sample 500
    python skills/pkm-metadata-indexer/tags_overlap_experiment.py --vault-dir <vault> --sample 500 --fuse-rrf-k 60
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
import index_pkm_meta as pkm
from recency_prior_experiment import rank_of, wikilink_ground_truth, note_vectors
from shared_neighbor_experiment import rrf_fuse_scores


def load_note_tags(db_path: Path) -> dict[str, set[str]]:
    """Every note's tag set, including notes with none (empty set, not absent) -
    coverage is exactly the question item 3 asks, so notes with zero tags must
    stay visible rather than being silently dropped here."""
    connection = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        rows = connection.execute("SELECT path, tags FROM notes").fetchall()
    finally:
        connection.close()
    tags_by_path: dict[str, set[str]] = {}
    for path, raw_tags in rows:
        try:
            tags = json.loads(raw_tags) if raw_tags else []
        except (json.JSONDecodeError, TypeError):
            tags = []
        tags_by_path[path] = set(tags)
    return tags_by_path


def hub_notes(tags_by_path: dict[str, set[str]], degree_threshold: int) -> set[str]:
    """Notes sharing at least one tag with more than `degree_threshold` other
    notes - the tag-graph analogue of co_commit.py's hub_notes() and
    shared_neighbor_experiment.py's wikilink-degree hub_notes(). "Degree" here
    is co-occurrence degree (how many OTHER notes share >=1 tag with this one),
    not tag count - a note with a single common tag like "technical" can have
    enormous degree this way, which is exactly the hub-note failure mode this
    is meant to catch. A hard cutoff, distinct from plain Jaccard's union-size
    normalisation, which softens a large shared-tag-population's effect on a
    single pair's score but never removes a note from the candidate pool.

    Built via an inverted tag->notes index rather than an O(n^2) pairwise scan
    over ~3,000 notes, the same reason co_commit.py's version is one SQL
    GROUP BY instead of a nested loop over commits.
    """
    tag_to_notes: dict[str, set[str]] = defaultdict(set)
    for path, tags in tags_by_path.items():
        for tag in tags:
            tag_to_notes[tag].add(path)
    hubs = set()
    for path, tags in tags_by_path.items():
        if not tags:
            continue
        connected: set[str] = set()
        for tag in tags:
            connected |= tag_to_notes[tag]
        connected.discard(path)
        if len(connected) > degree_threshold:
            hubs.add(path)
    return hubs


def score_all(tags_by_path: dict[str, set[str]], paths: list[str], anchor: str) -> np.ndarray:
    anchor_tags = tags_by_path.get(anchor, set())
    scores = np.zeros(len(paths), dtype=np.float64)
    if not anchor_tags:
        return scores
    for index, path in enumerate(paths):
        other_tags = tags_by_path.get(path, set())
        if not other_tags:
            continue
        union = len(anchor_tags | other_tags)
        scores[index] = len(anchor_tags & other_tags) / union if union else 0.0
    return scores


def run_experiment(vault_dir: Path, db_path: Path, sample: int, seed: int,
                   fuse_rrf_k: float | None = None,
                   exclude_hubs: bool = False, hub_degree: int = 20) -> dict:
    """Standalone mode (fuse_rrf_k=None): how well tag-Jaccard alone ranks the
    true target, and how much its top neighbours overlap with vector's - NOT a
    fair comparison to vector-only ranking, the overlap number is what matters,
    the same way co-commit and shared-neighbor AA were judged by overlap
    rather than standalone accuracy.

    Fusion mode (fuse_rrf_k set): RRF-fuse the tag-Jaccard rank list with the
    vector-rank list, the fair test of whether adding this signal to vector
    search actually helps.
    """
    connection = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        meta, matrix = pkm.load_vectors(connection.cursor())
    finally:
        connection.close()
    if matrix is None:
        return {"error": "no vectors in this index"}
    vec_paths, vec_index_of, pooled = note_vectors(meta, matrix)

    tags_by_path = load_note_tags(db_path)
    total_notes = len(tags_by_path)
    tagged_notes = sum(1 for tags in tags_by_path.values() if tags)
    tag_paths = sorted(tags_by_path)
    hubs_excluded = 0
    if exclude_hubs:
        hubs = hub_notes(tags_by_path, hub_degree)
        # ponytail: same one-list-serves-both-roles simplification as
        # shared_neighbor_experiment.py's --exclude-hubs - a hub note is
        # dropped as a possible anchor too, not just as a candidate.
        tag_paths = [p for p in tag_paths if p not in hubs]
        hubs_excluded = len(hubs)
    path_in_tag_index = {p: i for i, p in enumerate(tag_paths)}

    links = wikilink_ground_truth(db_path)
    candidate_pairs = [(a, b) for a, b in links if a in vec_index_of and b in vec_index_of
                       and a in path_in_tag_index and b in path_in_tag_index]
    # "usable" additionally requires the anchor to actually carry a tag - an
    # anchor with none scores every candidate 0, which is a fair result for
    # the signal (it truly has no opinion) but not a fair evaluation sample:
    # rank_of would just return tie-break order, not a measurement of Jaccard.
    usable = [(a, b) for a, b in candidate_pairs if tags_by_path[a]]
    dropped_no_anchor_tags = len(candidate_pairs) - len(usable)

    rng = np.random.default_rng(seed)
    if len(usable) > sample:
        usable = [usable[i] for i in rng.choice(len(usable), size=sample, replace=False)]

    coverage = {
        "notes_total": total_notes,
        "notes_with_tags": tagged_notes,
        "notes_with_tags_pct": round(100 * tagged_notes / total_notes, 1) if total_notes else None,
        "wikilinked_pairs_both_in_index": len(candidate_pairs) + dropped_no_anchor_tags,
        "dropped_anchor_has_no_tags": dropped_no_anchor_tags,
    }
    if exclude_hubs:
        coverage["hubs_excluded"] = hubs_excluded
        coverage["hub_degree"] = hub_degree

    if fuse_rrf_k is not None:
        result = run_fusion(usable, vec_paths, vec_index_of, pooled, tags_by_path,
                            tag_paths, path_in_tag_index, fuse_rrf_k)
        result["coverage"] = coverage
        return result

    ranks, baseline = [], []
    vector_neighbor_sets, tag_neighbor_sets = {}, {}
    for source, target in usable:
        anchor_v_index, target_v_index = vec_index_of[source], vec_index_of[target]
        vector_scores = pooled @ pooled[anchor_v_index]
        baseline_rank = rank_of(vector_scores, vec_index_of, anchor_v_index, target_v_index)
        if baseline_rank is None:
            continue
        top_vector = set(np.array(vec_paths)[np.argsort(-vector_scores)[:11]]) - {source}
        vector_neighbor_sets[source] = top_vector

        scores = score_all(tags_by_path, tag_paths, source)
        anchor_t_index, target_t_index = path_in_tag_index[source], path_in_tag_index[target]
        rank = rank_of(scores, path_in_tag_index, anchor_t_index, target_t_index)
        if rank is not None:
            ranks.append(rank)
            baseline.append(baseline_rank)
        top_tags = set(np.array(tag_paths)[np.argsort(-scores)[:11]]) - {source}
        tag_neighbor_sets[source] = top_tags

    overlaps = [
        len(vector_neighbor_sets[a] & tag_neighbor_sets[a]) / max(1, len(tag_neighbor_sets[a]))
        for a in tag_neighbor_sets if tag_neighbor_sets[a]
    ]

    out = {
        "pairs_sampled": len(usable),
        "mean_vector_tag_overlap_pct": round(100 * float(np.mean(overlaps)), 1) if overlaps else None,
        "coverage": coverage,
    }
    if not ranks:
        out["jaccard"] = {"error": "no usable pairs"}
        return out
    mrr = float(np.mean([1 / r for r in ranks]))
    mrr_baseline = float(np.mean([1 / r for r in baseline]))
    out["jaccard"] = {
        "pairs": len(ranks),
        "mean_rank": round(float(np.mean(ranks)), 2),
        "mrr": round(mrr, 4),
        "mrr_vs_vector_baseline_pct": round((mrr / mrr_baseline - 1) * 100, 2) if mrr_baseline else None,
    }
    return out


def run_fusion(usable, vec_paths, vec_index_of, pooled, tags_by_path, tag_paths,
              path_in_tag_index, k: float) -> dict:
    """RRF-fuse tag-Jaccard's rank list with the vector-rank list - the fair
    test of whether adding this signal to vector search improves on vector
    search alone, not whether Jaccard beats vector search by itself."""
    candidates = sorted(set(vec_paths) | set(tag_paths))
    cand_index = {p: i for i, p in enumerate(candidates)}
    vec_to_cand = np.array([cand_index.get(p, -1) for p in vec_paths])
    tag_to_cand = np.array([cand_index.get(p, -1) for p in tag_paths])

    baseline_ranks, fused_ranks = [], []
    for source, target in usable:
        anchor_v_index, target_v_index = vec_index_of[source], vec_index_of[target]
        vector_scores = pooled @ pooled[anchor_v_index]
        baseline_rank = rank_of(vector_scores, vec_index_of, anchor_v_index, target_v_index)
        if baseline_rank is None:
            continue

        tag_scores = score_all(tags_by_path, tag_paths, source)
        v_full = np.full(len(candidates), -1.0, dtype=np.float64)
        v_full[vec_to_cand] = vector_scores
        t_full = np.zeros(len(candidates), dtype=np.float64)
        t_full[tag_to_cand] = tag_scores

        fused = rrf_fuse_scores(v_full, t_full, k)
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
        "rrf_k": k, "pairs": n,
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
                        help="RRF-fuse tag-Jaccard with vector rank at this k, instead of "
                             "the standalone Jaccard-vs-vector report")
    parser.add_argument("--exclude-hubs", action="store_true",
                        help="Drop notes sharing a tag with more than --hub-degree other notes "
                             "from the candidate pool, mirroring co_commit.py's hub exclusion")
    parser.add_argument("--hub-degree", type=int, default=20,
                        help="A note tag-connected to more other notes than this counts as a hub")
    parser.add_argument("--self-check", action="store_true")
    args = parser.parse_args()
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    if args.self_check:
        return self_check()
    if not args.vault_dir:
        parser.error("--vault-dir is required unless --self-check")

    vault_dir = Path(args.vault_dir).resolve()
    db_path = Path(args.db).resolve() if args.db else pkm.default_db_path(vault_dir)
    result = run_experiment(vault_dir, db_path, args.sample, args.seed, args.fuse_rrf_k,
                            args.exclude_hubs, args.hub_degree)
    print(json.dumps(result, indent=1))


def self_check():
    tags_by_path = {"a": {"cat", "dog", "fish"}, "b": {"cat", "dog"}, "c": {"cat"}, "d": set()}
    paths = ["a", "b", "c", "d"]
    scores_from_a = score_all(tags_by_path, paths, "a")
    index_of = {p: i for i, p in enumerate(paths)}
    # b shares 2/3 tags with a (Jaccard 2/3), c shares 1/3 (Jaccard 1/3) -
    # b must rank above c, and d (no tags at all) must score exactly 0.
    assert scores_from_a[index_of["b"]] > scores_from_a[index_of["c"]], \
        "sharing more tags should score higher"
    assert scores_from_a[index_of["d"]] == 0.0, "a note with no tags shares nothing"
    assert abs(scores_from_a[index_of["b"]] - 2 / 3) < 1e-9
    assert abs(scores_from_a[index_of["c"]] - 1 / 3) < 1e-9
    # an anchor with no tags of its own has no opinion about anyone
    scores_from_d = score_all(tags_by_path, paths, "d")
    assert np.all(scores_from_d == 0.0)
    # a, b, c all share "cat" so each is tag-connected to the other two (degree
    # 2); d has no tags so it is never a hub regardless of threshold.
    assert hub_notes(tags_by_path, 1) == {"a", "b", "c"}
    assert hub_notes(tags_by_path, 2) == set()
    print("self-check ok")


if __name__ == "__main__":
    main()
