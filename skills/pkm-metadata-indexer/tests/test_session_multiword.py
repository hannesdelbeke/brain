import importlib.util
import sqlite3
import tempfile
import unittest
from pathlib import Path


SKILL = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("search_vault", SKILL / "search_vault.py")
SEARCH = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SEARCH)

SPEC_INDEXER = importlib.util.spec_from_file_location("test_indexer", SKILL / "index_pkm_meta.py")
INDEXER = importlib.util.module_from_spec(SPEC_INDEXER)
SPEC_INDEXER.loader.exec_module(INDEXER)


class SessionMultiwordTest(unittest.TestCase):
    def test_single_term(self):
        """Single-term query should behave as before."""
        with tempfile.TemporaryDirectory() as temp:
            vault = Path(temp) / "vault"
            session_dir = vault / "sessions"
            (vault / ".obsidian").mkdir(parents=True)
            session_dir.mkdir()
            (session_dir / "session-a.md").write_text(
                "---\nsession_id: session-a\ndate: 2026-10-18\n---\n"
                "## fix login timeout in widget service\n", encoding="utf-8"
            )
            database = vault / ".obsidian" / "pkm_index.db"
            INDEXER.build_index(str(vault), str(database), skip_embeddings=True)

            results = SEARCH.fast_session_search("login", str(database))
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0]["session_id"], "session-a")

    def test_adjacent_multi_term(self):
        """Multi-word query where words are adjacent in title."""
        with tempfile.TemporaryDirectory() as temp:
            vault = Path(temp) / "vault"
            session_dir = vault / "sessions"
            (vault / ".obsidian").mkdir(parents=True)
            session_dir.mkdir()
            (session_dir / "session-b.md").write_text(
                "---\nsession_id: session-b\ndate: 2026-10-18\n---\n"
                "## fix login timeout in widget service\n", encoding="utf-8"
            )
            database = vault / ".obsidian" / "pkm_index.db"
            INDEXER.build_index(str(vault), str(database), skip_embeddings=True)

            results = SEARCH.fast_session_search("login timeout", str(database))
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0]["session_id"], "session-b")

    def test_non_adjacent_multi_term_and(self):
        """Multi-word query where words are not adjacent (AND path)."""
        with tempfile.TemporaryDirectory() as temp:
            vault = Path(temp) / "vault"
            session_dir = vault / "sessions"
            (vault / ".obsidian").mkdir(parents=True)
            session_dir.mkdir()
            (session_dir / "session-c.md").write_text(
                "---\nsession_id: session-c\ndate: 2026-10-18\n---\n"
                "## rollup drain cost sonnet haiku analysis\n", encoding="utf-8"
            )
            database = vault / ".obsidian" / "pkm_index.db"
            INDEXER.build_index(str(vault), str(database), skip_embeddings=True)

            results = SEARCH.fast_session_search("rollup drain cost sonnet haiku", str(database))
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0]["session_id"], "session-c")

    def test_partial_match_or_fallback(self):
        """Query where one term matches nothing, OR fallback returns partial matches ranked."""
        with tempfile.TemporaryDirectory() as temp:
            vault = Path(temp) / "vault"
            session_dir = vault / "sessions"
            (vault / ".obsidian").mkdir(parents=True)
            session_dir.mkdir()
            (session_dir / "session-d1.md").write_text(
                "---\nsession_id: session-d1\ndate: 2026-10-18\n---\n"
                "## arena combo implementation\n", encoding="utf-8"
            )
            (session_dir / "session-d2.md").write_text(
                "---\nsession_id: session-d2\ndate: 2026-10-17\n---\n"
                "## arena refactor\n", encoding="utf-8"
            )
            database = vault / ".obsidian" / "pkm_index.db"
            INDEXER.build_index(str(vault), str(database), skip_embeddings=True)

            # "arena combo zzqx" - zzqx matches nothing, so AND returns empty, fallback to OR
            results = SEARCH.fast_session_search("arena combo zzqx", str(database))
            # Should get session-d1 (2 matches: arena+combo) before session-d2 (1 match: arena)
            self.assertEqual(len(results), 2)
            self.assertEqual(results[0]["session_id"], "session-d1")
            self.assertEqual(results[1]["session_id"], "session-d2")

    def test_no_match_at_all(self):
        """Query with no matches returns empty."""
        with tempfile.TemporaryDirectory() as temp:
            vault = Path(temp) / "vault"
            session_dir = vault / "sessions"
            (vault / ".obsidian").mkdir(parents=True)
            session_dir.mkdir()
            (session_dir / "session-e.md").write_text(
                "---\nsession_id: session-e\ndate: 2026-10-18\n---\n"
                "## some other work\n", encoding="utf-8"
            )
            database = vault / ".obsidian" / "pkm_index.db"
            INDEXER.build_index(str(vault), str(database), skip_embeddings=True)

            results = SEARCH.fast_session_search("zzqx nonexistent", str(database))
            self.assertEqual(len(results), 0)

    def test_touched_path_multiword(self):
        """Multi-word query matching touched file paths."""
        with tempfile.TemporaryDirectory() as temp:
            vault = Path(temp) / "vault"
            session_dir = vault / "sessions"
            (vault / ".obsidian").mkdir(parents=True)
            session_dir.mkdir()
            (session_dir / "session-f.md").write_text(
                "---\nsession_id: session-f\ndate: 2026-10-18\n"
                "touched:\n"
                "  - target: src/auth/login_handler.py\n    action: modified\n    vault: false\n---\n"
                "## backend work\n", encoding="utf-8"
            )
            database = vault / ".obsidian" / "pkm_index.db"
            INDEXER.build_index(str(vault), str(database), skip_embeddings=True)

            results = SEARCH.fast_session_search("auth login", str(database))
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0]["session_id"], "session-f")


if __name__ == "__main__":
    unittest.main()
