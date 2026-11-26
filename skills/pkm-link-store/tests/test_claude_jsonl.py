import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from link_store.adapters import BoundaryPolicy, sync_claude_root  # noqa: E402
from link_store.db import LinkStoreDB  # noqa: E402


def _init_git_repo(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "-C", str(path), "init", "-q"], check=True)
    subprocess.run(["git", "-C", str(path), "remote", "add", "origin", "https://github.com/org/demo.git"], check=True)


class ClaudeJsonlAdapterTest(unittest.TestCase):
    def test_incremental_sync_subagents_branches_and_ignores_tool_results(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            vault_dir = root / "vault"
            vault_dir.mkdir()
            (vault_dir / "design.md").write_text("# Design\n", encoding="utf-8")
            _init_git_repo(vault_dir)

            claude_root = root / "claude_projects" / "demo"
            sub_dir = claude_root / "sess-1" / "subagents"
            sub_dir.mkdir(parents=True)

            parent_jsonl = claude_root / "sess-1.jsonl"
            lines = [
                {
                    "type": "user",
                    "sessionId": "sess-1",
                    "cwd": str(vault_dir),
                    "gitBranch": "feat/link-store",
                    "timestamp": "2026-05-01T10:00:00Z",
                    "message": {
                        "content": [
                            {"type": "text", "text": "Check https://docs.python.org/3/library/sqlite3.html."}
                        ]
                    },
                },
                {
                    "type": "assistant",
                    "sessionId": "sess-1",
                    "cwd": str(vault_dir),
                    "gitBranch": "feat/link-store",
                    "timestamp": "2026-05-01T10:05:00Z",
                    "message": {
                        "content": [
                            {"type": "tool_use", "name": "Read", "input": {"file_path": str(vault_dir / "design.md")}},
                            {"type": "tool_use", "name": "WebFetch", "input": {"url": "https://sqlite.org/wal.html"}},
                        ]
                    },
                },
                {
                    "type": "user",
                    "sessionId": "sess-1",
                    "cwd": str(vault_dir),
                    "gitBranch": "feat/link-store",
                    "timestamp": "2026-05-01T10:06:00Z",
                    "message": {
                        "content": [
                            {
                                "type": "tool_result",
                                "content": "Ignore https://ignored-from-tool-result.invalid/secret?token=abc",
                            }
                        ]
                    },
                },
            ]
            parent_jsonl.write_text("\n".join(json.dumps(x) for x in lines) + "\n", encoding="utf-8")

            sub_jsonl = sub_dir / "agent-sub42.jsonl"
            sub_jsonl.write_text(
                json.dumps(
                    {
                        "type": "assistant",
                        "sessionId": "sess-1",
                        "agentId": "sub42",
                        "cwd": str(vault_dir),
                        "timestamp": "2026-05-01T10:07:00Z",
                        "message": {
                            "content": [
                                {"type": "tool_use", "name": "Edit", "input": {"file_path": str(vault_dir / "design.md")}}
                            ]
                        },
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            db_path = root / "store.db"
            policy = BoundaryPolicy.from_args(vault_roots={"brain": vault_dir})
            with LinkStoreDB(db_path) as db:
                res1 = sync_claude_root(db, root / "claude_projects", policy=policy)
                self.assertEqual(res1["files"], 2)

                # Verify tool_result URL was ignored
                ignored = db.get_node("url:https://ignored-from-tool-result.invalid/secret")
                self.assertIsNone(ignored)

                # Verify subagent child_of and modified_file
                edges = db.conn.execute(
                    "SELECT src_id, dst_id, rel, valid_from, valid_to FROM edges WHERE expired_at IS NULL"
                ).fetchall()
                edge_set = {(r["src_id"], r["dst_id"], r["rel"]) for r in edges}
                self.assertIn(("session:sess-1:agent-sub42", "session:sess-1", "child_of"), edge_set)
                self.assertIn(("session:sess-1", "note:brain/design.md", "read_file"), edge_set)
                self.assertIn(("session:sess-1:agent-sub42", "note:brain/design.md", "modified_file"), edge_set)
                self.assertIn(("session:sess-1", "url:https://sqlite.org/wal.html", "fetched_url"), edge_set)
                self.assertIn(
                    ("session:sess-1", "branch:github.com/org/demo@feat/link-store", "worked_in_branch"),
                    edge_set,
                )

                # Incremental append should process only new lines
                with parent_jsonl.open("a", encoding="utf-8") as fh:
                    fh.write(
                        json.dumps(
                            {
                                "type": "assistant",
                                "sessionId": "sess-1",
                                "cwd": str(vault_dir),
                                "timestamp": "2026-05-01T10:10:00Z",
                                "message": {
                                    "content": [
                                        {"type": "tool_use", "name": "WebFetch", "input": {"url": "https://linkml.io/"}}
                                    ]
                                },
                            }
                        )
                        + "\n"
                    )
                res2 = sync_claude_root(db, root / "claude_projects", policy=policy)
                self.assertEqual(res2["records"], 1)
                self.assertIsNotNone(db.get_node("url:https://linkml.io/"))


if __name__ == "__main__":
    unittest.main()
