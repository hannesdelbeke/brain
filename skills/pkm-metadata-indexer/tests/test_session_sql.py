import importlib.util
import sqlite3
import tempfile
import time
import unittest
from pathlib import Path


SKILL = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("test_indexer", SKILL / "index_pkm_meta.py")
INDEXER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(INDEXER)


class SessionSqlTest(unittest.TestCase):
    def test_session_provenance_projection_and_speed(self):
        with tempfile.TemporaryDirectory() as temp:
            vault = Path(temp) / "vault"
            session_dir = vault / "sessions"
            (vault / ".obsidian").mkdir(parents=True)
            session_dir.mkdir()
            (session_dir / "rollup.md").write_text(
                "---\nsession_id: session-1\ndate: 2026-09-24\ntrace_path: traces/session-1.jsonl\n"
                "cost_usd: 1.25\nrepo: example/repo\ntouched:\n"
                "  - target: scripts/example.py\n    action: modified\n---\n"
                "## Vault conventions backfill\n", encoding="utf-8"
            )
            database = vault / ".obsidian" / "pkm_index.db"
            INDEXER.build_index(str(vault), str(database), skip_embeddings=True)
            connection = sqlite3.connect(database)
            try:
                start = time.perf_counter()
                rows = connection.execute(
                    "SELECT session_id, title FROM sessions_idx WHERE title LIKE '%vault conventions%'"
                ).fetchall()
                elapsed = time.perf_counter() - start
                touches = connection.execute(
                    "SELECT action FROM session_touches WHERE target_path = 'scripts/example.py'"
                ).fetchall()
            finally:
                connection.close()
            self.assertEqual(rows, [("session-1", "Vault conventions backfill")])
            self.assertEqual(touches, [("modified",)])
            self.assertLess(elapsed, 0.005, f"Session query too slow: {elapsed}s")


if __name__ == "__main__":
    unittest.main()
