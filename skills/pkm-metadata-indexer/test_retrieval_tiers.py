"""The tier-2 payload, the per-note dedupe and the stop-reading signal.

These three exist to stop a caller reading notes it did not need: the section
text lets it judge a result without opening the note, the dedupe stops one note
filling several slots, and the cutoff says where the answers stop. Each is
cheap to get subtly wrong in a way no other test would catch, because the
search still returns plausible results either way.
"""
import importlib.util
import io
import contextlib
import sqlite3
import unittest
from pathlib import Path


def load(name: str):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).with_name(f"{name}.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


SEARCH_VAULT = load("search_vault")
SEARCHD = load("searchd")
PKM = load("index_pkm_meta")


def reranked(*logits: float) -> list[dict]:
    """Results as the cross-encoder leaves them: sorted, carrying both scores."""
    return [{"path": f"n{index}.md", "heading": "h", "line": 1,
             "score": 0.02, "rerank_score": logit}
            for index, logit in enumerate(logits)]


class AttachSectionTextTest(unittest.TestCase):
    """The text of the matching section, which is the whole of tier 2."""

    def setUp(self):
        self.connection = sqlite3.connect(":memory:")
        self.connection.execute(
            "CREATE VIRTUAL TABLE sections_fts USING fts5(section_id, content)")
        self.cursor = self.connection.cursor()

    def tearDown(self):
        self.connection.close()

    def store(self, section_id: str, content: str):
        self.cursor.execute("INSERT INTO sections_fts VALUES (?, ?)", (section_id, content))

    def test_attaches_the_section_that_matched(self):
        self.store("s1", "the classifier fails closed under concurrency")
        results = PKM.attach_section_text([{"section_id": "s1"}], self.cursor)
        self.assertEqual(results[0]["text"], "the classifier fails closed under concurrency")

    def test_truncates_on_a_word_boundary_and_says_so(self):
        self.store("s1", "word " * 400)
        results = PKM.attach_section_text([{"section_id": "s1"}], self.cursor, max_chars=50)
        text = results[0]["text"]
        self.assertTrue(text.endswith(" ..."))
        # The marker is allowed past the limit; the text it marks is not.
        self.assertLessEqual(len(text.removesuffix(" ...")), 50)
        self.assertNotIn("wor ...", text)

    def test_collapses_whitespace_so_a_result_stays_one_block(self):
        self.store("s1", "a line\n\n   and   another\tone")
        results = PKM.attach_section_text([{"section_id": "s1"}], self.cursor)
        self.assertEqual(results[0]["text"], "a line and another one")

    def test_missing_section_gives_empty_text_rather_than_raising(self):
        results = PKM.attach_section_text([{"section_id": "gone"}], self.cursor)
        self.assertEqual(results[0]["text"], "")

    def test_no_section_ids_is_left_alone(self):
        self.assertEqual(PKM.attach_section_text([{"path": "n.md"}], self.cursor),
                         [{"path": "n.md"}])

    def test_one_query_serves_every_result(self):
        for index in range(5):
            self.store(f"s{index}", f"body {index}")
        rows = [{"section_id": f"s{index}"} for index in range(5)]
        before = self.connection.total_changes
        results = PKM.attach_section_text(rows, self.cursor)
        self.assertEqual([row["text"] for row in results],
                         [f"body {index}" for index in range(5)])
        self.assertEqual(self.connection.total_changes, before)


class DedupeByPathTest(unittest.TestCase):
    """Ranking is over sections, reading is over notes, so slots are per note."""

    def test_keeps_the_first_occurrence_which_is_the_best_one(self):
        rows = [{"path": "a.md", "score": 0.9}, {"path": "a.md", "score": 0.1},
                {"path": "b.md", "score": 0.5}]
        kept = SEARCHD.dedupe_by_path(rows)
        self.assertEqual([row["path"] for row in kept], ["a.md", "b.md"])
        self.assertEqual(kept[0]["score"], 0.9)

    def test_same_path_in_two_corpora_is_two_notes(self):
        rows = [{"vault": "notes", "path": "a.md"}, {"vault": "brain", "path": "a.md"}]
        self.assertEqual(len(SEARCHD.dedupe_by_path(rows)), 2)

    def test_order_is_otherwise_untouched(self):
        rows = [{"path": f"{name}.md"} for name in "cab"]
        self.assertEqual([row["path"] for row in SEARCHD.dedupe_by_path(rows)],
                         ["c.md", "a.md", "b.md"])

    def test_the_two_search_paths_agree(self):
        """A direct search must not look like a different search from a daemon hit."""
        rows = [{"path": "a.md"}, {"path": "a.md"}, {"path": "b.md"}]
        self.assertEqual(SEARCHD.dedupe_by_path([dict(row) for row in rows]),
                         SEARCH_VAULT.dedupe_by_path([dict(row) for row in rows]))


class CutoffTest(unittest.TestCase):
    """Where the answers stop, on the one score that means the same thing twice."""

    def test_nothing_above_the_boundary_means_read_none(self):
        cut, reason = SEARCH_VAULT.find_cutoff(reranked(-11.1, -11.2, -11.3))
        self.assertEqual(cut, 0)
        self.assertIn("nothing here answers this", reason)

    def test_one_weak_best_is_still_not_an_answer(self):
        """Measured: a query about a person not in the vault tops out at -3.12.

        The cliff is real and means nothing -- the best of eight non-answers is
        a non-answer, and a relative rule would have sent the caller to it.
        """
        cut, _ = SEARCH_VAULT.find_cutoff(reranked(-3.12, -9.87, -10.18))
        self.assertEqual(cut, 0)

    def test_all_above_the_boundary_means_no_boundary_to_report(self):
        """Measured on 'classifier timeout', where all eight were on topic.

        The widest neighbour gap sits between ranks 1 and 2 here, so any rule
        that hunts for a cliff cuts seven good answers.
        """
        cut, reason = SEARCH_VAULT.find_cutoff(
            reranked(6.877, 5.796, 5.718, 5.543, 5.168, 4.903, 4.537, 4.258))
        self.assertEqual(cut, 8)
        self.assertEqual(reason, "")

    def test_cut_lands_where_the_sign_changes(self):
        cut, reason = SEARCH_VAULT.find_cutoff(reranked(7.0, 1.5, -2.0, -3.0))
        self.assertEqual(cut, 2)
        self.assertIn("below 2", reason)

    def test_the_reported_percentages_straddle_the_boundary(self):
        """The message is only worth printing where the sigmoid is not saturated.

        Reporting '100% against 100%' was the symptom that the cut was being
        made in the wrong place, so the numbers either side must differ.
        """
        _, reason = SEARCH_VAULT.find_cutoff(reranked(5.0, -0.5, -4.0))
        self.assertIn("99%", reason)
        self.assertIn("38%", reason)

    def test_empty_results(self):
        self.assertEqual(SEARCH_VAULT.find_cutoff([]), (0, ""))

    def test_without_rerank_it_falls_back_to_the_fused_score(self):
        rows = [{"score": value} for value in (0.0328, 0.0300, 0.0290, 0.0120, 0.0110)]
        cut, reason = SEARCH_VAULT.find_cutoff(rows)
        self.assertEqual(cut, 3)
        self.assertIn("%", reason)

    def test_a_flat_fused_list_reports_that_it_is_flat(self):
        rows = [{"score": value} for value in (0.0328, 0.0320, 0.0315, 0.0310)]
        cut, reason = SEARCH_VAULT.find_cutoff(rows)
        self.assertEqual(cut, 4)
        self.assertIn("no clear cutoff", reason)

    def test_a_partial_rerank_is_not_treated_as_a_rerank(self):
        """One row without a logit makes the logits incomparable, so use the fusion."""
        rows = reranked(5.0, -1.0)
        del rows[1]["rerank_score"]
        cut, _ = SEARCH_VAULT.find_cutoff(rows)
        self.assertEqual(cut, len(rows))


class PrintResultsTest(unittest.TestCase):
    """What the caller actually sees, which is the only place the saving lands."""

    def render(self, results) -> str:
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            SEARCH_VAULT.print_results("q", "direct", results)
        return buffer.getvalue()

    def test_text_is_printed_above_the_cut_and_withheld_below_it(self):
        rows = reranked(7.0, -2.0)
        rows[0]["text"], rows[1]["text"] = "the answer", "not the answer"
        output = self.render(rows)
        self.assertIn("the answer", output)
        self.assertNotIn("not the answer", output)
        self.assertIn("stop here", output)

    def test_a_no_answer_query_warns_before_the_list_not_after_it(self):
        rows = reranked(-11.0, -11.2)
        for row in rows:
            row["text"] = "body"
        output = self.render(rows)
        self.assertIn("nothing here answers this", output)
        # A warning under the list arrives after the caller has read the list.
        self.assertLess(output.index("nothing here answers this"), output.index("n0.md"))
        self.assertNotIn("body", output)

    def test_the_printed_score_is_the_one_that_ordered_the_list(self):
        """Printing the fused score beside a rerank ordering read as a broken ranker."""
        rows = reranked(7.0, 6.0, 5.0)
        rows[0]["score"], rows[1]["score"], rows[2]["score"] = 0.025, 0.031, 0.029
        printed = [float(line.split("[")[1].split("]")[0])
                   for line in self.render(rows).splitlines() if "[" in line]
        self.assertEqual(printed, sorted(printed, reverse=True))

    def test_without_rerank_the_printed_score_is_the_fused_one(self):
        rows = [{"path": "a.md", "heading": "h", "line": 1, "score": 0.031}]
        self.assertIn("[0.031]", self.render(rows))


if __name__ == "__main__":
    unittest.main()
