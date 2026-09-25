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

    def test_vault_flag_extraction(self):
        with tempfile.TemporaryDirectory() as temp:
            vault = Path(temp) / "vault"
            session_dir = vault / "sessions"
            (vault / ".obsidian").mkdir(parents=True)
            session_dir.mkdir()
            (session_dir / "with-vault-flags.md").write_text(
                "---\nsession_id: session-2\ndate: 2026-09-25\n"
                "touched:\n"
                "  - target: some note title\n    action: edited\n    vault: true\n"
                "  - target: repo/src/file.py\n    action: edited\n    vault: false\n"
                "  - target: other file\n    action: read\n---\n"
                "## Test session\n", encoding="utf-8"
            )
            database = vault / ".obsidian" / "pkm_index.db"
            INDEXER.build_index(str(vault), str(database), skip_embeddings=True)
            connection = sqlite3.connect(database)
            try:
                touches = connection.execute(
                    "SELECT target_path, vault FROM session_touches WHERE session_id = 'session-2' "
                    "ORDER BY target_path"
                ).fetchall()
            finally:
                connection.close()
            self.assertEqual(touches, [
                ("other file", None),
                ("repo/src/file.py", 0),
                ("some note title", 1),
            ])

    def test_touched_filter(self):
        with tempfile.TemporaryDirectory() as temp:
            vault = Path(temp) / "vault"
            session_dir = vault / "sessions"
            (vault / ".obsidian").mkdir(parents=True)
            session_dir.mkdir()
            (session_dir / "notes-only.md").write_text(
                "---\nsession_id: session-notes\ndate: 2026-09-25\n"
                "touched:\n"
                "  - target: concept.md\n    action: edited\n    vault: true\n---\n"
                "## Notes session\n", encoding="utf-8"
            )
            (session_dir / "code-only.md").write_text(
                "---\nsession_id: session-code\ndate: 2026-09-25\n"
                "touched:\n"
                "  - target: src/main.py\n    action: edited\n    vault: false\n---\n"
                "## Code session\n", encoding="utf-8"
            )
            (session_dir / "mixed.md").write_text(
                "---\nsession_id: session-mixed\ndate: 2026-09-25\n"
                "touched:\n"
                "  - target: notes.md\n    action: edited\n    vault: true\n"
                "  - target: src/util.py\n    action: edited\n    vault: false\n---\n"
                "## Mixed session\n", encoding="utf-8"
            )
            database = vault / ".obsidian" / "pkm_index.db"
            INDEXER.build_index(str(vault), str(database), skip_embeddings=True)

            results_any = INDEXER.query_sessions("session", db_path=str(database), limit=10, touched="any")
            self.assertEqual(len(results_any), 3)
            self.assertEqual(
                {r["session_id"] for r in results_any},
                {"session-notes", "session-code", "session-mixed"}
            )

            results_notes = INDEXER.query_sessions("py", db_path=str(database), limit=10, touched="notes")
            self.assertEqual(len(results_notes), 0)

            results_code = INDEXER.query_sessions("py", db_path=str(database), limit=10, touched="code")
            self.assertEqual(len(results_code), 2)
            self.assertEqual(
                {r["session_id"] for r in results_code},
                {"session-code", "session-mixed"}
            )


if __name__ == "__main__":
    unittest.main()
