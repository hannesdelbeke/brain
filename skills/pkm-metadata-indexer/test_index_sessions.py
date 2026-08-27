import json
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import index_pkm_meta as pkm  # noqa: E402
import index_sessions  # noqa: E402


def line(payload: dict) -> str:
    return json.dumps(payload) + "\n"


def user(text, **extra):
    return line({"type": "user", "uuid": text[:8], "message": {"content": text}, **extra})


def assistant(message_id, blocks):
    return line({"type": "assistant", "message": {"id": message_id, "content": blocks}})


class SessionIndexerTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name) / "projects"
        session = self.root / "some-project"
        (session / "aaa" / "subagents").mkdir(parents=True)
        self.db = self.root / ".pkm_index.db"

        (session / "aaa.jsonl").write_text(
            line({"type": "summary", "summary": "ignored record type"})
            + user("<command-name>/clear</command-name> and more text to clear the floor")
            + user("Caveat: injected by the client, not typed by anyone at all", isMeta=True)
            + user("ok")  # under the floor
            + user("make the distinctivephrase widget stop crashing on startup")
            + assistant("msg_1", [
                {"type": "thinking", "thinking": "skipped, and long enough to pass the floor"},
                {"type": "text", "text": "Looking at it now, the crash is in the loader."},
                {"type": "tool_use", "name": "Bash", "input": {"command": "pytest -k widget", "timeout": 5}},
                {"type": "tool_use", "name": "Edit", "input": {"file_path": "src/loader.py", "old_string": "x"}},
            ])
            # The same message id and blocks written again, as the client does.
            + assistant("msg_1", [{"type": "text", "text": "Looking at it now, the crash is in the loader."}])
            + line({"type": "user", "message": {"content": [
                {"type": "tool_result", "content": "SECRET_TOKEN=hunter2 " + "x" * 500}
            ]}}),
            encoding="utf-8",
        )
        (session / "aaa" / "subagents" / "agent-1.jsonl").write_text(
            user("go and find every caller of the loader function please"), encoding="utf-8"
        )
        (session / "aaa" / "subagents" / "agent-1.meta.json").write_text(
            json.dumps({"agentType": "general-purpose", "description": "Find loader callers"}),
            encoding="utf-8",
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_scan_keeps_prose_and_tool_arguments_and_drops_the_rest(self):
        events = list(index_sessions.iter_events(self.root / "some-project" / "aaa.jsonl"))
        texts = [event.text for event in events]
        self.assertEqual(
            texts,
            [
                "make the distinctivephrase widget stop crashing on startup",
                "Looking at it now, the crash is in the loader.",
                "Bash command: pytest -k widget",
                "Edit file_path: src/loader.py",
            ],
        )
        # Line numbers point at the jsonl line so a hit opens where it happened.
        self.assertEqual([event.line for event in events], [5, 6, 6, 6])
        self.assertEqual(events[-1].files, ("src/loader.py",))

    def test_index_is_searchable_and_carries_the_session_graph(self):
        pkm.build_index(
            vault_path=str(self.root),
            db_path=str(self.db),
            skip_embeddings=True,
            collect=index_sessions.scan_sessions,
        )
        connection = sqlite3.connect(self.db)
        try:
            cursor = connection.cursor()
            rows = pkm.search_index("distinctivephrase", db_path=str(self.db), limit=5, vectors=([], None))
            self.assertEqual(rows[0]["path"], "some-project/aaa.jsonl")
            self.assertEqual(rows[0]["start_line"], 5)

            titles = dict(cursor.execute("SELECT path, filename FROM notes"))
            self.assertEqual(titles["some-project/aaa.jsonl"],
                             "make the distinctivephrase widget stop crashing on startup")
            # A subagent is titled by its spawn description, not its first prompt.
            self.assertEqual(titles["some-project/aaa/subagents/agent-1.jsonl"], "Find loader callers")

            edges = set(cursor.execute("SELECT source_path, raw_target FROM edges"))
            self.assertIn(("some-project/aaa.jsonl", "src/loader.py"), edges)
            self.assertIn(("some-project/aaa/subagents/agent-1.jsonl", "some-project/aaa.jsonl"), edges)

            # Tool results are never indexed, whatever they contain.
            self.assertEqual(
                cursor.execute("SELECT COUNT(*) FROM sections_fts WHERE content MATCH 'SECRET_TOKEN'").fetchone()[0],
                0,
            )
        finally:
            connection.close()

    def build(self):
        pkm.build_index(vault_path=str(self.root), db_path=str(self.db), skip_embeddings=True,
                        collect=lambda root: index_sessions.scan_sessions(root, self.db))

    def sections_for(self, path):
        connection = sqlite3.connect(self.db)
        try:
            return dict(connection.execute(
                "SELECT sections.id, sections_fts.content FROM sections"
                " JOIN sections_fts ON sections_fts.section_id = sections.id"
                " WHERE sections.path = ?", (path,)))
        finally:
            connection.close()

    def test_an_appended_transcript_is_read_from_the_last_offset(self):
        transcript = self.root / "some-project" / "aaa.jsonl"
        self.build()
        before = self.sections_for("some-project/aaa.jsonl")
        state = json.loads((self.root / index_sessions.STATE_NAME).read_text())["files"]
        self.assertEqual(state["some-project/aaa.jsonl"]["offset"], transcript.stat().st_size)

        with transcript.open("a", encoding="utf-8") as handle:
            handle.write(user("and now the appendedphrase turns up in a later turn"))
        self.build()

        after = self.sections_for("some-project/aaa.jsonl")
        # The rows already indexed survive untouched, and only the new turn is added.
        self.assertEqual(before, {key: after[key] for key in before})
        self.assertEqual(len(after), len(before) + 1)
        rows = pkm.search_index("appendedphrase", db_path=str(self.db), limit=5, vectors=([], None))
        self.assertEqual(rows[0]["start_line"], 9)

    def test_a_rewritten_transcript_is_read_in_full(self):
        transcript = self.root / "some-project" / "aaa.jsonl"
        self.build()
        transcript.write_text(user("a different session about the rewrittenphrase entirely")
                              + user("padding so the file is longer than the one it replaced" * 5),
                              encoding="utf-8")
        self.build()

        texts = list(self.sections_for("some-project/aaa.jsonl").values())
        self.assertTrue(any("rewrittenphrase" in text for text in texts))
        self.assertFalse(any("distinctivephrase" in text for text in texts))

    def test_a_half_written_last_line_waits_for_the_rest_of_itself(self):
        transcript = self.root / "some-project" / "aaa.jsonl"
        with transcript.open("a", encoding="utf-8") as handle:
            handle.write(user("the halfwrittenphrase turn is still being written").rstrip("\n"))
        self.build()
        self.assertEqual(pkm.search_index("halfwrittenphrase", db_path=str(self.db), limit=5,
                                          vectors=([], None)), [])

        with transcript.open("a", encoding="utf-8") as handle:
            handle.write("\n")
        self.build()
        rows = pkm.search_index("halfwrittenphrase", db_path=str(self.db), limit=5, vectors=([], None))
        self.assertEqual(rows[0]["start_line"], 9)

    def test_editing_the_scanner_invalidates_every_offset(self):
        state_file = self.root / index_sessions.STATE_NAME
        self.build()
        state = json.loads(state_file.read_text())
        state["scanner"] = "not-this-scanner"
        state_file.write_text(json.dumps(state), encoding="utf-8")
        self.assertEqual(index_sessions.read_state(state_file), {})

    def test_default_db_sits_beside_a_corpus_that_is_not_a_vault(self):
        self.assertEqual(pkm.default_db_path(self.root), self.root / ".pkm_index.db")
        vault = self.root / "vault"
        (vault / ".obsidian").mkdir(parents=True)
        self.assertEqual(pkm.default_db_path(vault), vault / ".obsidian" / "pkm_index.db")


if __name__ == "__main__":
    unittest.main()
