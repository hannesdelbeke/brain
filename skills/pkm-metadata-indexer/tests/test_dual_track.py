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

    def test_stratify_falls_back_when_one_hop_is_all_there_is(self):
        graph = [{"hop": 1, "path": f"{index}.md"} for index in range(6)]
        self.assertEqual(len(dual_track.stratify_hops(graph, 5)), 5)
        self.assertEqual(dual_track.stratify_hops(graph, 0), [])


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
            self.assertRegex(outline, r"L\d+:")
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
            payload = dual_track.dual_track_search(
                database, "stroke fatigue",
                semantic=lambda query: [{"path": "only-semantic.md", "heading": "S",
                                         "line": 1, "score": 0.9, "text": "a body"}],
                top=5)
            paths = {row["path"] for row in payload["fused"]}
            self.assertIn("only-semantic.md", paths)
            self.assertIn("facets.md", paths)
            self.assertIn("Semantic Best Match", dual_track.render_outline(payload))

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


if __name__ == "__main__":
    unittest.main()
