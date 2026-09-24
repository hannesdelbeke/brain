import contextlib
import importlib.util
import io
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SKILL = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL))

SPEC = importlib.util.spec_from_file_location("test_indexer", SKILL / "index_pkm_meta.py")
INDEXER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(INDEXER)


class LoggingTest(unittest.TestCase):
    def test_build_index_emits_nothing_to_stdout_when_called_as_library(self):
        """Regression test for the logging change: progress moved from print to log.

        build_index() is imported and called by searchd.py, index_sessions.py and
        the experiment scripts. A library call has no business writing a timing
        table to their stdout.
        """
        with tempfile.TemporaryDirectory() as temp:
            vault = Path(temp) / "vault"
            (vault / ".obsidian").mkdir(parents=True)
            (vault / "test.md").write_text("# Test\nSome content.\n", encoding="utf-8")
            database = vault / ".obsidian" / "pkm_index.db"

            stdout_capture = io.StringIO()
            with contextlib.redirect_stdout(stdout_capture):
                INDEXER.build_index(str(vault), str(database), skip_embeddings=True)

            captured = stdout_capture.getvalue()
            self.assertEqual(captured, "", f"build_index() wrote to stdout: {captured!r}")

    def test_quiet_flag_suppresses_progress(self):
        """--quiet suppresses indexing progress while the command still exits 0."""
        with tempfile.TemporaryDirectory() as temp:
            vault = Path(temp) / "vault"
            (vault / ".obsidian").mkdir(parents=True)
            (vault / "test.md").write_text("# Test\nSome content.\n", encoding="utf-8")
            database = vault / ".obsidian" / "pkm_index.db"

            result = subprocess.run(
                [sys.executable, str(SKILL / "index_pkm_meta.py"),
                 "--vault", str(vault), "--db", str(database),
                 "--skip-embeddings", "--quiet"],
                capture_output=True, text=True
            )

            self.assertEqual(result.returncode, 0, f"--quiet run failed: {result.stderr}")
            self.assertEqual(result.stdout, "", f"--quiet produced output: {result.stdout!r}")


if __name__ == "__main__":
    unittest.main()
