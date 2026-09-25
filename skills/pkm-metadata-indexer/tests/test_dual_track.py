"""Acceptance tests for the dual-track structural search.

The graph tests build their `edges` rows by hand rather than by indexing markdown.
A wikilink only resolves to a path when the target note exists, so a fixture that
wrote `[[Hub]]` into a file would be testing the resolver as well as the traversal,
and a degree-50 hub would need fifty real notes on disk to exist at all.
"""

import importlib.util
import sqlite3
import sys
import tempfile
import time
import unittest
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL))

import dual_track  # noqa: E402
import query_parser  # noqa: E402
from query_parser import fts_literal, parse_query_facets, split_terms  # noqa: E402

SPEC = importlib.util.spec_from_file_location("test_indexer_dual", SKILL / "index_pkm_meta.py")
INDEXER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(INDEXER)


def build_vault(root: Path, notes: dict[str, str]) -> Path:
    """Index `notes` into a throwaway vault and return its database path."""
    (root / ".obsidian").mkdir(parents=True, exist_ok=True)
    for name, body in notes.items():
        target = root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(body, encoding="utf-8")
    database = root / ".obsidian" / "pkm_index.db"
    INDEXER.build_index(str(root), str(database), skip_embeddings=True)
    return database


def write_edges(database: Path, edges: list[tuple[str, str]]) -> None:
    """Replace the edge table with an exact graph, one row per (source, target)."""
    connection = sqlite3.connect(database)
    try:
        connection.execute("DELETE FROM edges")
        connection.executemany(
            "INSERT OR REPLACE INTO edges (source_path, raw_target, resolved_target_path, start_line)"
            " VALUES (?, ?, ?, 1)",
            [(source, Path(target).stem, target) for source, target in edges],
        )
        connection.commit()
    finally:
        connection.close()


class FacetClusteringTest(unittest.TestCase):
    def test_four_terms_make_four_facets(self):
        parsed = parse_query_facets("stroke fatigue dopamine coding")
        self.assertEqual([facet["term"] for facet in parsed["facets"]],
                         ["stroke", "fatigue", "dopamine", "coding"])
        self.assertFalse(parsed["single_entity"])

    def test_quoted_phrase_stays_one_facet(self):
        parsed = parse_query_facets('"exact phrase" single')
        terms = [facet["term"] for facet in parsed["facets"]]
        self.assertEqual(terms, ["exact phrase", "single"])
        self.assertTrue(parsed["facets"][0]["verbatim"])
        self.assertEqual(parsed["facets"][0]["expression"], '"exact phrase"')

    def test_single_quotes_are_atomic_too(self):
        parsed = parse_query_facets("'sarah notes'")
        self.assertEqual([facet["term"] for facet in parsed["facets"]], ["sarah notes"])
        self.assertTrue(parsed["single_entity"])

    def test_stop_words_do_not_become_facets(self):
        parsed = parse_query_facets("notes about the stroke and fatigue")
        self.assertEqual([facet["term"] for facet in parsed["facets"]],
                         ["notes", "stroke", "fatigue"])

    def test_one_term_is_a_single_entity_query(self):
        self.assertTrue(parse_query_facets("HRV")["single_entity"])

    def test_terms_past_the_cap_are_reported_not_dropped_silently(self):
        parsed = parse_query_facets(" ".join(f"term{index}" for index in range(12)))
        self.assertEqual(len(parsed["facets"]), query_parser.MAX_FACETS)
        self.assertEqual(len(parsed["dropped"]), 12 - query_parser.MAX_FACETS)

    def test_fts_literal_doubles_internal_quotes(self):
        # A stripped quote silently changes the term; a doubled one is the FTS5
        # escape and preserves it.
        self.assertEqual(fts_literal('say "hi"'), '"say ""hi"""')

    def test_punctuation_only_term_is_dropped_not_quoted(self):
        # `MATCH ""` is a syntax error that would take the whole facet pass down.
        parsed = parse_query_facets("stroke ---")
        self.assertEqual([facet["term"] for facet in parsed["facets"]], ["stroke"])

    def test_split_terms_keeps_reading_order(self):
        plain, verbatim = split_terms('alpha "beta gamma" delta')
        self.assertEqual(plain, ["alpha", "delta"])
        self.assertEqual(verbatim, ["beta gamma"])


