import contextlib
import io
import json
import os
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from link_store.adapters import BoundaryPolicy, derive_handovers, sync_vault  # noqa: E402
from link_store.cli import main  # noqa: E402
from link_store.db import LinkStoreDB  # noqa: E402
from link_store.schema_compiler import compile_schema  # noqa: E402

REPO_FILE = "file:github.com/org/demo@"


def _write(root: Path, rel: str, text: str) -> Path:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def _active_edges(db: LinkStoreDB, rel: str) -> set[tuple[str, str]]:
    return {
        (r["src_id"], r["dst_id"])
        for r in db.conn.execute(
            "SELECT src_id, dst_id FROM edges WHERE rel = ? AND expired_at IS NULL", (rel,)
        )
    }


def _make_vault(root: Path) -> None:
    _write(
        root,
        "alpha.md",
        "---\naliases:\n  - First Note\n  - Shared Name\n---\n"
        "See [[beta|the beta]] and [[tool.py]] and [data](assets/data.csv).\n"
        "Missing [[nowhere]]. Hidden [[secret]] and [[hidden.py]].\n"
        "[https://docs.python.org/3/](https://docs.python.org/3/) "
        "https://sqlite.org/wal.html?token=abc123&x=1 http://bad.test:port/\n",
    )
    _write(root, "beta.md", "---\naliases: [Shared Name, Second Note]\n---\nBack to [[alpha#top]].\n")
    _write(root, "assets/data.csv", "a,b\n")
    _write(root, "scripts/tool.py", "print('synthetic')\n")
    _write(root, "restricted/secret.md", "---\naliases: [Secret Alias]\n---\nhttps://sqlite.org/secret\n")
    _write(root, "restricted/hidden.py", "pass\n")
    _write(root, "nested/.git", "gitdir: elsewhere\n")
    _write(root, "nested/inner.md", "# Inner\n")
    _write(
        root,
        "sessions/2026-01-01_demo.md",
        "---\nsession_id: sess-aaa\nrecap_session: sess-recap\n---\n# Demo\n",
    )
    _write(root, "sessions/2026-01-02_no_id.md", "---\ntitle: no id\n---\n# None\n")


def _make_index(root: Path) -> Path:
    path = root / ".obsidian" / "pkm_index.db"
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    with conn:
        conn.executescript(
            """
            CREATE TABLE notes (path TEXT PRIMARY KEY, aliases TEXT NOT NULL DEFAULT '[]');
            CREATE TABLE edges (source_path TEXT, raw_target TEXT,
                                resolved_target_path TEXT, start_line INTEGER);
            CREATE TABLE sessions_idx (session_id TEXT PRIMARY KEY, note_path TEXT NOT NULL);
            """
        )
        conn.executemany(
            "INSERT INTO notes VALUES (?, ?)",
            [
                ("alpha.md", json.dumps(["Index Alias"])),
                ("beta.md", "[]"),
                ("restricted/secret.md", json.dumps(["Secret Alias"])),
                ("deleted.md", "[]"),
                ("../outside.md", "[]"),
                ("sessions/2026-01-01_demo.md", "[]"),
                ("sessions/2026-01-02_no_id.md", "[]"),
            ],
        )
        conn.executemany(
            "INSERT INTO edges VALUES (?, ?, ?, ?)",
            [
                # only the index knows this link, which proves the index is used
                ("beta.md", "demo", "sessions/2026-01-01_demo.md", 1),
                ("alpha.md", "secret", "restricted/secret.md", 6),
                ("alpha.md", "deleted", "deleted.md", 6),
                ("alpha.md", "nowhere", None, 6),
            ],
        )
        conn.executemany(
            "INSERT INTO sessions_idx VALUES (?, ?)",
            [
                ("sess-indexed", "sessions/2026-01-01_demo.md"),
                ("2026-01-02_no_id", "sessions/2026-01-02_no_id.md"),
                ("sess-denied", "restricted/secret.md"),
            ],
        )
    conn.close()
    return path


