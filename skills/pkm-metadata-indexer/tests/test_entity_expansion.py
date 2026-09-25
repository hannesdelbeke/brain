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


class SentenceQueryTest(unittest.TestCase):
    """A sentence must come back untouched, because the caller searches with it.

    `search_vault` and the daemon hand the expanded string to `search_index`
    whole, so every name added here is embedded as part of the query vector and
    read by the cross-encoder as part of the question. Expansion used to fire on
    any single shared token, which on a real vault meant a fifteen-word symptom
    matched almost every note and came back with two dozen unrelated titles
    appended -- measured at symptom recall@5 of 16.7% against 94.4% without them.
    """

    def build(self, vault: Path) -> Path:
        (vault / ".obsidian").mkdir(parents=True)
        # Each note shares a common word with the query below and nothing else.
        for name in ("alpha", "beta", "gamma", "delta"):
            (vault / f"{name} the command.md").write_text(
                f"---\naliases:\n  - {name} corporation\n---\n## {name}\nbody\n", encoding="utf-8")
        database = vault / ".obsidian" / "pkm_index.db"
        INDEXER.build_index(str(vault), str(database), skip_embeddings=True)
        return database

    def test_a_sentence_is_not_expanded(self):
        with tempfile.TemporaryDirectory() as temp:
            database = self.build(Path(temp) / "vault")
            query = ("claude keeps refusing the command saying it cannot "
                     "determine whether this command is safe to run")
            self.assertEqual(entity_expansion.expand_query(query, database), [query])

    def test_a_token_in_most_of_the_corpus_expands_nothing(self):
        with tempfile.TemporaryDirectory() as temp:
            database = self.build(Path(temp) / "vault")
            # `command` is in all four titles, so it selects the corpus, not a note.
            self.assertEqual(entity_expansion.expand_query("command", database), ["command"])

    def test_a_name_still_expands(self):
        with tempfile.TemporaryDirectory() as temp:
            database = self.build(Path(temp) / "vault")
            self.assertIn("alpha corporation", entity_expansion.expand_query("alpha", database))


class PreparedNotesCacheTest(unittest.TestCase):
    """The scan is cached across queries, so staleness is the risk worth testing.

    The daemon holds this for its whole lifetime. If a reindex did not invalidate
    it, every expansion afterwards would answer from the previous corpus.
    """

    def build(self, vault: Path, notes: dict[str, str]) -> Path:
        (vault / ".obsidian").mkdir(parents=True, exist_ok=True)
        for name, body in notes.items():
            (vault / name).write_text(body, encoding="utf-8")
        database = vault / ".obsidian" / "pkm_index.db"
        INDEXER.build_index(str(vault), str(database), skip_embeddings=True)
        return database

    def test_a_reindex_invalidates_the_cache(self):
        with tempfile.TemporaryDirectory() as temp:
            vault = Path(temp) / "vault"
            database = self.build(vault, {
                "first.md": "---\naliases:\n  - Alpha\n---\n## A\nbody\n"})
            self.assertIn("Alpha", entity_expansion.expand_facets(["first"], database)["first"])
            # A note the first scan never saw, and a fresh index over both.
            self.build(vault, {"second.md": "---\naliases:\n  - Beta\n---\n## B\nbody\n"})
            found = entity_expansion.expand_facets(["second"], database)["second"]
            self.assertIn("Beta", found,
                          "expansion answered from the pre-reindex corpus")

    def test_a_repeat_call_does_not_reopen_the_database(self):
        with tempfile.TemporaryDirectory() as temp:
            database = self.build(Path(temp) / "vault", {
                "note.md": "---\naliases:\n  - Alpha\n---\n## A\nbody\n"})
            first = entity_expansion.prepared_notes(database)
            self.assertIs(entity_expansion.prepared_notes(database), first,
                          "the second call rebuilt instead of reusing")

    def test_a_missing_database_is_not_an_error(self):
        with tempfile.TemporaryDirectory() as temp:
            self.assertEqual(entity_expansion.prepared_notes(Path(temp) / "nope.db"), [])


if __name__ == "__main__":
    unittest.main()
