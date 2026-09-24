"""A named --vault must never be answered silently from another corpus.

daemon_get refuses rather than let a mistyped --vault fall through to whatever
index the working directory resolves to, because a search of a corpus the caller
did not name is worse than no search. The FTS5 fallback cannot honour --vault at
all, since only the daemon holds the name-to-root mapping, so the requirement
here is the next best thing: it must say so on stderr and name the database that
actually answered, rather than pass the result off as the requested corpus.
"""

import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SKILL = Path(__file__).resolve().parents[1]

SPEC = importlib.util.spec_from_file_location("test_indexer", SKILL / "index_pkm_meta.py")
INDEXER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(INDEXER)

DEAD_DAEMON = "http://127.0.0.1:1"


def build_fixture(temp: str) -> Path:
    vault = Path(temp) / "vault"
    (vault / ".obsidian").mkdir(parents=True)
    (vault / "alpha.md").write_text("## Result\nA distinctive fallbackphrase.\n", encoding="utf-8")
    INDEXER.build_index(str(vault), str(vault / ".obsidian" / "pkm_index.db"), skip_embeddings=True)
    return vault


def run_search(vault: Path, *extra: str) -> subprocess.CompletedProcess:
    # --no-spawn keeps the test from leaving a real daemon behind.
    return subprocess.run(
        [sys.executable, str(SKILL / "search_vault.py"), "fallbackphrase",
         "--daemon", DEAD_DAEMON, "--no-spawn", *extra],
        cwd=str(vault), capture_output=True, text=True, timeout=60,
    )


class VaultSelectionTest(unittest.TestCase):
    def test_named_vault_is_flagged_when_the_fallback_cannot_honour_it(self):
        with tempfile.TemporaryDirectory() as temp:
            vault = build_fixture(temp)
            completed = run_search(vault, "--vault", "ledger")
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertIn("--vault ledger cannot be honoured", completed.stderr)
            self.assertIn("fallbackphrase", completed.stdout)

    def test_the_default_vault_draws_no_warning(self):
        with tempfile.TemporaryDirectory() as temp:
            vault = build_fixture(temp)
            completed = run_search(vault)
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertNotIn("cannot be honoured", completed.stderr)
            self.assertIn("fallbackphrase", completed.stdout)

    def test_no_spawn_leaves_no_daemon_behind(self):
        with tempfile.TemporaryDirectory() as temp:
            vault = build_fixture(temp)
            completed = run_search(vault)
            self.assertNotIn("auto-spawned", completed.stderr)


if __name__ == "__main__":
    unittest.main()
