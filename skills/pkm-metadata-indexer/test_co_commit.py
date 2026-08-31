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


if __name__ == "__main__":
    unittest.main()
