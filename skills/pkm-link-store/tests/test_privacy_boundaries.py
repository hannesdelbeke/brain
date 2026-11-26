import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from link_store.adapters import BoundaryPolicy, sync_claude_root  # noqa: E402
from link_store.db import LinkStoreDB  # noqa: E402


class PrivacyBoundariesTest(unittest.TestCase):
    def test_deny_root_overrides_allow_root_and_blocks_ingestion(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            vault = root / "vault"
            public_dir = vault / "notes"
            private_dir = vault / "restricted"
            public_dir.mkdir(parents=True)
            private_dir.mkdir(parents=True)
            (public_dir / "ok.md").write_text("# OK\n", encoding="utf-8")
            (private_dir / "secret.md").write_text("# Secret\n", encoding="utf-8")

            claude_root = root / "claude"
            claude_root.mkdir()
            (claude_root / "s1.jsonl").write_text(
                json.dumps(
                    {
                        "type": "assistant",
                        "sessionId": "s1",
                        "cwd": str(vault),
                        "timestamp": "2026-05-01T12:00:00Z",
                        "message": {
                            "content": [
                                {"type": "tool_use", "name": "Read", "input": {"file_path": str(public_dir / "ok.md")}},
                                {"type": "tool_use", "name": "Read", "input": {"file_path": str(private_dir / "secret.md")}},
                            ]
                        },
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            policy = BoundaryPolicy.from_args(
                allow_roots=[vault, claude_root],
                deny_roots=[private_dir],
                vault_roots={"brain": vault},
            )
            with LinkStoreDB(root / "store.db") as db:
                res = sync_claude_root(db, claude_root, policy=policy)
                self.assertGreaterEqual(res["skipped_denied"], 1)
                self.assertIsNotNone(db.get_node("note:brain/notes/ok.md"))
                self.assertIsNone(db.get_node("note:brain/restricted/secret.md"))


if __name__ == "__main__":
    unittest.main()
