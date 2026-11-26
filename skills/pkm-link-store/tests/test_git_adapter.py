import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from link_store.adapters import BoundaryPolicy, sync_git_repo  # noqa: E402
from link_store.db import LinkStoreDB  # noqa: E402


def _git(repo: Path, *args: str) -> str:
    res = subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True,
        text=True,
        check=True,
    )
    return res.stdout.strip()


class GitAdapterTest(unittest.TestCase):
    def test_branches_commits_trailers_large_commit_guard_and_deleted_branch_expiry(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = root / "vault"
            repo.mkdir()
            _git(repo, "init", "-b", "main")
            _git(repo, "config", "user.name", "Test Bot")
            _git(repo, "config", "user.email", "test@example.invalid")
            _git(repo, "remote", "add", "origin", "https://github.com/org/vault.git")

            (repo / "alpha.md").write_text("# Alpha\n", encoding="utf-8")
            _git(repo, "add", "alpha.md")
            _git(repo, "commit", "-m", "Add alpha\n\nSession: sess-99")

            # Feature branch that will later be deleted
            _git(repo, "checkout", "-b", "feat/temp")
            (repo / "beta.md").write_text("# Beta\n", encoding="utf-8")
            _git(repo, "add", "beta.md")
            _git(repo, "commit", "-m", "Add beta")

            # Bulk commit (> 200 files) should skip changed_file edges
            bulk_dir = repo / "bulk"
            bulk_dir.mkdir()
            for i in range(205):
                (bulk_dir / f"f{i}.txt").write_text("x", encoding="utf-8")
            _git(repo, "add", "bulk")
            _git(repo, "commit", "-m", "Bulk import")

            db_path = root / "store.db"
            policy = BoundaryPolicy.from_args(vault_roots={"brain": repo})
            with LinkStoreDB(db_path) as db:
                res1 = sync_git_repo(db, "brain", repo, policy=policy)
                self.assertEqual(res1["branches"], 2)
                self.assertEqual(res1["skipped_large"], 1)

                # Session trailer edge created
                sess_edges = db.conn.execute(
                    "SELECT dst_id FROM edges WHERE rel = 'mentions_session' AND expired_at IS NULL"
                ).fetchall()
                self.assertEqual([r["dst_id"] for r in sess_edges], ["session:sess-99"])

                # Default branch marked is_default=True
                main_node = db.get_node("branch:github.com/org/vault@main")
                self.assertIn('"is_default": true', main_node["metadata_json"])

                # Delete feat/temp and resync -> Branch node should be expired
                _git(repo, "checkout", "main")
                _git(repo, "branch", "-D", "feat/temp")
                res2 = sync_git_repo(db, "brain", repo, policy=policy)
                self.assertEqual(res2["expired_branches"], 1)
                temp_node = db.get_node("branch:github.com/org/vault@feat/temp")
                self.assertIsNotNone(temp_node["expired_at"])


if __name__ == "__main__":
    unittest.main()
