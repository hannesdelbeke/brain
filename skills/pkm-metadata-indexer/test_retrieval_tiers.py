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


class CorpusFloorTest(unittest.TestCase):
    """One slot per corpus that has a real answer, so a big corpus cannot sweep."""

    @staticmethod
    def rows(*pairs):
        return [{"vault": vault, "path": f"{vault}{index}.md", "score": 0.02,
                 "rerank_score": logit}
                for index, (vault, logit) in enumerate(pairs)]

    def test_a_buried_answer_from_another_corpus_is_pulled_into_the_last_slot(self):
        rows = self.rows(("traces", 7.0), ("traces", 6.0), ("traces", 5.0),
                         ("notes", 1.5))
        kept = SEARCHD.apply_corpus_floor(rows, 3)
        self.assertEqual([row["vault"] for row in kept], ["traces", "traces", "notes"])

    def test_survivors_stay_in_score_order_so_the_cutoff_still_reads(self):
        rows = self.rows(("traces", 7.0), ("traces", 6.0), ("notes", 1.5))
        kept = SEARCHD.apply_corpus_floor(rows, 2)
        self.assertEqual([row["rerank_score"] for row in kept], [7.0, 1.5])

    def test_a_corpus_below_the_answer_bar_is_given_nothing(self):
        """The floor keeps a real answer visible. It never promotes noise."""
        rows = self.rows(("traces", 7.0), ("traces", 6.0), ("notes", -8.0))
        kept = SEARCHD.apply_corpus_floor(rows, 2)
        self.assertEqual([row["vault"] for row in kept], ["traces", "traces"])

    def test_without_a_rerank_it_does_nothing_but_truncate(self):
        """Fused scores tie every corpus's rank-1 row, so the merge is already fair."""
        rows = [{"vault": "traces", "path": "a.md", "score": 0.03},
                {"vault": "traces", "path": "b.md", "score": 0.02},
                {"vault": "notes", "path": "c.md", "score": 0.01}]
        self.assertEqual(SEARCHD.apply_corpus_floor(rows, 2), rows[:2])

    def test_one_corpus_alone_is_unchanged(self):
        rows = self.rows(("notes", 7.0), ("notes", 6.0), ("notes", 5.0))
        self.assertEqual(SEARCHD.apply_corpus_floor(rows, 2), rows[:2])

    def test_more_answering_corpora_than_slots_takes_the_best_of_them(self):
        rows = self.rows(("a", 7.0), ("b", 6.0), ("c", 5.0))
        kept = SEARCHD.apply_corpus_floor(rows, 2)
        self.assertEqual([row["vault"] for row in kept], ["a", "b"])


class IndexStatusTest(unittest.TestCase):
    """Why a corpus is empty, which is the difference between normal and broken."""

    def setUp(self):
        self.db = Path(__file__).with_name("test_status_scratch.db")
        self.db.unlink(missing_ok=True)
        self.connection = sqlite3.connect(self.db)
        self.connection.executescript(
            """
            CREATE TABLE index_runs (id INTEGER PRIMARY KEY, completed_at TEXT);
            CREATE TABLE index_errors (run_id INTEGER, path TEXT, stage TEXT, message TEXT);
            INSERT INTO index_runs (id, completed_at) VALUES (1, '2026-09-20'), (2, '2026-09-21');
            """
        )
        self.connection.commit()

    def tearDown(self):
        self.connection.close()
        self.db.unlink(missing_ok=True)

    def add(self, run_id, stage, message):
        self.connection.execute(
            "INSERT INTO index_errors (run_id, path, stage, message) VALUES (?, '', ?, ?)",
            (run_id, stage, message))
        self.connection.commit()

    def test_the_reason_a_corpus_is_empty_survives_to_the_reader(self):
        self.add(2, "status", "no remote refs besides origin/main and origin/HEAD")
        self.assertEqual(PKM.last_index_status(self.db),
                         ["no remote refs besides origin/main and origin/HEAD"])

    def test_only_the_latest_run_is_reported(self):
        """A stale reason is worse than none: it describes a state that has passed."""
        self.add(1, "status", "not a git repository")
        self.add(2, "status", "no default branch (main/master) found")
        self.assertEqual(PKM.last_index_status(self.db),
                         ["no default branch (main/master) found"])

    def test_a_parse_failure_is_an_error_not_a_status(self):
        self.add(2, "parse", "could not read note.md")
        self.assertEqual(PKM.last_index_status(self.db), [])

    def test_a_missing_database_is_silent_rather_than_a_crash(self):
        self.assertEqual(PKM.last_index_status(self.db.with_name("absent.db")), [])


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


HOUSE_FORMAT = """> [!summary] eli5
> The daemon answers in 100ms without rerank and 3.6s with it.
> **needs from you:** whether to default rerank off.

> make search faster

**why:** [[retrieval]]

The cross-encoder is the whole of the difference. Everything else is noise.
"""


