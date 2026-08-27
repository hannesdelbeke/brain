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

    def test_a_repo_nested_in_the_vault_is_left_to_its_own_index(self):
        nested = self.vault / "public"
        (nested / ".git").mkdir(parents=True)
        (nested / "borrowed.md").write_text("## Elsewhere", encoding="utf-8")
        found = {path.name for path in INDEXER.markdown_paths(self.vault)}
        self.assertEqual(found, {"alpha.md", "beta.md"})

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

    def test_query_path_caps_the_onnx_thread_pool(self):
        """The idle CPU burn comes back if the query path stops passing threads."""
        calls = []

        class FakeModel:
            def __init__(self, **kwargs):
                calls.append(kwargs)

        original_model, original_cache = INDEXER.TextEmbedding, INDEXER._MODEL_CACHE
        INDEXER.TextEmbedding, INDEXER._MODEL_CACHE = FakeModel, {}
        try:
            INDEXER.get_embedding_model(INDEXER.QUERY_PROVIDERS, INDEXER.QUERY_THREADS)
            INDEXER.get_embedding_model(INDEXER.QUERY_PROVIDERS)  # the indexing path
            INDEXER.get_embedding_model(INDEXER.QUERY_PROVIDERS, INDEXER.QUERY_THREADS)  # cached
        finally:
            INDEXER.TextEmbedding, INDEXER._MODEL_CACHE = original_model, original_cache

        self.assertEqual(INDEXER.QUERY_THREADS, 1)
        self.assertEqual(len(calls), 2, "threads must be part of the cache key")
        self.assertEqual(calls[0].get("threads"), 1)
        self.assertNotIn("threads", calls[1], "bulk embedding keeps the full pool")


class RerankTest(unittest.TestCase):
    """The model is fastembed's; what is ours is the text it is handed and the order out."""

    class FakeCrossEncoder:
        def __init__(self):
            self.documents = None

        def rerank(self, query, documents):
            self.documents = list(documents)
            # scores rising down the list, so the order flips and a passthrough fails
            return [float(index) for index in range(1, len(self.documents) + 1)]

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.vault = Path(self.temp_dir.name) / "vault"
        (self.vault / ".obsidian").mkdir(parents=True)
        self.db = self.vault / ".obsidian" / "pkm_index.db"
        (self.vault / "alpha.md").write_text(
            "## First\nA distinctivephrase about batteries.\n"
            "## Second\nAnother distinctivephrase, this time about solar.\n",
            encoding="utf-8",
        )
        INDEXER.build_index(vault_path=str(self.vault), db_path=str(self.db), skip_embeddings=True)
        self.fake = self.FakeCrossEncoder()
        INDEXER._RERANK_CACHE["model"] = self.fake
        self.addCleanup(INDEXER._RERANK_CACHE.pop, "model", None)

    def search(self, rerank):
        return INDEXER.search_index("distinctivephrase", db_path=str(self.db),
                                    limit=5, rerank=rerank)

    def test_the_cross_encoder_decides_the_order(self):
        fused = [row["path"] + row["heading"] for row in self.search(False)]
        reranked = [row["path"] + row["heading"] for row in self.search(True)]
        self.assertEqual(reranked, list(reversed(fused)))
        self.assertTrue(all("rerank_score" in row for row in self.search(True)))

    def test_it_reranks_the_section_text_not_the_snippet(self):
        self.search(True)
        self.assertTrue(any("solar" in document for document in self.fake.documents),
                        "the indexed section content is what the model has to read")

    def test_fusion_alone_leaves_no_rerank_score(self):
        self.assertTrue(all("rerank_score" not in row for row in self.search(False)))


if __name__ == "__main__":
    unittest.main()
