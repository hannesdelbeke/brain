import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


SKILL = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL))
import search_vault  # noqa: E402

SPEC = importlib.util.spec_from_file_location("test_indexer", SKILL / "index_pkm_meta.py")
INDEXER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(INDEXER)


def build_fixture(temp: str) -> Path:
    vault = Path(temp) / "vault"
    (vault / ".obsidian").mkdir(parents=True)
    (vault / "alpha.md").write_text("## Result\nA distinctive fallbackphrase.\n", encoding="utf-8")
    database = vault / ".obsidian" / "pkm_index.db"
    INDEXER.build_index(str(vault), str(database), skip_embeddings=True)
    return database


class DaemonHealingTest(unittest.TestCase):
    def test_auto_heal_spawns_without_crashing_when_daemon_is_offline(self):
        with tempfile.TemporaryDirectory() as temp:
            database = Path(temp) / "pkm_index.db"
            with patch.object(search_vault, "daemon_healthy", return_value=False), \
                 patch.object(search_vault.subprocess, "Popen") as popen:
                popen.return_value.pid = 4242
                self.assertEqual(search_vault.auto_spawn_daemon(str(database)), 4242)
                popen.assert_called_once()

    def test_a_failed_spawn_still_lets_fts5_answer(self):
        """The brief's hardest clause: the spawn failing must not cost the caller an answer."""
        with tempfile.TemporaryDirectory() as temp:
            database = build_fixture(temp)
            with patch.object(search_vault, "daemon_healthy", return_value=False), \
                 patch.object(search_vault.subprocess, "Popen", side_effect=OSError("no fork for you")):
                self.assertIsNone(search_vault.auto_spawn_daemon(str(database)))
            results = search_vault.fast_fts_search("fallbackphrase", database, top=5)
            self.assertTrue(results, "a failed spawn left the caller with no results")
            self.assertEqual(results[0]["path"], "alpha.md")

    def test_spawn_decision_follows_the_daemon_the_caller_named(self):
        """--daemon pointing elsewhere must not be judged by the default daemon's health.

        Health-checking DEFAULT_DAEMON here meant a healthy daemon on the default
        port suppressed the spawn even when the daemon the search actually used
        was down.
        """
        with tempfile.TemporaryDirectory() as temp:
            database = Path(temp) / "pkm_index.db"
            seen = []

            def health(base):
                seen.append(base)
                return False

            with patch.object(search_vault, "daemon_healthy", side_effect=health), \
                 patch.object(search_vault.subprocess, "Popen") as popen:
                popen.return_value.pid = 99
                search_vault.auto_spawn_daemon(str(database), "http://127.0.0.1:9999")
            self.assertEqual(seen, ["http://127.0.0.1:9999"])


if __name__ == "__main__":
    unittest.main()