class SummarySnippetTest(unittest.TestCase):
    """Why the notes written to the house format were the ones with no snippet.

    The snippet is what a caller reads instead of the note, so a note with an
    empty one is a note that has to be opened to be judged. Headings and
    bullets were the only thing being read, and the house format opens with a
    callout and a blockquote -- so the 60%-populated corpus was the handwritten
    one and the 97% was the machine-written one, which is backwards.
    """

    def test_the_summary_callout_is_the_snippet(self):
        snippet = PKM.extract_key_lines(HOUSE_FORMAT)
        self.assertIn("The daemon answers in 100ms", snippet)
        self.assertIn("needs from you", snippet)

    def test_the_summary_comes_before_the_headings(self):
        body = "## a heading\n\n> [!summary] eli5\n> the finding\n"
        self.assertTrue(PKM.extract_key_lines(body).startswith("summary: the finding"))

    def test_the_prompt_blockquote_is_not_mistaken_for_a_callout(self):
        """A bare `>` quote is the prompt, not a summary; only `[!type]` opens one."""
        self.assertEqual(dict(PKM.iter_callouts("> just a quote\n> more quote\n")), {})

    def test_a_note_with_only_prose_still_gets_a_snippet(self):
        """The fallback that makes an empty snippet mean an empty note."""
        snippet = PKM.extract_key_lines("Bufferbloat is queueing delay under load.\n")
        self.assertEqual(snippet, "Bufferbloat is queueing delay under load.")

    def test_prose_is_a_last_resort_not_a_first_one(self):
        body = "some prose first\n\n## the heading\n"
        self.assertEqual(PKM.extract_key_lines(body), "## the heading")

    def test_headings_and_bullets_still_work_unchanged(self):
        """Machine-written notes were already at 97%; this must not move them."""
        body = "## outcome\n- shipped the dedupe\n- [ ] land the branch\n"
        self.assertEqual(PKM.extract_key_lines(body),
                         "## outcome\n- shipped the dedupe\n- [ ] land the branch")

    def test_rules_and_fences_never_become_a_snippet(self):
        self.assertEqual(PKM.extract_key_lines("---\n\n***\n\n```\n```\n"), "")

    def test_a_note_of_only_links_is_summarised_by_its_links(self):
        """323 measured stubs whose body is a column of wikilinks and nothing else.

        The links are the only thing such a note says. Dropping them left the
        caller a filename and no way to tell what it relates to but a read.
        """
        body = "[[second brain]]\n[[knowledge]]\n[[knowledge graph]]\n"
        self.assertEqual(PKM.extract_key_lines(body),
                         "second brain, knowledge, knowledge graph")

    def test_a_link_alias_is_reduced_to_its_target(self):
        self.assertEqual(PKM.extract_key_lines("[[AWS Lambda function|Lambda function]]\n"),
                         "AWS Lambda function")

    def test_links_are_a_last_resort_behind_every_other_source(self):
        body = "[[a note]]\n\nThe finding is that the sign is the boundary.\n"
        self.assertEqual(PKM.extract_key_lines(body),
                         "The finding is that the sign is the boundary.")

    def test_a_one_line_callout_falls_back_to_its_title(self):
        self.assertEqual(PKM.extract_key_lines("> [!summary] the whole finding\n"),
                         "summary: the whole finding")

    def test_a_todo_callout_is_taken_when_there_is_no_summary(self):
        body = "> [!todo] next\n> **next:** land the branch\n"
        self.assertIn("land the branch", PKM.extract_key_lines(body))

    def test_the_line_cap_still_holds(self):
        body = "\n".join(f"- item {index}" for index in range(40))
        self.assertEqual(len(PKM.extract_key_lines(body).splitlines()), 15)

    def test_a_long_line_is_truncated(self):
        snippet = PKM.extract_key_lines("- " + "x" * 400)
        self.assertTrue(snippet.endswith("..."))
        self.assertLessEqual(len(snippet), 203)

    def test_the_whole_snippet_is_capped_not_just_each_line(self):
        """Fifteen 200-char lines is 3k of snippet on a payload sold as cheap."""
        body = "\n".join("- " + "x" * 190 for _ in range(15))
        self.assertLessEqual(len(PKM.extract_key_lines(body)), 603)

    def test_an_empty_note_is_the_only_empty_snippet(self):
        self.assertEqual(PKM.extract_key_lines(""), "")

    def test_any_callout_beats_no_snippet_at_all(self):
        """Measured: notes whose only structure was a `[!note]` block came back blank."""
        body = "> [!NOTE]- Power outlet\n> suitable for accessories up to 12A\n"
        self.assertEqual(PKM.extract_key_lines(body),
                         "note: suitable for accessories up to 12A")

    def test_a_note_that_is_only_a_table_gets_its_rows(self):
        body = "| Name | Dose |\n| ---- | ---- |\n| Ginkgo Biloba | 6000mg |\n"
        snippet = PKM.extract_key_lines(body)
        self.assertIn("Ginkgo Biloba 6000mg", snippet)
        # The separator row is punctuation, not content.
        self.assertNotIn("----", snippet)

    def test_a_note_that_is_only_a_quote_gets_the_quote(self):
        body = "> In 2016 a group of scientists began wondering the same thing.\n"
        self.assertEqual(PKM.extract_key_lines(body),
                         "In 2016 a group of scientists began wondering the same thing.")

    def test_a_definition_opening_in_bold_is_prose_not_a_bullet(self):
        """Measured: 44 glossary notes came back blank because `**` is not `* `."""
        body = "**AWS Regions** -- separate geographic areas that AWS uses.\n"
        self.assertEqual(PKM.extract_key_lines(body),
                         "**AWS Regions** -- separate geographic areas that AWS uses.")

    def test_a_starred_bullet_is_a_bullet_and_is_still_collected(self):
        """`* ` is a list in Markdown too, and it must not fall through to prose."""
        self.assertEqual(PKM.extract_key_lines("* starred item\n"), "* starred item")

    def test_a_summary_callout_still_outranks_a_note_callout(self):
        body = "> [!note] aside\n> the aside\n\n> [!summary] eli5\n> the finding\n"
        self.assertEqual(PKM.extract_key_lines(body), "summary: the finding")


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