class FtsIntersectionTest(unittest.TestCase):
    def test_three_of_three_outranks_one_of_three(self):
        with tempfile.TemporaryDirectory() as temp:
            database = build_vault(Path(temp) / "vault", {
                "covers-all.md": (
                    "## Fatigue\nPost stroke fatigue milestones.\n\n"
                    "## Reward\nA dopamine reward loop.\n\n"
                    "## Sessions\nLong coding sessions.\n"
                ),
                "covers-one.md": (
                    "## Dopamine\ndopamine dopamine dopamine dopamine dopamine\n"
                ),
            })
            parsed = parse_query_facets("fatigue dopamine coding", database)
            connection = dual_track.connect(database)
            try:
                ranked = dual_track.rank_facet_matches(
                    dual_track.facet_intersection(connection, parsed["facets"]))
            finally:
                connection.close()
            by_path = {row["path"]: row for row in ranked}
            self.assertEqual(by_path["covers-all.md"]["coverage"], 3)
            self.assertEqual(by_path["covers-one.md"]["coverage"], 1)
            # Coverage leads, so the note repeating one term loses to the note
            # covering three even though bm25 prefers the repetition.
            self.assertEqual(ranked[0]["path"], "covers-all.md")

    def test_headings_carry_the_line_the_facet_was_found_on(self):
        with tempfile.TemporaryDirectory() as temp:
            database = build_vault(Path(temp) / "vault", {
                "anchored.md": "## Intro\nnothing here\n\n## Deep\nthe hyperfocus section\n",
            })
            parsed = parse_query_facets("hyperfocus", database)
            connection = dual_track.connect(database)
            try:
                found = dual_track.facet_intersection(connection, parsed["facets"])
            finally:
                connection.close()
            headings = found["anchored.md"]["headings"]
            self.assertTrue(headings)
            self.assertEqual(headings[0]["heading"], "Deep")
            # The point of the whole mode: a line number, so nothing reads line 1..N.
            self.assertGreater(headings[0]["line"], 1)

    def test_a_title_only_match_still_counts_as_coverage(self):
        with tempfile.TemporaryDirectory() as temp:
            database = build_vault(Path(temp) / "vault", {
                "hyperfocus.md": "## Body\nunrelated words entirely\n",
            })
            parsed = parse_query_facets("hyperfocus", database)
            connection = dual_track.connect(database)
            try:
                found = dual_track.facet_intersection(connection, parsed["facets"])
            finally:
                connection.close()
            self.assertIn("hyperfocus.md", found)
            self.assertTrue(found["hyperfocus.md"]["titled"])

    def test_scores_are_positive_is_better(self):
        # bm25 returns a more negative number for a better match. If that leaked
        # out, the secondary sort would run backwards.
        with tempfile.TemporaryDirectory() as temp:
            database = build_vault(Path(temp) / "vault", {
                "one.md": "## A\nhyperfocus\n",
            })
            parsed = parse_query_facets("hyperfocus", database)
            connection = dual_track.connect(database)
            try:
                found = dual_track.facet_intersection(connection, parsed["facets"])
            finally:
                connection.close()
            self.assertGreater(found["one.md"]["score"], 0)


