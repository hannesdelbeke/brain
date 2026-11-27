import contextlib
import io
import json
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from link_store import cli  # noqa: E402
from link_store.adapters import (  # noqa: E402
    BoundaryPolicy,
    reconcile_sessions,
    sync_claude_root,
    sync_git_repo,
    sync_vault,
)
from link_store.db import LinkStoreDB  # noqa: E402

A = "aaaaaaaa-0000-4000-8000-000000000001"
B = "bbbbbbbb-0000-4000-8000-000000000002"
C = "cccccccc-0000-4000-8000-000000000003"
# Two sessions sharing an 8-char prefix.
D1 = "dddddddd-0000-4000-8000-000000000004"
D2 = "dddddddd-0000-4000-8000-000000000005"


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(repo), *args], capture_output=True, check=True)


def _init_repo(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    _git(path, "init", "-q", "-b", "main")
    _git(path, "config", "user.name", "Test Bot")
    _git(path, "config", "user.email", "test@example.invalid")
    _git(path, "remote", "add", "origin", "https://github.com/org/demo.git")


def _commit(repo: Path, name: str, message: str) -> None:
    (repo / name).write_text("x\n", encoding="utf-8")
    _git(repo, "add", name)
    _git(repo, "commit", "-q", "-m", message)


def _jsonl(path: Path, records: list[dict], mode: str = "w") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open(mode, encoding="utf-8") as fh:
        fh.writelines(json.dumps(r) + "\n" for r in records)


def _edges(db: LinkStoreDB, rel: str) -> set[tuple[str, str]]:
    return {
        (r["src_id"], r["dst_id"])
        for r in db.conn.execute(
            "SELECT src_id, dst_id FROM edges WHERE rel = ? AND expired_at IS NULL", (rel,)
        )
    }


class _Case(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name).resolve()
        self.claude = self.root / "projects"
        self.vault = self.root / "vault"
        _init_repo(self.vault)
        (self.vault / "design.md").write_text("# Design\n", encoding="utf-8")
        self.policy = BoundaryPolicy.from_args(vault_roots={"brain": self.vault})
        self.db = LinkStoreDB(self.root / "store.db")
        self.addCleanup(self.db.close)

    def transcript(self, uuid: str) -> Path:
        return self.claude / "proj" / f"{uuid}.jsonl"

    def user(self, uuid: str, **extra) -> dict:
        return {
            "type": "user",
            "sessionId": uuid,
            "cwd": str(self.vault),
            "timestamp": "2026-05-01T10:00:00Z",
            **extra,
        }

    def sync(self) -> dict:
        return sync_claude_root(self.db, self.claude, policy=self.policy)


class RecordTypeTest(_Case):
    def test_lineage_records(self):
        _jsonl(self.transcript(A), [
            self.user(A),
            {"type": "continued-in", "sessionId": A, "continuedInSessionId": B,
             "timestamp": "2026-05-01T11:00:00Z"},
        ])
        _jsonl(self.transcript(B), [
            self.user(B),
            {"type": "derived-from", "sessionId": B, "v": 1, "sessions": [
                {"id": A, "type": "claude_code_session", "via": "compact"},
                {"id": A, "type": "claude_code_session", "via": "fork"},
                {"id": B, "type": "claude_code_session", "via": "compact"},
            ]},
        ])
        agent = self.claude / "proj" / B / "subagents" / "agent-f1.jsonl"
        # No sessionId or cwd, as Claude Code writes it.
        _jsonl(agent, [{"type": "fork-context-ref", "agentId": "f1", "parentSessionId": A,
                        "parentLastUuid": "x", "contextLength": 3}])
        self.sync()

        self.assertEqual(_edges(self.db, "continued_in"), {(f"session:{A}", f"session:{B}")})
        # The self-reference is dropped.
        self.assertEqual(_edges(self.db, "derived_from"), {(f"session:{B}", f"session:{A}")})
        meta = self.db.conn.execute(
            "SELECT metadata_json FROM edges WHERE rel = 'derived_from'"
        ).fetchone()[0]
        self.assertEqual(json.loads(meta)["via"], ["compact", "fork"])
        child = f"session:{B}:agent-f1"
        self.assertIn((child, f"session:{A}"), _edges(self.db, "child_of"))
        self.assertIn((child, f"session:{B}"), _edges(self.db, "child_of"))

    def test_titles_become_labels_and_aliases_and_survive_later_syncs(self):
        _jsonl(self.transcript(A), [
            self.user(A),
            {"type": "ai-title", "sessionId": A, "aiTitle": "Build the link store"},
        ])
        self.sync()
        node = self.db.get_node(f"session:{A}")
        self.assertEqual(node["title"], "Build the link store")
        self.assertEqual(self.db.resolve_alias("Build the link store"), f"session:{A}")

        _jsonl(self.transcript(A), [
            {"type": "agent-name", "sessionId": A, "agentName": "link-builder"},
            {"type": "ai-title", "sessionId": A, "aiTitle": "Link store, phase 2"},
        ], mode="a")
        # A subagent ingested later re-upserts the parent node.
        _jsonl(self.claude / "proj" / A / "subagents" / "agent-s1.jsonl",
               [self.user(A, agentId="s1")])
        self.sync()
        node = self.db.get_node(f"session:{A}")
        self.assertEqual(node["title"], "link-builder")  # agent-name wins
        meta = json.loads(node["metadata_json"])
        self.assertEqual(meta["ai_title"], "Link store, phase 2")
        self.assertEqual(meta["source_file"], f"proj/{A}.jsonl")
        self.assertEqual(self.db.resolve_alias("link-builder"), f"session:{A}")
        self.assertEqual(self.db.resolve_alias("Link store, phase 2"), f"session:{A}")
        self.assertIsNone(self.db.resolve_alias("Build the link store"))

    def test_shared_and_path_like_titles_get_no_alias(self):
        for uuid in (A, B):
            _jsonl(self.transcript(uuid), [
                self.user(uuid),
                {"type": "ai-title", "sessionId": uuid, "aiTitle": "Same title"},
            ])
        _jsonl(self.transcript(C), [
            self.user(C),
            {"type": "ai-title", "sessionId": C, "aiTitle": "design.md"},
        ])
        self.sync()
        self.assertIsNone(self.db.resolve_alias("Same title"))
        self.assertIsNone(self.db.resolve_alias("design.md"))

        # Once only one session holds the label, it resolves again.
        _jsonl(self.transcript(B), [
            {"type": "ai-title", "sessionId": B, "aiTitle": "Other title"},
        ], mode="a")
        self.sync()
        self.assertEqual(self.db.resolve_alias("Same title"), f"session:{A}")

    def test_note_alias_outranks_session_label(self):
        _jsonl(self.transcript(A), [
            self.user(A),
            {"type": "ai-title", "sessionId": A, "aiTitle": "Taskwarrior setup"},
        ])
        self.sync()
        (self.vault / "tasks.md").write_text(
            "---\naliases: [Taskwarrior setup]\n---\n", encoding="utf-8")
        sync_vault(self.db, "brain", self.vault, policy=self.policy)
        self.assertEqual(self.db.resolve_alias("Taskwarrior setup"), "note:brain/tasks.md")

    def test_attachments(self):
        _jsonl(self.transcript(A), [
            self.user(A, type="attachment", attachment={
                "type": "compact_file_reference",
                "filename": str(self.vault / "design.md"), "displayPath": "design.md"}),
            self.user(A, type="attachment", attachment={
                "type": "edited_text_file", "displayPath": "src/app.py",
                "snippet": "https://snippet.invalid/must-not-be-read"}),
            self.user(A, type="attachment", attachment={
                "type": "remote_session_change", "url": "https://claude.ai/code/session_abc"}),
            self.user(A, type="attachment", attachment={
                "type": "remote_session_change", "url": None}),
        ])
        self.sync()
        self.assertEqual(
            _edges(self.db, "read_file"),
            {(f"session:{A}", "note:brain/design.md"),
             (f"session:{A}", "file:github.com/org/demo@src/app.py")},
        )
        self.assertEqual(_edges(self.db, "modified_file"), set())
        self.assertEqual(
            _edges(self.db, "cited_url"),
            {(f"session:{A}", "url:https://claude.ai/code/session_abc")},
        )

    def test_command_urls_without_tool_results_or_crashes(self):
        _jsonl(self.transcript(A), [
            self.user(A, type="assistant", message={"content": [
                {"type": "tool_use", "name": "Bash", "input": {
                    "command": "curl http://$HOST:$PORT/x https://api.github.test/repos"}},
            ]}),
            self.user(A, message={"content": [
                {"type": "tool_result", "content": "https://from-result.invalid/x"},
            ]}),
        ])
        self.sync()
        self.assertEqual(
            _edges(self.db, "cited_url"),
            {(f"session:{A}", "url:https://api.github.test/repos")},
        )
        self.assertIsNone(self.db.get_node("url:https://from-result.invalid/x"))

    def test_detached_head_creates_no_branch(self):
        _jsonl(self.transcript(A), [
            self.user(A, gitBranch="HEAD"),
            self.user(A, gitBranch="feat/x", timestamp="2026-05-01T10:01:00Z"),
            self.user(A, gitBranch="HEAD", timestamp="2026-05-01T10:02:00Z"),
        ])
        self.sync()
        branches = [r[0] for r in self.db.conn.execute(
            "SELECT id FROM nodes WHERE node_type = 'Branch'")]
        self.assertEqual(branches, ["branch:github.com/org/demo@feat/x"])
        self.assertEqual(len(_edges(self.db, "worked_in_branch")), 1)

    def test_preamble_of_a_denied_transcript_is_not_ingested(self):
        _jsonl(self.transcript(A), [
            {"type": "ai-title", "sessionId": A, "aiTitle": "secret title"},
            self.user(A),
        ])
        policy = BoundaryPolicy.from_args(deny_roots=[self.vault])
        sync_claude_root(self.db, self.claude, policy=policy)
        self.assertIsNone(self.db.get_node(f"session:{A}"))

    def test_old_parser_state_rereads_transcript(self):
        _jsonl(self.transcript(A), [self.user(A)])
        self.sync()
        self.assertEqual(self.sync()["records"], 0)
        with self.db.conn:
            self.db.conn.execute(
                "UPDATE sync_state SET extra_json = json_remove(extra_json, '$.parser_version')")
        self.assertEqual(self.sync()["records"], 1)


class ShortIdTest(_Case):
    def test_alias_only_while_unambiguous(self):
        _jsonl(self.transcript(D1), [self.user(D1)])
        _jsonl(self.claude / "proj" / D1 / "subagents" / "agent-s1.jsonl",
               [self.user(D1, agentId="s1")])
        self.sync()
        alias = self.db.get_alias("dddddddd")
        self.assertEqual(alias["node_id"], f"session:{D1}")
        self.assertEqual(alias["alias_kind"], "short_id")

        _jsonl(self.transcript(D2), [self.user(D2)])
        self.sync()
        self.assertIsNone(self.db.resolve_alias("dddddddd"))

        # Expiring one makes the prefix unique again.
        self.db.expire_node(f"session:{D1}")
        self.db.refresh_short_id_alias("dddddddd")
        self.assertEqual(self.db.resolve_alias("dddddddd"), f"session:{D2}")

    def test_ambiguity_drops_every_spelling_of_the_short_alias(self):
        self.db.upsert_node(f"session:{D1}", "Session")
        self.db.upsert_alias("DDDDDDDD", f"session:{D1}", alias_kind="short_id")
        self.db.upsert_node(f"session:{D2}", "Session")
        self.db.refresh_short_id_alias("dddddddd")
        self.assertIsNone(self.db.resolve_alias("DDDDDDDD"))
        self.assertIsNone(self.db.resolve_alias("dddddddd"))

    def test_existing_store_gains_alias_kind_column(self):
        path = self.root / "old.db"
        conn = sqlite3.connect(path)
        conn.execute("CREATE TABLE aliases (alias TEXT PRIMARY KEY, node_id TEXT NOT NULL, "
                     "recorded_at TEXT NOT NULL)")
        conn.commit()
        conn.close()
        with LinkStoreDB(path) as db:
            db.upsert_node(f"session:{A}", "Session")
            db.upsert_alias("aaaaaaaa", f"session:{A}", alias_kind="short_id")
            self.assertEqual(db.get_alias("aaaaaaaa")["alias_kind"], "short_id")


class GitTrailerTest(_Case):
    def sync_git(self) -> dict:
        return sync_git_repo(self.db, "brain", self.vault, policy=self.policy)

    def test_short_trailer_prefix_fallback_and_no_orphan_stubs(self):
        # No aliases: forces the prefix query. The subagent must not count.
        for node in (f"session:{A}", f"session:{A}:agent-s1",
                     f"session:{D1}", f"session:{D2}"):
            self.db.upsert_node(node, "Session")
        _commit(self.vault, "a.txt", "a\n\nSession: AAAAAAAA")
        _commit(self.vault, "d.txt", "d\n\nSession: dddddddd")
        _commit(self.vault, "c.txt", "c\n\nSession: cccccccc")
        res = self.sync_git()
        self.assertEqual([dst for _, dst in _edges(self.db, "mentions_session")], [f"session:{A}"])
        self.assertEqual(res["unresolved_trailers"], 2)
        self.assertIsNone(self.db.get_node("session:dddddddd"))
        self.assertIsNone(self.db.get_node("session:cccccccc"))

        # The transcript arrives after the commit was already read.
        self.db.upsert_node(f"session:{C}", "Session")
        res = self.sync_git()
        self.assertEqual(res["commits"], 0)
        self.assertEqual(res["unresolved_trailers"], 1)
        self.assertEqual(
            {dst for _, dst in _edges(self.db, "mentions_session")},
            {f"session:{A}", f"session:{C}"},
        )


class ReconcileTest(_Case):
    def _stub(self, short: str) -> str:
        node = f"session:{short}"
        self.db.upsert_node(node, "Session", title=short)
        return node

    def _commit_node(self, n: int) -> str:
        node = f"commit:local/r@{n:040d}"
        self.db.upsert_node(node, "Commit")
        return node

    def test_merges_unique_stubs_only(self):
        full = f"session:{A}"
        self.db.upsert_node(full, "Session", title="full")
        for node in (f"session:{D1}", f"session:{D2}"):
            self.db.upsert_node(node, "Session")
        stub = self._stub("aaaaaaaa")
        ambiguous = self._stub("dddddddd")
        unmatched = self._stub("eeeeeeee")
        self.db.upsert_alias("my-alias", stub)
        c1, c2 = self._commit_node(1), self._commit_node(2)
        self.db.upsert_edge(c1, stub, "mentions_session", "git_adapter",
                            valid_from="2026-01-01T00:00:00Z", source_ref="r1", confidence=0.5)
        # Already present on the full node: dropped, not overwritten.
        self.db.upsert_edge(c2, full, "mentions_session", "git_adapter", source_ref="keep")
        self.db.upsert_edge(c2, stub, "mentions_session", "git_adapter", source_ref="dup")
        self.db.upsert_edge(stub, full, "continued_in", "claude_jsonl")  # would self-loop

        res = reconcile_sessions(self.db)
        self.assertEqual(
            (res["stubs"], res["merged"], res["ambiguous"], res["unmatched"]), (3, 1, 1, 1))
        self.assertEqual((res["moved_edges"], res["dropped_edges"]), (1, 2))
        self.assertEqual(_edges(self.db, "mentions_session"), {(c1, full), (c2, full)})
        self.assertEqual(_edges(self.db, "continued_in"), set())
        moved = self.db.conn.execute(
            "SELECT * FROM edges WHERE src_id = ? AND expired_at IS NULL", (c1,)).fetchone()
        self.assertEqual((moved["source_ref"], moved["confidence"]), ("r1", 0.5))
        kept = self.db.conn.execute(
            "SELECT source_ref FROM edges WHERE src_id = ? AND expired_at IS NULL",
            (c2,)).fetchone()
        self.assertEqual(kept[0], "keep")
        self.assertIsNotNone(self.db.get_node(stub)["expired_at"])
        self.assertIsNone(self.db.get_node(ambiguous)["expired_at"])
        self.assertIsNone(self.db.get_node(unmatched)["expired_at"])
        self.assertEqual(self.db.resolve_alias("my-alias"), full)
        self.assertEqual(self.db.resolve_alias("aaaaaaaa"), full)
        self.assertEqual(reconcile_sessions(self.db)["merged"], 0)

    def test_sync_and_standalone_commands_reconcile(self):
        _commit(self.vault, "a.txt", "a")
        self._stub("aaaaaaaa")
        _jsonl(self.transcript(A), [self.user(A)])
        db_path = str(self.root / "store.db")
        for argv, pick in (
            (["sync", "--db", db_path, "--claude-root", str(self.claude)],
             lambda out: out["reconcile"]),
            (["reconcile-sessions", "--db", db_path], lambda out: out),
        ):
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                self.assertEqual(cli.main(argv), 0)
            expected = 1 if argv[0] == "sync" else 0
            self.assertEqual(pick(json.loads(out.getvalue()))["merged"], expected)

    def test_vault_resync_stays_on_the_full_node(self):
        (self.vault / "recap.md").write_text("---\nsession_id: aaaaaaaa\n---\n", encoding="utf-8")
        sync_vault(self.db, "brain", self.vault, policy=self.policy)
        _jsonl(self.transcript(A), [self.user(A)])
        self.sync()
        reconcile_sessions(self.db)
        sync_vault(self.db, "brain", self.vault, policy=self.policy)
        self.assertEqual(
            _edges(self.db, "documented_in"), {(f"session:{A}", "note:brain/recap.md")})
        self.assertIsNotNone(self.db.get_node("session:aaaaaaaa")["expired_at"])


class VaultSessionFrontmatterTest(_Case):
    def test_session_frontmatter_anywhere_emits_documented_in(self):
        for rel, key, uuid in (
            (f"traces/2026-05-01_claude_{A}/verbatim.md", "session_id", A),
            ("anywhere/recap.md", "recap_session", B),
        ):
            note = self.vault / rel
            note.parent.mkdir(parents=True)
            note.write_text(f"---\n{key}: {uuid}\n---\nbody\n", encoding="utf-8")
        sync_vault(self.db, "traces", self.vault)
        self.assertEqual(
            _edges(self.db, "documented_in"),
            {(f"session:{A}", f"note:traces/traces/2026-05-01_claude_{A}/verbatim.md"),
             (f"session:{B}", "note:traces/anywhere/recap.md")},
        )


if __name__ == "__main__":
    unittest.main()
