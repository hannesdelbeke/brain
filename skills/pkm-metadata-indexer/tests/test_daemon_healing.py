import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


SKILL = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL))
import search_vault  # noqa: E402


class DaemonHealingTest(unittest.TestCase):
    def test_auto_heal_spawns_without_crashing_when_daemon_is_offline(self):
        with tempfile.TemporaryDirectory() as temp:
            database = Path(temp) / "pkm_index.db"
            with patch.object(search_vault, "daemon_healthy", return_value=False), \
                 patch.object(search_vault.subprocess, "Popen") as popen:
                popen.return_value.pid = 4242
                self.assertEqual(search_vault.auto_spawn_daemon(str(database)), 4242)
                popen.assert_called_once()


if __name__ == "__main__":
    unittest.main()