class RecursiveGraphTest(unittest.TestCase):
    """A -> B -> C, and A -> Hub -> D where Hub has degree 50."""

    def graph(self, temp: str) -> Path:
        notes = {name: f"## Body\n{name} body text\n" for name in
                 ("A.md", "B.md", "C.md", "D.md", "Hub.md")}
        database = build_vault(Path(temp) / "vault", notes)
        edges = [("A.md", "B.md"), ("B.md", "C.md"), ("A.md", "Hub.md"), ("Hub.md", "D.md")]
        # Pad Hub's out-degree past HUB_DEGREE. Out-degree is what makes a
        # map-of-content a hub, and an in-degree-only count would score Hub at 1.
        edges += [("Hub.md", f"filler-{index}.md") for index in range(50)]
        write_edges(database, edges)
        return database

    def test_two_hop_target_is_reached(self):
        with tempfile.TemporaryDirectory() as temp:
            connection = dual_track.connect(self.graph(temp))
            try:
                rows = dual_track.graph_neighborhood(connection, ["A.md"], [], hops=2)
            finally:
                connection.close()
            reached = {row["path"]: row for row in rows}
            self.assertIn("C.md", reached, "A -> B -> C is a 2-hop path and must be found")
            self.assertEqual(reached["C.md"]["hop"], 2)
            self.assertEqual(reached["C.md"]["via"], "B.md")

    def test_hub_is_pruned_when_it_matches_no_facet(self):
        with tempfile.TemporaryDirectory() as temp:
            connection = dual_track.connect(self.graph(temp))
            try:
                rows = dual_track.graph_neighborhood(connection, ["A.md"], [], hops=2)
            finally:
                connection.close()
            reached = {row["path"] for row in rows}
            self.assertNotIn("D.md", reached,
                             "D sits behind a degree-50 hub that matched nothing")
            # The hub itself is one hop out and is still reported; only walking
            # *through* it is refused.
            self.assertIn("Hub.md", reached)

    def test_hub_is_traversed_when_it_matches_a_facet(self):
        with tempfile.TemporaryDirectory() as temp:
            connection = dual_track.connect(self.graph(temp))
            try:
                rows = dual_track.graph_neighborhood(
                    connection, ["A.md"], ["Hub.md"], hops=2)
            finally:
                connection.close()
            reached = {row["path"] for row in rows}
            self.assertIn("D.md", reached,
                          "an on-topic hub is a bridge, not a switchboard")

    def test_one_hop_stops_at_one_hop(self):
        with tempfile.TemporaryDirectory() as temp:
            connection = dual_track.connect(self.graph(temp))
            try:
                rows = dual_track.graph_neighborhood(connection, ["A.md"], [], hops=1)
            finally:
                connection.close()
            self.assertEqual({row["hop"] for row in rows}, {1})
            self.assertNotIn("C.md", {row["path"] for row in rows})

    def test_cycle_terminates(self):
        with tempfile.TemporaryDirectory() as temp:
            database = build_vault(Path(temp) / "vault", {
                "A.md": "## A\nbody\n", "B.md": "## B\nbody\n",
            })
            write_edges(database, [("A.md", "B.md"), ("B.md", "A.md")])
            connection = dual_track.connect(database)
            try:
                began = time.perf_counter()
                rows = dual_track.graph_neighborhood(connection, ["A.md"], [], hops=2)
                elapsed = time.perf_counter() - began
            finally:
                connection.close()
            self.assertLess(elapsed, 1.0, "A -> B -> A must not loop")
            # A is the seed and B is one hop out; returning to A is not a discovery.
            self.assertEqual({row["path"] for row in rows}, {"B.md"})

    def test_substring_paths_are_not_mistaken_for_a_revisit(self):
        # `b.md` is a substring of `folder/b.md`. A naive cycle check prunes the
        # second hop here; the delimiter-wrapped one does not.
        with tempfile.TemporaryDirectory() as temp:
            database = build_vault(Path(temp) / "vault", {
                "b.md": "## b\nbody\n",
                "folder/b.md": "## nested\nbody\n",
                "folder/c.md": "## c\nbody\n",
            })
            write_edges(database, [("b.md", "folder/b.md"), ("folder/b.md", "folder/c.md")])
            connection = dual_track.connect(database)
            try:
                rows = dual_track.graph_neighborhood(connection, ["b.md"], [], hops=2)
            finally:
                connection.close()
            self.assertIn("folder/c.md", {row["path"] for row in rows})

    def test_no_seeds_is_an_empty_walk_not_a_whole_vault(self):
        with tempfile.TemporaryDirectory() as temp:
            connection = dual_track.connect(self.graph(temp))
            try:
                self.assertEqual(dual_track.graph_neighborhood(connection, [], []), [])
            finally:
                connection.close()

    def test_two_hop_rows_survive_a_wide_seed(self):
        # The reserve exists because a 2-hop weight is a product of two factors
        # below 1, so a seed with more direct links than the limit would otherwise
        # crowd every 2-hop row out of the answer entirely.
        with tempfile.TemporaryDirectory() as temp:
            notes = {"seed.md": "## s\nbody\n", "far.md": "## f\nbody\n",
                     "near.md": "## n\nbody\n"}
            database = build_vault(Path(temp) / "vault", notes)
            edges = [("seed.md", f"wide-{index}.md") for index in range(40)]
            edges += [("seed.md", "near.md"), ("near.md", "far.md")]
            write_edges(database, edges)
            connection = dual_track.connect(database)
            try:
                rows = dual_track.graph_neighborhood(connection, ["seed.md"], [], hops=2)
            finally:
                connection.close()
            self.assertIn("far.md", {row["path"] for row in rows})