class SchemaPhase2Test(unittest.TestCase):
    def test_new_edge_rules(self):
        rules = compile_schema().edge_rules
        for rule in (
            ("wikilinks_to", "Note", "Note"),
            ("documented_in", "Session", "Note"),
            ("handed_over_to", "Session", "Session"),
            ("backed_by", "Note", "File"),
            ("cited_url", "Session", "Url"),
            ("cited_url", "Note", "Url"),
            ("made_commit", "Session", "Commit"),
        ):
            self.assertIn(rule, rules)


class VaultAdapterTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.tmp = Path(tmp.name).resolve()
        self.vault = self.tmp / "vault"
        _make_vault(self.vault)
        self.policy = BoundaryPolicy.from_args(deny_roots=[self.vault / "restricted"])
        self.db = LinkStoreDB(self.tmp / "store" / "store.db")
        self.addCleanup(self.db.close)

    def _sync(self, policy=None):
        return sync_vault(self.db, "demo", self.vault, policy=policy or self.policy)

    def _assert_denied_absent(self):
        rows = self.db.conn.execute("SELECT id FROM nodes").fetchall()
        for row in rows:
            self.assertNotIn("restricted", row["id"])
            self.assertNotIn("sqlite.org/secret", row["id"])
        self.assertIsNone(self.db.resolve_alias("Secret Alias"))
        self.assertIsNone(self.db.get_node("session:sess-denied"))

    def test_markdown_fallback(self):
        res = self._sync()
        self.assertEqual(res["source"], "markdown")
        self.assertEqual(
            _active_edges(self.db, "wikilinks_to"),
            {
                ("note:demo/alpha.md", "note:demo/beta.md"),
                ("note:demo/beta.md", "note:demo/alpha.md"),
            },
        )
        self.assertEqual(
            _active_edges(self.db, "backed_by"),
            {
                ("note:demo/alpha.md", "file:local/demo@scripts/tool.py"),
                ("note:demo/alpha.md", "file:local/demo@assets/data.csv"),
            },
        )
        self.assertEqual(
            _active_edges(self.db, "cited_url"),
            {
                ("note:demo/alpha.md", "url:https://docs.python.org/3"),
                ("note:demo/alpha.md", "url:https://sqlite.org/wal.html?x=1"),
            },
        )
        self.assertEqual(
            _active_edges(self.db, "documented_in"),
            {
                ("session:sess-aaa", "note:demo/sessions/2026-01-01_demo.md"),
                ("session:sess-recap", "note:demo/sessions/2026-01-01_demo.md"),
            },
        )
        self.assertEqual(self.db.resolve_alias("First Note"), "note:demo/alpha.md")
        self.assertEqual(self.db.resolve_alias("Second Note"), "note:demo/beta.md")
        self.assertIsNone(self.db.resolve_alias("Shared Name"))  # ambiguous
        self.assertIsNone(self.db.get_node("note:demo/nested/inner.md"))
        self._assert_denied_absent()

    def test_index_mode_is_read_only_and_filtered(self):
        index = _make_index(self.vault)
        before = index.read_bytes()
        res = self._sync()
        self.assertEqual(res["source"], "pkm_index")
        self.assertEqual(index.read_bytes(), before)
        self.assertEqual(
            _active_edges(self.db, "wikilinks_to"),
            {("note:demo/beta.md", "note:demo/sessions/2026-01-01_demo.md")},
        )
        sessions = {src for src, _ in _active_edges(self.db, "documented_in")}
        self.assertEqual(
            sessions, {"session:sess-indexed", "session:sess-aaa", "session:sess-recap"}
        )
        self.assertEqual(self.db.resolve_alias("Index Alias"), "note:demo/alpha.md")
        self.assertIsNone(self.db.get_node("note:demo/deleted.md"))
        self.assertIsNone(self.db.get_node("note:demo/../outside.md"))
        self.assertEqual(len(_active_edges(self.db, "backed_by")), 2)
        self._assert_denied_absent()

    def test_corrupt_index_falls_back_to_markdown(self):
        _write(self.vault, ".obsidian/pkm_index.db", "not a database")
        self.assertEqual(self._sync()["source"], "markdown")

    def test_denied_index_is_not_read(self):
        _make_index(self.vault)
        policy = BoundaryPolicy.from_args(
            deny_roots=[self.vault / "restricted", self.vault / ".obsidian"]
        )
        self.assertEqual(self._sync(policy)["source"], "markdown")

    def test_allow_root_limits_notes_but_keeps_index(self):
        _make_index(self.vault)
        policy = BoundaryPolicy.from_args(allow_roots=[self.vault / "sessions"])
        res = self._sync(policy)
        self.assertEqual(res["source"], "pkm_index")
        self.assertEqual(res["notes"], 2)
        self.assertIsNone(self.db.get_node("note:demo/alpha.md"))

    def test_symlink_into_denied_root_is_skipped(self):
        try:
            os.symlink(self.vault / "restricted" / "secret.md", self.vault / "shortcut.md")
        except (OSError, NotImplementedError):
            self.skipTest("symlinks unavailable")
        self._sync()
        self.assertIsNone(self.db.get_node("note:demo/shortcut.md"))
        self._assert_denied_absent()

    def test_nested_vault_owns_its_notes(self):
        policy = BoundaryPolicy.from_args(vault_roots={"inner": self.vault / "assets"})
        _write(self.vault, "assets/owned.md", "# Owned\n")
        self._sync(policy)
        self.assertIsNone(self.db.get_node("note:demo/assets/owned.md"))
        self.assertIsNone(self.db.get_node("note:inner/owned.md"))

    def test_backed_by_uses_git_remote_file_ids(self):
        for args in (["init", "-q"], ["remote", "add", "origin", "https://github.com/org/demo.git"]):
            subprocess.run(["git", "-C", str(self.vault), *args], check=True)
        self._sync()
        self.assertIn(
            ("note:demo/alpha.md", REPO_FILE + "scripts/tool.py"),
            _active_edges(self.db, "backed_by"),
        )

    def test_alias_does_not_take_over_existing_alias(self):
        self.db.upsert_node("session:other", "Session")
        self.db.upsert_alias("First Note", "session:other")
        self._sync()
        self.assertEqual(self.db.resolve_alias("First Note"), "session:other")

    def test_resync_is_idempotent_and_expires_removed_data(self):
        self._sync()
        count = "SELECT COUNT(*) FROM edges"
        first = self.db.conn.execute(count).fetchone()[0]
        again = self._sync()
        self.assertEqual(self.db.conn.execute(count).fetchone()[0], first)
        self.assertEqual((again["expired_edges"], again["expired_nodes"]), (0, 0))

        (self.vault / "beta.md").unlink()
        _write(self.vault, "alpha.md", "Nothing left.\n")
        res = self._sync()
        self.assertEqual(res["expired_nodes"], 1)
        self.assertEqual(_active_edges(self.db, "wikilinks_to"), set())
        self.assertEqual(_active_edges(self.db, "backed_by"), set())
        self.assertIsNotNone(self.db.get_node("note:demo/beta.md")["expired_at"])
        self.assertIsNone(self.db.resolve_alias("First Note"))
        self.assertIsNone(self.db.resolve_alias("Second Note"))

    def test_syncing_one_vault_keeps_another_vaults_edges(self):
        other = self.tmp / "other"
        _write(other, "a.md", "[[b]]\n")
        _write(other, "b.md", "# B\n")
        sync_vault(self.db, "other", other)
        self._sync()
        self.assertIn(("note:other/a.md", "note:other/b.md"), _active_edges(self.db, "wikilinks_to"))

    def test_missing_root_expires_nothing(self):
        self._sync()
        res = sync_vault(self.db, "demo", self.tmp / "unmounted")
        self.assertEqual((res["expired_edges"], res["expired_nodes"]), (0, 0))
        self.assertTrue(_active_edges(self.db, "wikilinks_to"))


class HandoverTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.path = Path(tmp.name) / "store.db"
        self.db = LinkStoreDB(self.path)
        self.addCleanup(self.db.close)

    def _touch(self, sess: str, rel: str, target: str, ts: str) -> None:
        kinds = {"file": "File", "note": "Note", "commit": "Commit", "branch": "Branch"}
        self.db.upsert_node(f"session:{sess}", "Session")
        self.db.upsert_node(target, kinds[target.split(":", 1)[0]])
        self.db.upsert_edge(f"session:{sess}", target, rel, "test", valid_from=ts)

    def _handovers(self) -> dict[tuple[str, str], dict]:
        return {
            (r["src_id"][8:], r["dst_id"][8:]): dict(r)
            for r in self.db.conn.execute(
                "SELECT * FROM edges WHERE rel = 'handed_over_to' AND expired_at IS NULL"
            )
        }

    def _read_pair(self, b_start="2026-01-01T12:00:00Z"):
        self._touch("a", "modified_file", REPO_FILE + "x.py", "2026-01-01T10:00:00Z")
        self._touch("b", "read_file", REPO_FILE + "x.py", b_start)
        self._touch("b", "worked_in_branch", "branch:github.com/org/demo@feat/x", b_start)

    def test_read_after_modify(self):
        self._read_pair()
        derive_handovers(self.db)
        edges = self._handovers()
        self.assertEqual(set(edges), {("a", "b")})
        edge = edges[("a", "b")]
        self.assertEqual(edge["confidence"], 0.80)
        self.assertEqual(edge["source_adapter"], "handover_heuristic")
        self.assertEqual(edge["source_ref"], f"shared:{REPO_FILE}x.py")
        self.assertEqual(
            json.loads(edge["metadata_json"])["evidence"], f"shared:{REPO_FILE}x.py"
        )

    def test_gap_boundaries(self):
        for b_start, expected in (
            ("2026-01-01T10:00:00Z", True),
            ("2026-01-03T10:00:00Z", True),
            ("2026-01-03T10:00:01Z", False),
            ("2026-01-01T09:59:59Z", False),
            ("2026-01-01T12:00:00+01:00", True),
        ):
            with self.subTest(b_start=b_start):
                self.db.conn.execute("DELETE FROM edges")
                self.db.conn.commit()
                self._read_pair(b_start)
                derive_handovers(self.db)
                self.assertEqual(("a", "b") in self._handovers(), expected)

    def test_overlapping_sessions_do_not_hand_over(self):
        self._read_pair()
        self._touch("a", "read_file", REPO_FILE + "late.py", "2026-01-01T13:00:00Z")
        derive_handovers(self.db)
        self.assertEqual(self._handovers(), {})

    def test_requires_shared_repo(self):
        self._touch("a", "modified_file", "note:demo/n.md", "2026-01-01T10:00:00Z")
        self._touch("a", "worked_in_branch", "branch:github.com/org/one@main", "2026-01-01T10:00:00Z")
        self._touch("b", "read_file", "note:demo/n.md", "2026-01-01T11:00:00Z")
        self._touch("b", "worked_in_branch", "branch:github.com/org/two@main", "2026-01-01T11:00:00Z")
        derive_handovers(self.db)
        self.assertEqual(self._handovers(), {})
        self._touch("b", "worked_in_branch", "branch:github.com/org/one@feat/y", "2026-01-01T11:00:00Z")
        derive_handovers(self.db)
        self.assertEqual(set(self._handovers()), {("a", "b")})

    def test_explicit_lineage_suppresses_and_expires(self):
        for rel, src, dst in (
            ("continued_in", "a", "b"),
            ("derived_from", "b", "a"),
        ):
            with self.subTest(rel=rel):
                self._read_pair()
                derive_handovers(self.db)
                self.assertIn(("a", "b"), self._handovers())
                self.db.upsert_edge(f"session:{src}", f"session:{dst}", rel, "test")
                res = derive_handovers(self.db)
                self.assertEqual(res["expired_edges"], 1)
                self.assertEqual(self._handovers(), {})
                self.db.expire_edge(f"session:{src}", f"session:{dst}", rel)

    def test_subagents_of_one_session_are_not_handovers(self):
        self._touch("p:agent-1", "modified_file", REPO_FILE + "x.py", "2026-01-01T10:00:00Z")
        self._touch("p:agent-2", "read_file", REPO_FILE + "x.py", "2026-01-01T11:00:00Z")
        self._touch(
            "p:agent-2", "worked_in_branch", "branch:github.com/org/demo@main", "2026-01-01T11:00:00Z"
        )
        derive_handovers(self.db)
        self.assertEqual(self._handovers(), {})

    def _shared_pair(self, targets: list[str]):
        for target in targets:
            rel = "made_commit" if target.startswith("commit:") else "modified_file"
            self._touch("a", rel, target, "2026-01-01T10:00:00Z")
            self._touch("b", rel, target, "2026-01-01T11:00:00Z")

    def test_shared_targets_confidence_scales_and_caps(self):
        for count, expected in ((1, None), (2, 0.65), (3, 0.70), (6, 0.85), (9, 0.85)):
            with self.subTest(count=count):
                self.db.conn.execute("DELETE FROM edges")
                self.db.conn.commit()
                self._shared_pair([f"{REPO_FILE}f{i}.py" for i in range(count)])
                derive_handovers(self.db)
                edge = self._handovers().get(("a", "b"))
                self.assertEqual(edge and edge["confidence"], expected)

    def test_commits_count_as_shared_targets(self):
        self._shared_pair([REPO_FILE + "f.py", "commit:github.com/org/demo@" + "a" * 40])
        derive_handovers(self.db)
        self.assertEqual(self._handovers()[("a", "b")]["confidence"], 0.65)

    def test_commit_session_trailers_count_as_commits(self):
        for sess, ts in (("a", "2026-01-01T10:00:00Z"), ("b", "2026-01-01T11:00:00Z")):
            self._touch(sess, "modified_file", REPO_FILE + "f.py", ts)
        commit = "commit:github.com/org/demo@" + "b" * 40
        self.db.upsert_node(commit, "Commit")
        for sess in ("a", "b"):
            self.db.upsert_edge(commit, f"session:{sess}", "mentions_session", "test")
        derive_handovers(self.db)
        self.assertIn(("a", "b"), self._handovers())

    def test_hub_targets_are_not_shared_evidence(self):
        targets = [REPO_FILE + "hub.md", REPO_FILE + "other.py"]
        self._shared_pair(targets)
        self._touch("c", "modified_file", targets[0], "2025-01-01T00:00:00Z")
        res = derive_handovers(self.db, hub_max_sessions=2)
        self.assertEqual(res["hubs"], 1)
        self.assertEqual(self._handovers(), {})
        derive_handovers(self.db, hub_max_sessions=3)
        self.assertIn(("a", "b"), self._handovers())

    def test_rerun_is_idempotent(self):
        self._read_pair()
        derive_handovers(self.db)
        first = self._handovers()
        res = derive_handovers(self.db)
        self.assertEqual(res["expired_edges"], 0)
        self.assertEqual(self._handovers(), first)


class CliPhase2Test(unittest.TestCase):
    def test_sync_vault_and_derive_handovers_commands(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            vault = root / "vault"
            _make_vault(vault)
            db = str(root / "store.db")

            def run(*argv):
                out = io.StringIO()
                with contextlib.redirect_stdout(out):
                    self.assertEqual(main(list(argv)), 0)
                return json.loads(out.getvalue())

            synced = run(
                "sync-vault",
                "--db", db,
                "--vault", f"demo={vault}",
                "--deny-root", str(vault / "restricted"),
            )
            self.assertEqual(synced["vaults"][0]["wikilinks_to"], 2)
            derived = run("derive-handovers", "--db", db)
            self.assertEqual(derived["handovers"], 0)
            queried = run("query", "--db", db, "--node", "First Note")
            self.assertEqual(queried["node"]["id"], "note:demo/alpha.md")


if __name__ == "__main__":
    unittest.main()
