---
date: 2026-08-30
created: 2026-08-30
tags:
  - obsidian
  - search
  - embeddings
  - pkm
---

> [!summary] eli5
> the search daemon holds vectors, wikilinks, and a query log. beyond search, this is what else it can answer, measured over 3,080 notes rather than assumed.
> missing links ranked by mutual-kNN similarity hit 95% on the top 20: pairs the index knows are close that you never linked. duplicate detection at 0.95 cosine separates 43 near-duplicate pairs from 650 related ones. co-retrieval looked like 4,884 associations from 8,322 logged queries and turned out to be one benchmark query run 2,870 times. orphan detection reaches 122 unlinked notes, though 96% of the vault already has links so the list is small. the query log is too new to show what search misses.
> **needs from you:** nothing. the ranking is below, and the two features at the top of it shipped the day it was written.

> [!todo] next
> **next:** nothing from this list. missing links shipped on 2026-08-30, co-retrieval was measured the same day and dropped, and the three below all say wait. the next thing the index answers comes from using the plugin, not from this ranking.
> **blocked:** nothing.

**why:** [[2026-08-29 one obsidian plugin over the search daemon]]

the daemon already serves `/search`, `/similar`, `/links`, `/unlinked`, `/graph`. the graph endpoint gave mutual-kNN edges for the whole vault on 2026-08-30, and the query log has been recording every search since 2026-08-27. the question is what else those can answer that is worth building.

## what was measured

five candidate features, tested over the brain corpus (3,080 notes, 7,301 sections, 10,257 mutual-kNN edges, 8,322 logged queries):

1. **missing links:** mutual-kNN pairs with no wikilink between them, ranked by similarity. sampled the top 20 by reading note titles and first lines. 19 of 20 should be linked (95% hit rate): disc podcast series pairs, related amino acids, skill documentation and its progress note, obsidian feature pairs, maya control features, entity registry versions. one unclear. zero false positives in the top 20.

2. **co-retrieval edges:** notes that keep appearing in the same search results. the log holds 8,322 queries over three days, producing 4,884 distinct note pairs with decayed weights from 1.0 to 3,012, and the incremental fold from `co_retrieval.py` works. the pairs are not evidence though: a later pass classified the log and found 97% of it is benchmark traffic, half the pair mass coming from one query repeated 2,870 times, which is why the battery and solar clusters sit at the top.

3. **query misses:** what search did not find. 5,926 queries, 2,967 distinct, zero returned empty, one returned fewer than four notes (stream deck), and 82 reformulation runs covering 5,924 queries. most reformulations are test probes with synthetic query strings (battery vector n5445104, linter cache n5460141). the log is too young and too full of daemon tests to show what real searches miss. ask again in a month.

4. **duplicate detection:** pairs above a cosine threshold. measured the similarity distribution over all 4,375,761 note pairs: p50 is 0.524, p95 is 0.678, p99.9 is 0.848. 43 pairs above 0.95, 650 above 0.90, 4,095 above 0.85. the 0.95 threshold separates near-duplicates (disc podcast variants, glutamic acid and glutamine, medical and medical condition, vault index work log and progress note) from related notes. above 0.90 is too broad, above 0.85 is noise.

5. **orphans and hubs:** degree distribution from the wikilink graph. 122 orphans (4.0%), 2,958 notes with links (96.0%). degree distribution: median 3, mean 5.6, max 111 (obsidian.md). 509 notes at degree 1, 1,575 at degree 2-5, 10 above degree 50. the orphan list exists and is queryable, but 96% coverage means the list is small and most of it is stub notes (drawing files, single-topic references, certification pages). hubs are correct: obsidian, aws, maya, python, unreal.

## features ranked by value over cost

1. **missing links (shipped 2026-08-30).** 3,751 edges the index found that you did not write, 95% hit rate at the top, ranked by similarity so the list starts with the best. it cost less than the route this note asked for: the plugin already caches the `/graph` payload for its views, so the feature is a filter on `linked == 0`, a sort, and a `!` prefix in the search modal. 5ms over the cached payload, top 200 kept, and obsidian's own link map is subtracted as well as the index's so a link written since the last pass does not read as missing. the top of the list on the public corpus is near-duplicate pairs rather than missing links, which is the duplicate feature below arriving early and unasked.