class SeedWideningTest(unittest.TestCase):
    """The best-coverage note is a dead end; something below it is not.

    Measured on the real vault: the query this module was built for seeded exactly
    one 4/5 note whose every wikilink pointed at a script or a person and so
    resolved to nothing, and the graph section rendered empty while a 2/5 note two
    rows down sat there with a live neighbourhood.
    """

    def vault(self, temp: str) -> Path:
        notes = {
            # 3/3 coverage and no outbound edges at all -- the dead end.
            "top.md": "## Body\nalpha beta gamma together\n",
            # 2/3 coverage, and it can actually be walked from.
            "mid.md": "## Body\nalpha beta only\n",
            # 1/3 coverage, also walkable, and must never be seeded for a
            # multi-facet query -- this is the note that answered a question about
            # stroke with three notes about wifi passwords.
            "weak.md": "## Body\nalpha by itself\n",
            "wanted.md": "## Body\nunrelated vocabulary\n",
            "unwanted.md": "## Body\nunrelated vocabulary\n",
        }
        database = build_vault(Path(temp) / "vault", notes)
        write_edges(database, [("mid.md", "wanted.md"), ("weak.md", "unwanted.md")])
        return database

    def test_widens_past_a_dead_end_best_tier(self):
        with tempfile.TemporaryDirectory() as temp:
            database = self.vault(temp)
            parsed = parse_query_facets("alpha beta gamma")
            payload = dual_track.structural_search(database, parsed, hops=2)
            self.assertEqual(payload["facets"][0]["path"], "top.md",
                             "3/3 coverage still has to rank first")
            reached = {row["path"] for row in payload["graph"]}
            self.assertIn("wanted.md", reached,
                          "the 2/3 note is walkable and the 3/3 note is not")

    def test_widening_never_seeds_a_single_facet_match(self):
        with tempfile.TemporaryDirectory() as temp:
            database = self.vault(temp)
            parsed = parse_query_facets("alpha beta gamma")
            payload = dual_track.structural_search(database, parsed, hops=2)
            reached = {row["path"] for row in payload["graph"]}
            self.assertNotIn("unwanted.md", reached,
                             "1/3 coverage is below the floor; its neighbours are noise")

    def test_stays_silent_when_nothing_above_the_floor_can_be_walked(self):
        with tempfile.TemporaryDirectory() as temp:
            notes = {
                "top.md": "## Body\nalpha beta gamma together\n",
                "weak.md": "## Body\nalpha by itself\n",
                "unwanted.md": "## Body\nunrelated vocabulary\n",
            }
            database = build_vault(Path(temp) / "vault", notes)
            write_edges(database, [("weak.md", "unwanted.md")])
            parsed = parse_query_facets("alpha beta gamma")
            payload = dual_track.structural_search(database, parsed, hops=2)
            self.assertEqual(payload["graph"], [],
                             "an empty section is the honest answer, not a wrong one")

    def test_single_facet_query_may_widen_within_its_own_tier(self):
        with tempfile.TemporaryDirectory() as temp:
            database = self.vault(temp)
            # Every match is 1/1 here, so the floor is that tier and widening is
            # only buying more attempts -- which is the point when the first seed
            # picked happens to be the one with no edges.
            parsed = parse_query_facets("alpha")
            payload = dual_track.structural_search(database, parsed, hops=2)
            reached = {row["path"] for row in payload["graph"]}
            self.assertTrue(reached & {"wanted.md", "unwanted.md"},
                            "a single-facet query has no weaker tier to exclude")


