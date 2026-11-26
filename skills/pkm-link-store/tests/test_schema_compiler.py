import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from link_store.db import LinkStoreDB  # noqa: E402
from link_store.schema_compiler import compile_schema  # noqa: E402


class SchemaCompilerTest(unittest.TestCase):
    def test_compile_default_schema_classes_and_rules(self):
        schema = compile_schema()
        self.assertEqual(
            schema.node_types,
            frozenset({"Note", "Session", "Repo", "Branch", "Commit", "File", "Url"}),
        )
        self.assertIn(("child_of", "Session", "Session"), schema.edge_rules)
        self.assertIn(("worked_in_branch", "Session", "Branch"), schema.edge_rules)
        self.assertIn(("read_file", "Session", "File"), schema.edge_rules)
        self.assertIn(("read_file", "Session", "Note"), schema.edge_rules)
        self.assertIn(("in_repo", "Branch", "Repo"), schema.edge_rules)
        self.assertIn(("in_repo", "Commit", "Repo"), schema.edge_rules)
        self.assertIn(("changed_file", "Commit", "Note"), schema.edge_rules)
        self.assertIn(("mentions_session", "Commit", "Session"), schema.edge_rules)

    def test_db_rejects_invalid_node_and_edge_types(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "store.db"
            with LinkStoreDB(db_path) as db:
                with self.assertRaises(ValueError):
                    db.upsert_node("bogus:1", "NotAType")

                db.upsert_node("note:v/a.md", "Note", title="a.md")
                db.upsert_node("url:https://docs.python.org/3/", "Url")
                with self.assertRaises(ValueError):
                    # Note -> Url via child_of is invalid
                    db.upsert_edge("note:v/a.md", "url:https://docs.python.org/3/", "child_of", "test")

                # Valid bitemporal edge + active uniqueness
                db.upsert_node("session:s1", "Session")
                db.upsert_edge("session:s1", "note:v/a.md", "read_file", "test", valid_from="2026-01-01T00:00:00Z")
                db.upsert_edge("session:s1", "note:v/a.md", "read_file", "test", valid_from="2026-01-01T00:00:00Z")
                cnt = db.conn.execute("SELECT COUNT(*) FROM edges WHERE expired_at IS NULL").fetchone()[0]
                self.assertEqual(cnt, 1)


if __name__ == "__main__":
    unittest.main()