2. **co-retrieval edges folded into ranking (measured on 2026-08-30, do not build).** the eval was run before the wiring, which is the right order, and it said no: no bonus weight moves nDCG@10 by more than 0.02, the sign flips between neighbouring weights, and the best of 21 cells has p(Δ>0) of 0.89. the reason is upstream of the ranking — 97% of the query log is benchmark traffic, and the 4,884 pairs counted below are mostly one query run 2,870 times. the full measurement is in [[2026-08-30 co-retrieval edges do not improve ranking]], including the two defects it turned up: a multi-corpus search was logging its edges under a composite corpus name, now fixed, and `eval_rerank.py`'s headline metric is invariant under reordering, so it cannot see a rerank at all.

3. **duplicate detection at 0.95 (build it when note count climbs).** 43 pairs is a small list, and most are legitimate variants (disc series, progress notes on the same system, amino acid pairs). the feature is "check for duplicates before writing a note," which `index_pkm_meta.py --check-duplicate` already does. the route is one line, `/duplicates?threshold=0.95`. value is preventing note sprawl, but at 43 pairs over 3,080 notes the problem is not burning yet. build it when the vault hits 10,000 notes or the pair count breaks 200.

4. **query miss analysis (wait).** the log exists, `query_misses.py` reads it, but three days of mostly test traffic is not enough to say what real searches miss. the reformulation detector works (82 runs found), but drift 0.00 on "battery vector n5445104 -> vector unity n5445107" is a test, not a user struggling. wait until the log has 30 days of real plugin use, then read it. no route needed, the CLI tool is enough.

5. **orphan list (do not build).** 122 orphans is 4% of the vault, and sampling the list shows stub notes and single-topic references that are correctly unlinked. degree 1 is a bigger pool (509 notes), but that is also correct: a note linked once is not an error. the query is one line (`SELECT path FROM notes WHERE path NOT IN (SELECT DISTINCT source_path FROM edges UNION SELECT DISTINCT resolved_target_path FROM edges WHERE resolved_target_path IS NOT NULL)`), but there is no action to take on the result. the orphan list does not earn a route or a pane.

6. **whole-vault graph (shipped 2026-08-30, ranked last and built anyway).** the ranking said last, and it was: the `/graph` route made the data free, so the remaining work was a canvas and a force layout, which came to a day. 116ms of layout at the 300-node default and 986ms for all 2,960 nodes, so the whole corpus is a button rather than what opens. the reservation stands unchanged and is still untested: a picture of everything is the feature that gets opened once. the filter that might save it, "start from the open note's neighbourhood," is what the view does by default.

## the measurements

| feature | measured value | threshold or count | cost | rank |
| --- | --- | --- | --- | --- |
| missing links | 3,751 pairs, 95% hit rate on top 20 | semantic edges without wikilinks | shipped: a filter on the cached graph, 5ms | 1 |
| co-retrieval | no gain over baseline, 97% of the log is machine traffic | nDCG@10 within ±0.043 at every weight | measured, dropped | 2 |
| duplicates | 43 pairs at 0.95, 650 at 0.90 | cosine > 0.95 | one route, burns at scale | 3 |
| query misses | 0 empty, 1 narrow, 82 reformulations | log too young | wait 30 days | 4 |
| orphans | 122 notes, 4.0% of vault | degree 0 | one query, no action | 5 |
| whole-vault graph | 10,257 edges, 2,959 nodes | mutual-kNN k=10 | shipped: 116ms at 300 nodes, 986ms at 2,960 | 6 |

related: [[2026-08-30 a semantic graph over the whole vault]] for the mutual-kNN measurement that makes missing links possible, [[co-retrieval edges from the search log]] for how the log becomes edges, and [[core Obsidian features to rework on the vault index]] for what the plugin already replaced.