class FusionTest(unittest.TestCase):
    def test_agreement_beats_a_single_strong_rank(self):
        fused = dual_track.reciprocal_rank_fusion(["a.md", "b.md"], ["b.md", "a.md"])
        # Both appear in both, so both get the same pair of ranks.
        self.assertAlmostEqual(fused["a.md"], fused["b.md"])
        fused = dual_track.reciprocal_rank_fusion(["a.md"], ["a.md"], ["z.md"])
        self.assertGreater(fused["a.md"], fused["z.md"])

    def test_missing_from_a_track_contributes_nothing(self):
        fused = dual_track.reciprocal_rank_fusion(["only.md"], [])
        self.assertAlmostEqual(fused["only.md"], 1.0 / (dual_track.RRF_K + 1))

    def test_a_weighted_track_contributes_less(self):
        full = dual_track.reciprocal_rank_fusion(["a.md"], ["b.md"])
        self.assertAlmostEqual(full["a.md"], full["b.md"])
        half = dual_track.reciprocal_rank_fusion(["a.md"], ["b.md"], weights=[1.0, 0.5])
        self.assertAlmostEqual(half["b.md"], half["a.md"] / 2)

    def test_default_weights_are_still_one_each(self):
        # The signature grew a parameter; callers that do not pass it must be
        # unaffected, because searchd.rank fuses with this too.
        self.assertAlmostEqual(
            dual_track.reciprocal_rank_fusion(["a.md"], ["a.md"])["a.md"],
            2.0 / (dual_track.RRF_K + 1))

    def test_stratify_falls_back_when_one_hop_is_all_there_is(self):
        graph = [{"hop": 1, "path": f"{index}.md"} for index in range(6)]
        self.assertEqual(len(dual_track.stratify_hops(graph, 5)), 5)
        self.assertEqual(dual_track.stratify_hops(graph, 0), [])


class CorrelatedEvidenceTest(unittest.TestCase):
    """A graph neighbour must not outrank a better-covered note by voting twice.

    The graph is seeded from the facet winners, so a weak facet match that also
    sits next to one is agreeing with itself. Before the fix that double vote beat
    the top-coverage note outright and headed the outline with it.
    """

    def fixture(self, temp):
        notes = {
            # Three facets, and no links at all -- one vote, and it must still win.
            "best.md": "## A\nstroke\n\n## B\nfatigue\n\n## C\ndopamine\n",
            # One facet, but adjacent to the seed, so it used to collect two.
            "weak.md": "## A\nstroke only here\n",
            "hub.md": "## H\nstroke\n",
        }
        database = build_vault(Path(temp) / "vault", notes)
        # weak.md is reachable from the seed, which is what gives it a graph vote.
        write_edges(database, [("best.md", "weak.md"), ("weak.md", "hub.md")])
        return database

    def test_top_coverage_note_heads_the_fused_answer(self):
        with tempfile.TemporaryDirectory() as temp:
            database = self.fixture(temp)
            payload = dual_track.dual_track_search(
                database, "stroke fatigue dopamine", top=5)
            coverage = {row["path"]: row["coverage"] for row in payload["structural"]}
            self.assertEqual(coverage["best.md"], 3)
            self.assertEqual(payload["fused"][0]["path"], "best.md",
                             f"a weaker note outranked 3/3 coverage: {payload['fused']}")

    def test_a_facet_match_gets_no_second_vote_from_the_graph(self):
        with tempfile.TemporaryDirectory() as temp:
            database = self.fixture(temp)
            payload = dual_track.dual_track_search(
                database, "stroke fatigue dopamine", top=10)
            facets = {row["path"] for row in payload["structural"]}
            fused = {row["path"]: row["score"] for row in payload["fused"]}
            for row in payload["graph"]:
                if row["path"] in facets and row["path"] in fused:
                    # Its score must be explicable by its facet rank alone.
                    rank = [r["path"] for r in payload["structural"]].index(row["path"])
                    self.assertAlmostEqual(
                        fused[row["path"]], 1.0 / (dual_track.RRF_K + rank + 1),
                        msg=f"{row['path']} was counted by both tracks")

    def test_the_graph_still_carries_notes_the_facets_missed(self):
        # Narrowing what the graph may vote on must not silence it: a note with no
        # facet match at all is the only thing the walk is for.
        with tempfile.TemporaryDirectory() as temp:
            database = build_vault(Path(temp) / "vault", {
                "seed.md": "## A\nstroke\n\n## B\nfatigue\n",
                "neighbour.md": "## N\nnothing in common with the query\n",
            })
            write_edges(database, [("seed.md", "neighbour.md")])
            payload = dual_track.dual_track_search(database, "stroke fatigue", top=5)
            self.assertIn("neighbour.md", {row["path"] for row in payload["fused"]})


