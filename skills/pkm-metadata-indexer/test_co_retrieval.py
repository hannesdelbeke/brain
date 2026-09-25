import contextlib
import importlib.util
import os
import tempfile
import unittest
from pathlib import Path


def load(name: str):
    path = Path(__file__).with_name(f"{name}.py")
    spec = importlib.util.spec_from_file_location(f"{name}_module", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


CO_RETRIEVAL = load("co_retrieval")


@contextlib.contextmanager
def telemetry_dir(value):
    """Set or clear PKM_TELEMETRY_DIR, restoring whatever the machine had."""
    previous = os.environ.get("PKM_TELEMETRY_DIR")
    if value is None:
        os.environ.pop("PKM_TELEMETRY_DIR", None)
    else:
        os.environ["PKM_TELEMETRY_DIR"] = str(value)
    try:
        yield
    finally:
        if previous is None:
            os.environ.pop("PKM_TELEMETRY_DIR", None)
        else:
            os.environ["PKM_TELEMETRY_DIR"] = previous


class ResolveLogPathsTest(unittest.TestCase):
    """The reader has to open the file the writer writes, or it derives an empty
    graph and says nothing, which is the failure that motivated these."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        base = Path(self.temp_dir.name)

        self.configured = base / "telemetry"
        self.configured.mkdir()
        self.configured_log = self.configured / "queries_configured.jsonl"
        self.configured_log.write_text("", encoding="utf-8")

        # a vault laid out the way the old vault-relative discovery expected
        self.vault_root = base / "vault"
        vault_queries = self.vault_root / "data" / "telemetry" / "queries"
        vault_queries.mkdir(parents=True)
        self.vault_log = vault_queries / "queries_vault.jsonl"
        self.vault_log.write_text("", encoding="utf-8")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_configured_directory_beats_the_vault_relative_guess(self):
        with telemetry_dir(self.configured):
            found = CO_RETRIEVAL.resolve_log_paths(str(self.vault_root))
        self.assertEqual(found, [self.configured_log])

    def test_an_explicit_log_still_beats_the_configured_directory(self):
        # --log is the operator saying exactly which file to read, so it outranks
        # the environment the daemon happens to be running with.
        with telemetry_dir(self.configured):
            found = CO_RETRIEVAL.resolve_log_paths("", log_override=self.vault_log)
        self.assertEqual(found, [self.vault_log])

    def test_the_vault_relative_cascade_survives_when_nothing_is_configured(self):
        with telemetry_dir(None):
            found = CO_RETRIEVAL.resolve_log_paths(str(self.vault_root))
        # resolved on both sides: the cascade calls .resolve(), and on macOS the
        # temp dir is /var, a symlink to /private/var
        self.assertEqual(found, [self.vault_log.resolve()])

    def test_an_empty_configured_directory_falls_through_rather_than_returning_nothing(self):
        empty = Path(self.temp_dir.name) / "empty"
        empty.mkdir()
        with telemetry_dir(empty):
            found = CO_RETRIEVAL.resolve_log_paths(str(self.vault_root))
        self.assertEqual(found, [self.vault_log.resolve()])

    def test_the_reader_resolves_the_file_the_writer_writes(self):
        # The invariant that matters, asserted across the two modules rather than
        # within either: searchd picks a destination, co_retrieval has to find it.
        searchd = load("searchd")
        with telemetry_dir(self.configured):
            written = searchd.resolve_query_log()
            written.write_text("", encoding="utf-8")
            found = CO_RETRIEVAL.resolve_log_paths("")
        self.assertIn(written, found)
        self.assertEqual(written.parent, self.configured)


if __name__ == "__main__":
    unittest.main()
