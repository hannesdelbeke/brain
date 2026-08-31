import importlib.util
import subprocess
import tempfile
import unittest
from pathlib import Path


SCRIPT_PATH = Path(__file__).with_name("co_commit.py")
SPEC = importlib.util.spec_from_file_location("co_commit_module", SCRIPT_PATH)
CO_COMMIT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CO_COMMIT)


def run_git(repo: Path, *args: str):
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True)


class CoCommitGitHistoryTest(unittest.TestCase):
    """Exercises the real git-log-parsing path, which --selfcheck never touches."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.repo = Path(self.temp_dir.name) / "repo"
        self.repo.mkdir()
        run_git(self.repo, "init", "-q")
        run_git(self.repo, "config", "user.email", "t@t")
        run_git(self.repo, "config", "user.name", "t")
        self.db = Path(self.temp_dir.name) / "co_commit.db"

    def tearDown(self):
        self.temp_dir.cleanup()

    def commit_files(self, message: str, **files: str):
        for name, content in files.items():
            path = self.repo / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
        run_git(self.repo, "add", "-A")
        run_git(self.repo, "commit", "-q", "-m", message)

    def test_scan_git_commits_yields_only_multi_markdown_commits(self):
        self.commit_files("single file", **{"a.md": "one"})
        self.commit_files("two markdown files", **{"a.md": "two", "b.md": "b"})
        self.commit_files("markdown plus non-markdown", **{"a.md": "three", "notes.txt": "x"})
        commits = list(CO_COMMIT.scan_git_commits(self.repo))
        self.assertEqual(len(commits), 1, "only the 2-markdown-file commit qualifies")
        sha, date, msg, files = commits[0]
        self.assertEqual(msg, "two markdown files")
        self.assertEqual(sorted(files), ["a.md", "b.md"])

    def test_update_co_commits_incremental_matches_rebuild(self):
        self.commit_files("first pair", **{"a.md": "1", "b.md": "1"})
        result = CO_COMMIT.update_co_commits(self.db, self.repo, "v")
        self.assertEqual(result, (1, 1, 0))

        self.commit_files("second pair, same files again", **{"a.md": "2", "b.md": "2"})
        result = CO_COMMIT.update_co_commits(self.db, self.repo, "v")
        self.assertEqual(result, (1, 1, 0), "incremental run only sees the new commit")

        incremental_row = CO_COMMIT.heaviest_edges(self.db, "v", top=1)[0]
        self.assertEqual(incremental_row[4], 2, "commit_count accumulated across both runs")

        rebuilt_commits, rebuilt_edges, rebuilt_skipped = CO_COMMIT.update_co_commits(
            self.db, self.repo, "v", rebuild=True)
        self.assertEqual((rebuilt_commits, rebuilt_skipped), (2, 0))
        rebuilt_row = CO_COMMIT.heaviest_edges(self.db, "v", top=1)[0]
        self.assertEqual(rebuilt_row[3:5], incremental_row[3:5],
                         "a full rebuild must land on the same weight and count as the incremental runs")

    def test_bulk_commit_over_max_files_is_skipped(self):
        bulk = {f"n{i}.md": "x" for i in range(CO_COMMIT.MAX_COMMIT_FILES + 5)}
        self.commit_files("bulk import", **bulk)
        result = CO_COMMIT.update_co_commits(self.db, self.repo, "v")
        self.assertEqual(result, (1, 0, 1), "a bulk commit is counted but skipped, not pairwise-weighted")

    def test_checkpoint_invalid_after_history_rewrite_forces_full_rescan(self):
        self.commit_files("first", **{"a.md": "1", "b.md": "1"})
        CO_COMMIT.update_co_commits(self.db, self.repo, "v")
        run_git(self.repo, "commit", "--amend", "-q", "-m", "first (amended)")  # changes the sha
        result = CO_COMMIT.update_co_commits(self.db, self.repo, "v")
        self.assertEqual(result, (1, 1, 0))
        row = CO_COMMIT.heaviest_edges(self.db, "v", top=1)[0]
        self.assertEqual(row[4], 1, "a stale checkpoint must not double-count the rewritten commit")

    def test_hub_exclusion(self):
        self.commit_files("hub forms", **{"d.md": "1", "e.md": "1"})
        self.commit_files("hub forms", **{"d.md": "2", "f.md": "1"})
        self.commit_files("hub forms", **{"d.md": "3", "g.md": "1"})
        CO_COMMIT.update_co_commits(self.db, self.repo, "v")
        self.assertEqual(CO_COMMIT.hub_notes(self.db, "v", degree_threshold=2), {"d.md"})
        associated = {row[1] for row in CO_COMMIT.query_associations(
            self.db, "e.md", vault="v", top=5, exclude_hubs=True, hub_degree=2)}
        self.assertNotIn("d.md", associated)


class LiftRankingTest(unittest.TestCase):
    """rank_by="lift" (co_commit.py's new hub-handling default for a fresh
    standalone query, see query_associations's docstring), tested directly
    against a real sqlite fixture rather than through git-log parsing -
    same fixture-building style as CoCommitGitHistoryTest.setUp/commit_files,
    but the thing under test here is the scoring math, not the git plumbing,
    so rows are inserted straight into the co_commits table."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db = Path(self.temp_dir.name) / "co_commit.db"
        conn = CO_COMMIT.connect(self.db)
        with conn:
            # Q--H is the higher raw weight edge (10), but H also co-occurs
            # heavily with 4 other notes (total_weight(H)=50): a classic hub.
            # Q--R is the lower raw weight edge (3), but R co-occurs with
            # nothing else (total_weight(R)=3): fully explained by this one
            # pairing, so it is far more informative about Q specifically -
            # the same synthetic shape lift_cooccurrence_experiment.py's own
            # self_check() uses to prove lift inverts raw weight's ranking.
            conn.execute("INSERT INTO co_commits VALUES ('v', 'Q.md', 'H.md', 10.0, 1, '2026-08-31', 'a')")
            conn.execute("INSERT INTO co_commits VALUES ('v', 'Q.md', 'R.md', 3.0, 1, '2026-08-31', 'b')")
            conn.executemany(
                "INSERT INTO co_commits VALUES ('v', 'H.md', ?, 10.0, 1, '2026-08-31', 'c')",
                [("X1.md",), ("X2.md",), ("X3.md",), ("X4.md",)],
            )
        conn.close()  # Windows will not delete the temp dir with the file still open

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_lift_deprioritizes_hub_despite_higher_raw_weight(self):
        lift_order = [row[1] for row in CO_COMMIT.query_associations(
            self.db, "Q.md", vault="v", top=5, rank_by="lift")]
        self.assertLess(lift_order.index("R.md"), lift_order.index("H.md"),
                        "lift must rank the rare, fully-explained pairing (R) above the hub pairing (H)")

    def test_lift_mode_still_returns_raw_weight_in_the_weight_field(self):
        rows = {row[1]: row[2] for row in CO_COMMIT.query_associations(
            self.db, "Q.md", vault="v", top=5, rank_by="lift")}
        self.assertEqual(rows["H.md"], 10.0)
        self.assertEqual(rows["R.md"], 3.0)

    def test_old_raw_weight_path_still_works_unchanged(self):
        # rank_by="weight" is query_associations's own default (kept for
        # backward compatibility with searchd.py and eval_related.py, which
        # call this without rank_by) - explicit here or omitted must agree.
        explicit = [row[1] for row in CO_COMMIT.query_associations(
            self.db, "Q.md", vault="v", top=5, rank_by="weight")]
        default = [row[1] for row in CO_COMMIT.query_associations(
            self.db, "Q.md", vault="v", top=5)]
        self.assertEqual(explicit, default)
        self.assertLess(explicit.index("H.md"), explicit.index("R.md"),
                        "raw weight ranks the higher-weight hub pairing first (10 > 3)")

    def test_rank_by_rejects_unknown_value(self):
        with self.assertRaises(ValueError):
            CO_COMMIT.query_associations(self.db, "Q.md", vault="v", rank_by="bogus")

    def test_note_totals(self):
        totals, grand_total = CO_COMMIT.note_totals(self.db, "v")
        self.assertEqual(totals["Q.md"], 13.0)  # 10 + 3
        self.assertEqual(totals["H.md"], 50.0)  # 10 (Q) + 4*10 (X1-4)
        self.assertEqual(totals["R.md"], 3.0)
        self.assertEqual(grand_total, sum(totals.values()))


if __name__ == "__main__":
    unittest.main()