class OutlineThriftTest(unittest.TestCase):
    """Two things the outline used to spend tokens on and get nothing for."""

    def test_a_heading_that_repeats_the_note_name_is_not_printed(self):
        with tempfile.TemporaryDirectory() as temp:
            database = build_vault(Path(temp) / "vault", {
                # The atomic-note shape: the only heading is the title.
                "stroke recovery.md": "## stroke recovery\nfatigue and dopamine\n",
            })
            payload = dual_track.dual_track_search(
                database, "stroke recovery fatigue", top=5)
            outline = dual_track.render_outline(payload)
            self.assertIn("stroke recovery.md", outline)
            self.assertNotIn("└─ L1: stroke recovery", outline)

    def test_a_heading_that_differs_is_still_printed(self):
        with tempfile.TemporaryDirectory() as temp:
            database = build_vault(Path(temp) / "vault", {
                "notes.md": "## Fatigue milestones\nstroke and fatigue\n",
            })
            outline = dual_track.render_outline(
                dual_track.dual_track_search(database, "stroke fatigue", top=5))
            self.assertIn("Fatigue milestones", outline)

    def test_a_multi_chunk_section_reports_its_whole_extent(self):
        # A long section is stored as several rows sharing a heading. Ending the
        # range at the next chunk would hand back part of a section, so the range
        # must run to the next *different* heading.
        with tempfile.TemporaryDirectory() as temp:
            body = "\n".join(f"line {n} stroke and fatigue" for n in range(1, 60))
            database = build_vault(Path(temp) / "vault", {
                "long.md": f"## Big\n{body}\n\n## After\ntail\n",
            })
            payload = dual_track.dual_track_search(database, "stroke fatigue", top=5)
            headings = payload["structural"][0]["headings"]
            big = [h for h in headings if h["heading"] == "Big"]
            self.assertTrue(big, f"no Big heading in {headings}")
            after_start = 2 + len(body.splitlines()) + 1
            self.assertEqual(big[0]["end_line"], after_start - 1,
                             "the range stopped at a chunk boundary, not the section")

    def test_neighbours_of_one_seed_name_it_once(self):
        with tempfile.TemporaryDirectory() as temp:
            database = build_vault(Path(temp) / "vault", {
                "seed.md": "## A\nstroke\n\n## B\nfatigue\n",
                "one.md": "## N\nunrelated\n",
                "two.md": "## N\nunrelated\n",
                "three.md": "## N\nunrelated\n",
            })
            write_edges(database, [("seed.md", "one.md"), ("seed.md", "two.md"),
                                   ("seed.md", "three.md")])
            outline = dual_track.render_outline(
                dual_track.dual_track_search(database, "stroke fatigue", top=5))
            self.assertEqual(outline.count("seed ("), 1,
                             f"the seed was named more than once:\n{outline}")
            for name in ("one.md", "two.md", "three.md"):
                self.assertIn(name, outline)


class SemanticGateTest(unittest.TestCase):
    def semantic(self, _query):
        self.called = True
        return [{"path": "semantic.md", "heading": "S", "line": 1,
                 "score": 0.9, "text": "a body"}]

    def setUp(self):
        self.called = False

    def build(self, temp):
        return build_vault(Path(temp) / "vault", {
            "facets.md": "## F\nstroke and fatigue and dopamine\n",
            "semantic.md": "## S\nunrelated words entirely\n",
        })

    def test_a_multi_facet_query_does_not_pay_for_the_embedding(self):
        with tempfile.TemporaryDirectory() as temp:
            payload = dual_track.dual_track_search(
                self.build(temp), "stroke fatigue dopamine",
                semantic=self.semantic, top=5)
            self.assertFalse(self.called, "the gated track was still called")
            self.assertTrue(payload["semantic_skipped"])
            self.assertEqual(payload["semantic"], [])
            # And the largest block of the outline goes with it.
            self.assertNotIn("Semantic Best Match", dual_track.render_outline(payload))

    def test_a_single_facet_query_still_runs_it(self):
        with tempfile.TemporaryDirectory() as temp:
            payload = dual_track.dual_track_search(
                self.build(temp), "stroke", semantic=self.semantic, top=5)
            self.assertTrue(self.called, "a one-facet query has no coverage signal "
                                        "to rank on and needs the embedding")
            self.assertFalse(payload["semantic_skipped"])

    def test_the_gate_is_at_the_documented_facet_count(self):
        self.assertEqual(dual_track.SEMANTIC_GATE_FACETS, 2)

    def test_no_semantic_track_is_not_reported_as_gated(self):
        with tempfile.TemporaryDirectory() as temp:
            payload = dual_track.dual_track_search(
                self.build(temp), "stroke fatigue dopamine", top=5)
            self.assertFalse(payload["semantic_skipped"],
                             "nothing was skipped; there was nothing to skip")


