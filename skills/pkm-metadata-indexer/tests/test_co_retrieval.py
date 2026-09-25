import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


SKILL = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("co_retrieval", SKILL / "co_retrieval.py")
CO_RETRIEVAL = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CO_RETRIEVAL)


class CoRetrievalTest(unittest.TestCase):
    def test_synthetic_origin_contributes_no_edge(self):
        """Log rows with origin=eval-* must not create co-retrieval edges."""
        with tempfile.TemporaryDirectory() as temp:
            log = Path(temp) / "queries.jsonl"
            db = Path(temp) / "edges.db"
            with log.open("w", encoding="utf-8") as handle:
                handle.write(json.dumps({
                    "t": "2026-09-25T10:00:00",
                    "vault": "test",
                    "kind": "search",
                    "q": "synthetic query",
                    "origin": "eval-gate",
                    "results": ["a.md", "b.md"]
                }) + "\n")
            folded, edges = CO_RETRIEVAL.update(db, log)
            self.assertEqual(folded, 0, "eval-gate query must not be folded")
            self.assertEqual(edges, 0, "no edges from synthetic traffic")

    def test_missing_origin_contributes_edge(self):
        """Log rows without an origin key are real traffic and must count."""
        with tempfile.TemporaryDirectory() as temp:
            log = Path(temp) / "queries.jsonl"
            db = Path(temp) / "edges.db"
            with log.open("w", encoding="utf-8") as handle:
                handle.write(json.dumps({
                    "t": "2026-09-25T10:00:00",
                    "vault": "test",
                    "kind": "search",
                    "q": "real query",
                    "results": ["a.md", "b.md"]
                }) + "\n")
            folded, edges = CO_RETRIEVAL.update(db, log)
            self.assertEqual(folded, 1, "query without origin must be folded")
            self.assertEqual(edges, 1, "one pair creates one edge")

    def test_non_synthetic_origin_contributes_edge(self):
        """Log rows with a non-synthetic origin (e.g. cli) must count."""
        with tempfile.TemporaryDirectory() as temp:
            log = Path(temp) / "queries.jsonl"
            db = Path(temp) / "edges.db"
            with log.open("w", encoding="utf-8") as handle:
                handle.write(json.dumps({
                    "t": "2026-09-25T10:00:00",
                    "vault": "test",
                    "kind": "search",
                    "q": "cli query",
                    "origin": "cli",
                    "results": ["a.md", "b.md"]
                }) + "\n")
            folded, edges = CO_RETRIEVAL.update(db, log)
            self.assertEqual(folded, 1, "cli origin query must be folded")
            self.assertEqual(edges, 1, "one pair creates one edge")


if __name__ == "__main__":
    unittest.main()
