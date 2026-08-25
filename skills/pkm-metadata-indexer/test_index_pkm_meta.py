import importlib.util
import sqlite3
import tempfile
import unittest
from pathlib import Path


SCRIPT_PATH = Path(__file__).with_name("index_pkm_meta.py")
SPEC = importlib.util.spec_from_file_location("pkm_indexer", SCRIPT_PATH)
INDEXER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(INDEXER)


class MetadataIndexerTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.vault = Path(self.temp_dir.name) / "vault"
        (self.vault / ".obsidian").mkdir(parents=True)
        (self.vault / "folder").mkdir()
        self.db = self.vault / ".obsidian" / "pkm_index.db"
        (self.vault / "alpha.md").write_text(
            "---\ntags:\n  - test\n---\n\n## Planned\n"
            "A distinctivephrase appears here. [[folder/beta]]\n\n"
            "## Long\n"
            + " ".join(["word"] * 1000),
            encoding="utf-8",
        )
        (self.vault / "folder" / "beta.md").write_text(
            "## Result\nA linked destination.\n", encoding="utf-8"
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def build_metadata_only(self):
        return INDEXER.build_index(
            vault_path=str(self.vault), db_path=str(self.db), skip_embeddings=True
        )

    def test_metadata_fts_chunks_and_links(self):
        result = self.build_metadata_only()
        self.assertEqual(result["notes"], 2)
        self.assertGreater(result["sections"], 3)

        connection = sqlite3.connect(self.db)
        try:
            self.assertEqual(connection.execute("SELECT COUNT(*) FROM sections_fts").fetchone()[0], result["sections"])
            edge = connection.execute(
                "SELECT source_path, raw_target, resolved_target_path, start_line FROM edges"
            ).fetchone()
        finally:
            connection.close()
        self.assertEqual(edge[:3], ("alpha.md", "folder/beta", "folder/beta.md"))
        self.assertEqual(edge[3], 7)

        search_results = INDEXER.search_index(
            "distinctivephrase", vault_path=str(self.vault), db_path=str(self.db)
        )
        self.assertEqual(search_results[0]["path"], "alpha.md")
        self.assertEqual(search_results[0]["start_line"], 6)
        self.assertIn("distinctivephrase", search_results[0]["snippet"])

        links = INDEXER.query_links("folder/beta", vault_path=str(self.vault), db_path=str(self.db))
        self.assertEqual(links["path"], "folder/beta.md")
        self.assertEqual(links["inbound"][0][0], "alpha.md")

    def test_common_terms_are_pruned_from_the_fts_expression(self):
        self.build_metadata_only()
        connection = sqlite3.connect(self.db)
        try:
            cursor = connection.cursor()
            # 9 sections, "word" is in 7 of them and "distinctivephrase" in 1.
            self.assertEqual(
                INDEXER.fts_query("distinctivephrase word", cursor), '"distinctivephrase"'
            )
            # Every term too common leaves the rarest one rather than nothing.
            self.assertEqual(INDEXER.fts_query("word a", cursor), '"a"')
            # A single term is never pruned, and no cursor means no pruning.
            self.assertEqual(INDEXER.fts_query("word", cursor), '"word"')
            self.assertEqual(INDEXER.fts_query("distinctivephrase word"), '"distinctivephrase" OR "word"')
        finally:
            connection.close()

    def test_unchanged_section_keeps_cached_vector(self):
        self.build_metadata_only()
        connection = sqlite3.connect(self.db)
        try:
            section_id = connection.execute(
                "SELECT id FROM sections WHERE path = 'alpha.md' AND heading = 'Planned'"
            ).fetchone()[0]
            connection.execute(
                "UPDATE sections SET vector = ?, embedding_model = ?, chunking_version = ? WHERE id = ?",
                (
                    bytes(INDEXER.EMBEDDING_DIMENSIONS * 4),
                    INDEXER.EMBEDDING_MODEL,
                    INDEXER.CHUNKING_VERSION,
                    section_id,
                ),
            )
            connection.commit()
        finally:
            connection.close()

        self.build_metadata_only()
        connection = sqlite3.connect(self.db)
        try:
            cached_vector = connection.execute(
                "SELECT vector FROM sections WHERE id = ?", (section_id,)
            ).fetchone()[0]
        finally:
            connection.close()
        self.assertEqual(cached_vector, bytes(INDEXER.EMBEDDING_DIMENSIONS * 4))

        alpha_path = self.vault / "alpha.md"
        alpha_path.write_text(
            alpha_path.read_text(encoding="utf-8").replace("distinctivephrase", "changedphrase"),
            encoding="utf-8",
        )
        self.build_metadata_only()
        connection = sqlite3.connect(self.db)
        try:
            updated_vector = connection.execute(
                "SELECT vector FROM sections WHERE id = ?", (section_id,)
            ).fetchone()[0]
        finally:
            connection.close()
        self.assertIsNone(updated_vector)

    def test_similar_notes_come_from_stored_vectors(self):
        """Vectors are handed in, so this exercises the maths without a model."""
        import numpy as np

        self.build_metadata_only()
        meta = [
            (1, "alpha.md", "Planned", 6),
            (2, "alpha.md", "Long", 9),
            (3, "folder/beta.md", "Result", 1),
            (4, "folder/beta.md", "Aside", 5),
            (5, "gamma.md", "Other", 1),
        ]
        matrix = np.array(
            [
                [1.0, 0.0, 0.0],  # alpha, pooled into the query vector
                [0.0, 1.0, 0.0],
                [0.6, 0.8, 0.0],  # beta's better section
                [1.0, 0.0, 0.0],  # beta's weaker section
                [0.0, 0.0, 1.0],  # unrelated
            ],
            dtype=np.float32,
        )
        rows = INDEXER.find_similar_notes(
            "alpha", vault_path=str(self.vault), db_path=str(self.db), vectors=(meta, matrix)
        )
        # the note itself is excluded, each neighbour appears once, best section first
        self.assertEqual([row["path"] for row in rows], ["folder/beta.md", "gamma.md"])
        self.assertEqual(rows[0]["heading"], "Result")
        self.assertGreater(rows[0]["score"], 0.98)
        self.assertAlmostEqual(rows[1]["score"], 0.0, places=6)

        self.assertEqual(
            len(INDEXER.find_similar_notes(
                "alpha", vault_path=str(self.vault), db_path=str(self.db), limit=1,
                vectors=(meta, matrix),
            )),
            1,
        )
        # an unknown note is None, which is not the same as a note with no neighbours
        self.assertIsNone(INDEXER.find_similar_notes(
            "nosuchnote", vault_path=str(self.vault), db_path=str(self.db), vectors=(meta, matrix)
        ))
        self.assertEqual(
            INDEXER.find_similar_notes(
                "alpha", vault_path=str(self.vault), db_path=str(self.db),
                vectors=([], None),
            ),
            [],
        )


if __name__ == "__main__":
    unittest.main()