class EndToEndTest(unittest.TestCase):
    def test_outline_is_compact_and_names_lines(self):
        with tempfile.TemporaryDirectory() as temp:
            database = build_vault(Path(temp) / "vault", {
                "patterns.md": (
                    "## Physical fatigue\nControlling for post stroke fatigue.\n\n"
                    "## The core\nhyperfocus, dopamine and sensation gating\n\n"
                    "## Tooling\nlong coding sessions\n"
                ),
                "goals.md": "## Rabbit holes\nhyperfocus rabbit holes versus goals\n",
            })
            payload = dual_track.dual_track_search(
                database, "stroke fatigue dopamine coding hyperfocus", top=5)
            self.assertEqual(payload["facet_count"], 5)
            outline = dual_track.render_outline(payload)
            self.assertIn("Facet Intersections", outline)
            self.assertIn("patterns.md", outline)
            # A range, not a bare line: the point is that a follow-up read can be
            # bounded. `L7+` is the last section in a note -- read to EOF.
            self.assertRegex(outline, r"L\d+(-\d+|\+):")
            self.assertIn("L1-3: Physical fatigue", outline)
            self.assertIn("L7+: Tooling", outline)
            # The token budget the whole mode is for. ~4 chars per token is the
            # usual rule of thumb, so 250 tokens is about 1000 characters.
            self.assertLess(len(outline), 1000, f"outline too long:\n{outline}")
            self.assertNotIn("Controlling for post stroke fatigue", outline,
                             "the outline must never carry section bodies")

    def test_injected_semantic_track_is_fused_in(self):
        with tempfile.TemporaryDirectory() as temp:
            database = build_vault(Path(temp) / "vault", {
                "only-semantic.md": "## S\nnothing lexical in common\n",
                "facets.md": "## F\nstroke and fatigue\n",
            })
            # gate_semantic=False because "stroke fatigue" is two facets and would
            # otherwise be gated; what this test is about is that an injected track
            # reaches the fusion at all.
            payload = dual_track.dual_track_search(
                database, "stroke fatigue",
                semantic=lambda query: [{"path": "only-semantic.md", "heading": "S",
                                         "line": 1, "score": 0.9, "text": "a body"}],
                top=5, gate_semantic=False)
            paths = {row["path"] for row in payload["fused"]}
            self.assertIn("only-semantic.md", paths)
            self.assertIn("facets.md", paths)
            self.assertIn("Semantic Best Match", dual_track.render_outline(payload))
            self.assertFalse(payload["semantic_skipped"])

    def test_a_failing_semantic_track_does_not_lose_the_answer(self):
        with tempfile.TemporaryDirectory() as temp:
            database = build_vault(Path(temp) / "vault", {
                "facets.md": "## F\nstroke and fatigue\n",
            })

            def broken(_query):
                raise RuntimeError("no model here")

            payload = dual_track.dual_track_search(
                database, "stroke fatigue", semantic=broken, top=5)
            self.assertIn("facets.md", {row["path"] for row in payload["fused"]})

    def test_facet_override_replaces_clustering(self):
        with tempfile.TemporaryDirectory() as temp:
            database = build_vault(Path(temp) / "vault", {
                "note.md": "## A\nstroke\n\n## B\ncoding\n",
            })
            payload = dual_track.dual_track_search(
                database, "ignored query text", facets=["stroke", "coding"], top=5)
            self.assertEqual(payload["facet_count"], 2)
            self.assertEqual(payload["structural"][0]["coverage"], 2)

    def test_performance_gate(self):
        with tempfile.TemporaryDirectory() as temp:
            notes = {f"note-{index}.md": (
                f"## Fatigue {index}\npost stroke fatigue and dopamine\n\n"
                f"## Coding {index}\nhyperfocus during long coding sessions\n"
            ) for index in range(40)}
            database = build_vault(Path(temp) / "vault", notes)
            edges = [(f"note-{index}.md", f"note-{index + 1}.md") for index in range(39)]
            write_edges(database, edges)
            parsed = parse_query_facets("stroke fatigue dopamine coding hyperfocus", database)
            # Warm the page cache, then measure. A cold first query measures SQLite
            # opening the file, which is not what the gate is about.
            dual_track.structural_search(database, parsed)
            began = time.perf_counter()
            dual_track.structural_search(database, parsed)
            elapsed = (time.perf_counter() - began) * 1000
            self.assertLess(elapsed, 30.0, f"structural search too slow: {elapsed:.1f}ms")

    def test_json_serialisable_for_the_daemon_wire(self):
        import json

        with tempfile.TemporaryDirectory() as temp:
            database = build_vault(Path(temp) / "vault", {
                "note.md": "## A\nstroke and fatigue\n",
            })
            payload = dual_track.dual_track_search(database, "stroke fatigue", top=5)
            json.dumps({"outlines": {"vault": dual_track.render_outline(payload)},
                        "results": payload["fused"],
                        "structural": payload["structural"]})


