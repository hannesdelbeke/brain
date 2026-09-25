import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


SKILL = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("co_retrieval", SKILL / "co_retrieval.py")
CO_RETRIEVAL = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CO_RETRIEVAL)


class CoRetrievalOriginTest(unittest.TestCase):
    """Which logged queries are allowed to teach the graph track.

    Every case goes through `update`, the entry point the daemon calls, rather
    than through `fold` directly, so the filter is tested where it actually runs.
    """

    def fold_one(self, **extra) -> tuple[int, int]:
        """Fold a single two-result query, returning (queries folded, edges made)."""
        row = {"t": "2026-09-25T10:00:00", "vault": "test", "kind": "search",
               "q": "a query", "results": ["a.md", "b.md"], **extra}
        with tempfile.TemporaryDirectory() as temp:
            log = Path(temp) / "queries.jsonl"
            with log.open("w", encoding="utf-8") as handle:
                handle.write(json.dumps(row) + "\n")
            return CO_RETRIEVAL.update(Path(temp) / "edges.db", log)

    def test_synthetic_origin_contributes_no_edge(self):
        self.assertEqual(self.fold_one(origin="eval-gate"), (0, 0),
                         "an eval's invented query must not become an edge")

    def test_missing_origin_contributes_edge(self):
        # The normal case for real traffic: searchd writes the key only when the
        # caller passed a non-empty origin, so most rows have no origin at all.
        self.assertEqual(self.fold_one(), (1, 1),
                         "a query with no origin is real traffic and must count")

    def test_non_synthetic_origin_contributes_edge(self):
        self.assertEqual(self.fold_one(origin="cli"), (1, 1),
                         "a named non-eval origin must count")

    def test_null_origin_counts_as_real_rather_than_crashing(self):
        # `.startswith` on None raises AttributeError, which fold's except clause
        # does not catch, so an unguarded read would take down the whole run over
        # one foreign row instead of skipping it. Null means real, like absent.
        self.assertEqual(self.fold_one(origin=None), (1, 1),
                         "a null origin must count, and must not raise")

    def test_non_string_origin_does_not_raise(self):
        self.assertEqual(self.fold_one(origin=7), (1, 1),
                         "a number is not the eval prefix, and must not raise")


if __name__ == "__main__":
    unittest.main()
