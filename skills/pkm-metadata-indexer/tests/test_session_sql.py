import importlib.util
import sqlite3
import tempfile
import time
import unittest
from pathlib import Path


SKILL = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("test_indexer", SKILL / "index_pkm_meta.py")
INDEXER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(INDEXER)


class SessionSqlTest(unittest.TestCase):
    def test_session_provenance_projection_and_speed(self):
        with tempfile.TemporaryDirectory() as temp:
            vault = Path(temp) / "vault"
            session_dir = vault / "sessions"
            (vault / ".obsidian").mkdir(parents=True)
            session_dir.mkdir()
            (session_dir / "rollup.md").write_text(
                "---\nsession_id: session-1\ndate: 2026-09-24\ntrace_path: traces/session-1.jsonl\n"
                "cost_usd: 1.25\nrepo: example/repo\ntouched:\n"
                "  - target: scripts/example.py\n    action: modified\n---\n"
                "## Vault conventions backfill\n", encoding="utf-8"
            )
            database = vault / ".obsidian" / "pkm_index.db"
            INDEXER.build_index(str(vault), str(database), skip_embeddings=True)
            connection = sqlite3.connect(database)
            try:
                start = time.perf_counter()
                rows = connection.execute(
                    "SELECT session_id, title FROM sessions_idx WHERE title LIKE '%vault conventions%'"
                ).fetchall()
                elapsed = time.perf_counter() - start
                touches = connection.execute(
                    "SELECT action FROM session_touches WHERE target_path = 'scripts/example.py'"
                ).fetchall()
            finally:
                connection.close()
            self.assertEqual(rows, [("session-1", "Vault conventions backfill")])
            self.assertEqual(touches, [("modified",)])
            self.assertLess(elapsed, 0.005, f"Session query too slow: {elapsed}s")

    def test_vault_flag_extraction(self):
        with tempfile.TemporaryDirectory() as temp:
            vault = Path(temp) / "vault"
            session_dir = vault / "sessions"
            (vault / ".obsidian").mkdir(parents=True)
            session_dir.mkdir()
            (session_dir / "with-vault-flags.md").write_text(
                "---\nsession_id: session-2\ndate: 2026-09-25\n"
                "touched:\n"
                "  - target: some note title\n    action: edited\n    vault: true\n"
                "  - target: repo/src/file.py\n    action: edited\n    vault: false\n"
                "  - target: other file\n    action: read\n---\n"
                "## Test session\n", encoding="utf-8"
            )
            database = vault / ".obsidian" / "pkm_index.db"
            INDEXER.build_index(str(vault), str(database), skip_embeddings=True)
            connection = sqlite3.connect(database)
            try:
                touches = connection.execute(
                    "SELECT target_path, vault FROM session_touches WHERE session_id = 'session-2' "
                    "ORDER BY target_path"
                ).fetchall()
            finally:
                connection.close()
            self.assertEqual(touches, [
                ("other file", None),
                ("repo/src/file.py", 0),
                ("some note title", 1),
            ])

    def test_touched_filter(self):
        with tempfile.TemporaryDirectory() as temp:
            vault = Path(temp) / "vault"
            session_dir = vault / "sessions"
            (vault / ".obsidian").mkdir(parents=True)
            session_dir.mkdir()
            (session_dir / "notes-only.md").write_text(
                "---\nsession_id: session-notes\ndate: 2026-09-25\n"
                "touched:\n"
                "  - target: concept.md\n    action: edited\n    vault: true\n---\n"
                "## Notes session\n", encoding="utf-8"
            )
            (session_dir / "code-only.md").write_text(
                "---\nsession_id: session-code\ndate: 2026-09-25\n"
                "touched:\n"
                "  - target: src/main.py\n    action: edited\n    vault: false\n---\n"
                "## Code session\n", encoding="utf-8"
            )
            (session_dir / "mixed.md").write_text(
                "---\nsession_id: session-mixed\ndate: 2026-09-25\n"
                "touched:\n"
                "  - target: notes.md\n    action: edited\n    vault: true\n"
                "  - target: src/util.py\n    action: edited\n    vault: false\n---\n"
                "## Mixed session\n", encoding="utf-8"
            )
            database = vault / ".obsidian" / "pkm_index.db"
            INDEXER.build_index(str(vault), str(database), skip_embeddings=True)

            results_any = INDEXER.query_sessions("session", db_path=str(database), limit=10, touched="any")
            self.assertEqual(len(results_any), 3)
            self.assertEqual(
                {r["session_id"] for r in results_any},
                {"session-notes", "session-code", "session-mixed"}
            )

            results_notes = INDEXER.query_sessions("py", db_path=str(database), limit=10, touched="notes")
            self.assertEqual(len(results_notes), 0)

            results_code = INDEXER.query_sessions("py", db_path=str(database), limit=10, touched="code")
            self.assertEqual(len(results_code), 2)
            self.assertEqual(
                {r["session_id"] for r in results_code},
                {"session-code", "session-mixed"}
            )

    def test_session_touches_vault_migration(self):
        """ensure_schema adds vault column to existing three-column session_touches table."""
        with tempfile.TemporaryDirectory() as temp:
            database = Path(temp) / "test.db"
            connection = sqlite3.connect(database)
            try:
                # simulate old schema: three-column session_touches table
                connection.execute("PRAGMA journal_mode=WAL;")
                connection.execute(
                    """
                    CREATE TABLE sessions_idx (
                        session_id TEXT PRIMARY KEY,
                        title TEXT NOT NULL,
                        created TEXT,
                        trace_path TEXT,
                        cost_usd REAL,
                        repo TEXT,
                        note_path TEXT NOT NULL
                    )
                    """
                )
                connection.execute(
                    """
                    CREATE TABLE session_touches (
                        session_id TEXT NOT NULL,
                        target_path TEXT NOT NULL,
                        action TEXT,
                        PRIMARY KEY (session_id, target_path, action),
                        FOREIGN KEY (session_id) REFERENCES sessions_idx(session_id)
                    )
                    """
                )
                connection.commit()

                # verify old schema has only three columns
                columns_before = {row[1] for row in connection.execute("PRAGMA table_info(session_touches)")}
                self.assertEqual(columns_before, {"session_id", "target_path", "action"})

                # run schema migration
                INDEXER.ensure_schema(connection)

                # verify vault column was added
                columns_after = {row[1] for row in connection.execute("PRAGMA table_info(session_touches)")}
                self.assertIn("vault", columns_after)
                self.assertEqual(columns_after, {"session_id", "target_path", "action", "vault"})

                # verify four-column insert succeeds
                connection.execute("INSERT INTO sessions_idx(session_id, title, note_path) VALUES (?, ?, ?)",
                                   ("test-session", "Test Session", "sessions/test.md"))
                connection.execute(
                    "INSERT INTO session_touches(session_id, target_path, action, vault) VALUES (?, ?, ?, ?)",
                    ("test-session", "test.md", "edited", 1)
                )
                connection.commit()

                # verify the row was inserted correctly
                row = connection.execute(
                    "SELECT session_id, target_path, action, vault FROM session_touches"
                ).fetchone()
                self.assertEqual(row, ("test-session", "test.md", "edited", 1))
            finally:
                connection.close()

    def test_trace_path_body_extraction(self):
        """extract trace path from body section when not in frontmatter."""
        with tempfile.TemporaryDirectory() as temp:
            vault = Path(temp) / "vault"
            session_dir = vault / "sessions"
            (vault / ".obsidian").mkdir(parents=True)
            session_dir.mkdir()
            # note with trace in body, exact case
            (session_dir / "with-trace.md").write_text(
                "---\nsession_id: session-trace\ndate: 2026-09-25\n---\n"
                "## Summary\nSome content\n\n"
                "## the full trace is at traces/2026-09-25_session-trace-id\n\n"
                "Every turn is recorded.\n", encoding="utf-8"
            )
            # note with trace in body, different case and extra whitespace
            (session_dir / "with-trace-case.md").write_text(
                "---\nsession_id: session-case\ndate: 2026-09-25\n---\n"
                "## Summary\nSome content\n\n"
                "##  The  FULL  Trace  IS  At  traces/2026-09-25_case-insensitive\n\n"
                "Every turn is recorded.\n", encoding="utf-8"
            )
            # note without trace in body
            (session_dir / "no-trace.md").write_text(
                "---\nsession_id: session-no-trace\ndate: 2026-09-25\n---\n"
                "## Summary\nSome content\n", encoding="utf-8"
            )
            # note with trace in frontmatter (should use frontmatter value)
            (session_dir / "trace-frontmatter.md").write_text(
                "---\nsession_id: session-fm\ndate: 2026-09-25\n"
                "trace_path: traces/from-frontmatter\n---\n"
                "## the full trace is at traces/should-not-use-this\n", encoding="utf-8"
            )
            database = vault / ".obsidian" / "pkm_index.db"
            INDEXER.build_index(str(vault), str(database), skip_embeddings=True)
            connection = sqlite3.connect(database)
            try:
                traces = connection.execute(
                    "SELECT session_id, trace_path FROM sessions_idx ORDER BY session_id"
                ).fetchall()
            finally:
                connection.close()
            self.assertEqual(traces, [
                ("session-case", "traces/2026-09-25_case-insensitive"),
                ("session-fm", "traces/from-frontmatter"),
                ("session-no-trace", None),
                ("session-trace", "traces/2026-09-25_session-trace-id"),
            ])

    def test_duplicate_session_id_deduplication(self):
        """deduplicate session_id when a session is continued into a second note.

        when a session continues into a second note, both notes share the same
        session_id and may list different touched files. the sessions_idx table
        has session_id as PRIMARY KEY, so duplicates would abort a whole-corpus
        reindex. this test verifies that:
        1. exactly one row per session_id survives in sessions_idx
        2. the winning row has the trace_path (if any note has one)
        3. touch rows from both notes are present (merged via INSERT OR IGNORE)
        4. the deduplication count is correctly returned
        """
        with tempfile.TemporaryDirectory() as temp:
            vault = Path(temp) / "vault"
            session_dir = vault / "sessions"
            (vault / ".obsidian").mkdir(parents=True)
            session_dir.mkdir()
            # first note: has trace_path, touches file_a.py
            (session_dir / "2026-09-20-session-start.md").write_text(
                "---\nsession_id: continued-session\ndate: 2026-09-20\n"
                "trace_path: traces/continued-session.jsonl\n"
                "touched:\n"
                "  - target: file_a.py\n    action: created\n    vault: false\n---\n"
                "## First session\n", encoding="utf-8"
            )
            # second note: same session_id, no trace_path, touches file_b.py
            (session_dir / "2026-09-21-session-continued.md").write_text(
                "---\nsession_id: continued-session\ndate: 2026-09-21\n"
                "touched:\n"
                "  - target: file_b.py\n    action: modified\n    vault: false\n---\n"
                "## Continued work\n", encoding="utf-8"
            )

            # verify the deduplication count is correctly returned
            session_rows, touch_rows, dedup_count = INDEXER.session_frontmatter_rows(vault)
            self.assertEqual(dedup_count, 1, "expected deduplication count of 1 for one session spanning two notes")
            self.assertEqual(len(session_rows), 1, "expected one session row after deduplication")
            self.assertEqual(len(touch_rows), 2, "expected two touch rows from both notes")

            database = vault / ".obsidian" / "pkm_index.db"
            INDEXER.build_index(str(vault), str(database), skip_embeddings=True)
            connection = sqlite3.connect(database)
            try:
                # verify exactly one sessions_idx row for the shared session_id
                session_rows = connection.execute(
                    "SELECT session_id, trace_path, note_path FROM sessions_idx "
                    "WHERE session_id = 'continued-session'"
                ).fetchall()
                self.assertEqual(len(session_rows), 1, "expected exactly one sessions_idx row for duplicate session_id")
                session_id, trace_path, note_path = session_rows[0]
                self.assertEqual(session_id, "continued-session")
                # the row with the trace_path should win
                self.assertEqual(trace_path, "traces/continued-session.jsonl", "expected the row with trace_path to win")
                self.assertEqual(note_path, "sessions/2026-09-20-session-start.md")

                # verify touch rows from both notes are present
                touches = connection.execute(
                    "SELECT target_path, action FROM session_touches "
                    "WHERE session_id = 'continued-session' ORDER BY target_path"
                ).fetchall()
                self.assertEqual(len(touches), 2, "expected touch rows from both notes")
                self.assertEqual(touches, [
                    ("file_a.py", "created"),
                    ("file_b.py", "modified"),
                ])
            finally:
                connection.close()


if __name__ == "__main__":
    unittest.main()
