import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from link_store.canonical_ids import (  # noqa: E402
    branch_id,
    commit_id,
    file_id,
    note_id,
    repo_id,
    session_id,
    strip_branch_ref,
    url_id,
)


class CanonicalIdsTest(unittest.TestCase):
    def test_session_and_subagent_ids(self):
        self.assertEqual(session_id("abc-123"), "session:abc-123")
        self.assertEqual(session_id("abc-123", "xyz"), "session:abc-123:agent-xyz")
        self.assertEqual(session_id("abc-123", "agent-xyz"), "session:abc-123:agent-xyz")

    def test_repo_and_branch_ids_preserve_feature_prefixes(self):
        rid = repo_id("git@github.com:org-one/sample-repo.git")
        self.assertEqual(rid, "repo:github.com/org-one/sample-repo")
        self.assertEqual(
            repo_id("https://github.com/org-one/sample-repo.git"),
            rid,
        )
        self.assertEqual(strip_branch_ref("refs/heads/feat/x"), "feat/x")
        self.assertEqual(strip_branch_ref("refs/remotes/origin/feat/x"), "feat/x")
        self.assertEqual(strip_branch_ref("feat/x"), "feat/x")
        self.assertEqual(
            branch_id(rid, "refs/remotes/origin/feat/x"),
            "branch:github.com/org-one/sample-repo@feat/x",
        )

    def test_commit_note_and_file_ids(self):
        rid = "repo:github.com/org-one/sample-repo"
        sha = "a" * 40
        self.assertEqual(commit_id(rid, sha), f"commit:github.com/org-one/sample-repo@{sha}")
        self.assertEqual(note_id("brain", "./sub/note.md"), "note:brain/sub/note.md")
        self.assertEqual(file_id(rid, "./src/app.py"), "file:github.com/org-one/sample-repo@src/app.py")

    def test_url_id_strips_punctuation_filters_boilerplate_and_redacts_secrets(self):
        self.assertEqual(
            url_id("https://docs.python.org/3/library/sqlite3.html."),
            "url:https://docs.python.org/3/library/sqlite3.html",
        )
        self.assertIsNone(url_id("http://localhost:8080/health"))
        self.assertIsNone(url_id("https://example.com/test"))
        self.assertEqual(
            url_id("https://api.service.dev/items?token=supersecret&page=2"),
            "url:https://api.service.dev/items?page=2",
        )


if __name__ == "__main__":
    unittest.main()