class ReciprocalRankFusionTest(unittest.TestCase):
    def test_repeated_path_in_one_ranking_counts_once_at_best_rank(self):
        # A path appearing at positions 0, 5, 10 should score as if it appeared
        # only at position 0, which is weight / (k + 0 + 1).
        ranking = ["A.md", "B.md", "C.md", "A.md", "D.md", "A.md"]
        scores = dual_track.reciprocal_rank_fusion(ranking, k=60, weights=[1.0])
        # Best rank for A.md is 0, so score = 1.0 / (60 + 0 + 1) = 1/61
        expected_score = 1.0 / 61
        self.assertAlmostEqual(scores["A.md"], expected_score, places=6)
        # B.md appears once at rank 1, so score = 1.0 / (60 + 1 + 1) = 1/62
        self.assertAlmostEqual(scores["B.md"], 1.0 / 62, places=6)

    def test_same_path_in_different_rankings_accumulates(self):
        # A.md appears in both rankings. It should get contributions from both.
        ranking1 = ["A.md", "B.md"]
        ranking2 = ["C.md", "A.md"]
        scores = dual_track.reciprocal_rank_fusion(ranking1, ranking2, k=60,
                                                  weights=[1.0, 1.0])
        # A.md: rank 0 in ranking1 (1/61) + rank 1 in ranking2 (1/62)
        expected = (1.0 / 61) + (1.0 / 62)
        self.assertAlmostEqual(scores["A.md"], expected, places=6)

    def test_dual_track_search_with_repeated_semantic_rows(self):
        # A note with multiple matching sections should not outrank a note with
        # a single better-placed section.
        with tempfile.TemporaryDirectory() as temp:
            database = build_vault(Path(temp) / "vault", {
                "multi-section.md": (
                    "## Section 1\nstroke recovery\n\n"
                    "## Section 2\nstroke and fatigue\n\n"
                    "## Section 3\npost stroke exercise\n"
                ),
                "single-section.md": "## Best\nstroke dopamine pathway\n",
            })

            # Mock semantic callable that returns three rows for multi-section.md
            # and one row for single-section.md. The semantic parameter is a callable
            # that takes just the query string.
            def mock_semantic(query):
                return [
                    {"path": "single-section.md", "heading": "Best", "line": 1,
                     "score": 0.95, "section_id": "s1"},
                    {"path": "multi-section.md", "heading": "Section 1", "line": 1,
                     "score": 0.70, "section_id": "s2"},
                    {"path": "multi-section.md", "heading": "Section 2", "line": 3,
                     "score": 0.68, "section_id": "s3"},
                    {"path": "multi-section.md", "heading": "Section 3", "line": 5,
                     "score": 0.65, "section_id": "s4"},
                ]

            result = dual_track.dual_track_search(database, "stroke", semantic=mock_semantic,
                                                 top=10)
            fused_order = [row["path"] for row in result["fused"]]

            # Asserted unconditionally. Guarding the comparison behind "if both are
            # in the results" makes the test pass without comparing anything the
            # moment either note drops out, which is the failure it exists to catch.
            self.assertIn("single-section.md", fused_order, fused_order)
            self.assertIn("multi-section.md", fused_order, fused_order)
            self.assertLess(fused_order.index("single-section.md"),
                            fused_order.index("multi-section.md"),
                            f"the note ranked first on one section must beat the note "
                            f"that only appears three times lower down: {fused_order}")


if __name__ == "__main__":
    unittest.main()
