import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


SKILL = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL))
import entity_expansion  # noqa: E402

SPEC = importlib.util.spec_from_file_location("test_indexer", SKILL / "index_pkm_meta.py")
INDEXER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(INDEXER)


class EntityExpansionTest(unittest.TestCase):
    def test_alias_expansion_includes_titles_and_outbound_entities(self):
        with tempfile.TemporaryDirectory() as temp:
            vault = Path(temp) / "vault"
            (vault / ".obsidian").mkdir(parents=True)
            (vault / "entity.md").write_text(
                "---\naliases:\n  - EC\n  - Example Corporation\ntags:\n  - vendor\n---\n"
                "## Entity\n[[Example Tools]]\n",
                encoding="utf-8",
            )
            (vault / "Example Tools.md").write_text(
                "---\naliases:\n  - ET\n---\n## Tools\nExample tools material.\n", encoding="utf-8"
            )
            database = vault / ".obsidian" / "pkm_index.db"
            INDEXER.build_index(str(vault), str(database), skip_embeddings=True)
            terms = entity_expansion.expand_query("ec", database)
            self.assertIn("ec", terms)
            self.assertIn("Example Corporation", terms)
            self.assertIn("Example Tools", terms)


if __name__ == "__main__":
    unittest.main()
