import importlib.util
import sys
import tempfile
import time
import unittest
from pathlib import Path


SKILL = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL))
import search_vault  # noqa: E402

SPEC = importlib.util.spec_from_file_location("test_indexer", SKILL / "index_pkm_meta.py")
INDEXER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(INDEXER)


class FtsFallbackTest(unittest.TestCase):
    def test_fts5_standalone_speed(self):
        with tempfile.TemporaryDirectory() as temp:
            vault = Path(temp) / "vault"
            (vault / ".obsidian").mkdir(parents=True)
            (vault / "alpha.md").write_text("## Result\nA distinctive fallbackphrase.\n", encoding="utf-8")
            database = vault / ".obsidian" / "pkm_index.db"
            INDEXER.build_index(str(vault), str(database), skip_embeddings=True)
            start = time.perf_counter()
            # expand=True is named rather than inherited: this exercises the
            # expanding branch on purpose, and the CLI default is False.
            results = search_vault.fast_fts_search("fallbackphrase", database, top=5, expand=True)
            elapsed = time.perf_counter() - start
            self.assertTrue(results)
            self.assertEqual(results[0]["path"], "alpha.md")
            self.assertLess(elapsed, 0.05, f"FTS5 search too slow: {elapsed}s")


if __name__ == "__main__":
    unittest.main()
