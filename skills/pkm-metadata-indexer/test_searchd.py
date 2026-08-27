import importlib.util
import json
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path


def load(name: str):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).with_name(f"{name}.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


SEARCHD = load("searchd")


def fetch(port: int, path: str, headers: dict | None = None, method: str = "GET"):
    request = urllib.request.Request(
        f"http://127.0.0.1:{port}{path}", headers=headers or {}, method=method
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return response.status, json.loads(response.read())
    except urllib.error.HTTPError as error:
        return error.code, json.loads(error.read())


def build_vault(root: Path, name: str, notes: dict[str, str]):
    (root / ".obsidian").mkdir(parents=True)
    for filename, text in notes.items():
        (root / filename).write_text(text, encoding="utf-8")
    db = root / ".obsidian" / "pkm_index.db"
    SEARCHD.pkm.build_index(vault_path=str(root), db_path=str(db), skip_embeddings=True)
    return SEARCHD.Vault(name, root, db)


class SearchDaemonTest(unittest.TestCase):
    """Runs against a real index built without embeddings, so no model is loaded."""

    @classmethod
    def build_vault(cls, name: str, notes: dict[str, str]):
        return build_vault(Path(cls.temp_dir.name) / name, name, notes)

    @classmethod
    def setUpClass(cls):
        cls.temp_dir = tempfile.TemporaryDirectory()
        first = cls.build_vault("first", {
            "alpha.md": "## Planned\nA distinctivephrase appears here. [[beta]]\n",
            "beta.md": "## Result\nA linked destination.\n",
        })
        second = cls.build_vault("second", {"gamma.md": "## Other\nA separatephrase lives here.\n"})

        SEARCHD.STATE = SEARCHD.State([first, second])
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), SEARCHD.Handler)
        cls.port = cls.server.server_address[1]
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.temp_dir.cleanup()

    def get(self, path: str, headers: dict | None = None, method: str = "GET"):
        return fetch(self.port, path, headers, method)

    def test_health_reports_every_vault(self):
        status, body = self.get("/health")
        self.assertEqual(status, 200)
        self.assertEqual(body["default_vault"], "first")
        self.assertEqual([v["name"] for v in body["vaults"]], ["first", "second"])
        self.assertEqual(body["vaults"][0]["notes"], 2)
        self.assertEqual(body["vaults"][0]["vectors"], 0)

    def test_search_finds_a_lexical_hit(self):
        status, body = self.get("/search?q=distinctivephrase")
        self.assertEqual(status, 200)
        self.assertEqual(body["vault"], "first")
        self.assertEqual([row["path"] for row in body["results"]], ["alpha.md"])
        self.assertIn("distinctivephrase", body["results"][0]["snippet"])

    def test_a_query_is_logged_with_its_results(self):
        log = Path(self.temp_dir.name) / "queries.jsonl"
        SEARCHD.LOG_PATH = log
        try:
            self.get("/search?q=distinctivephrase&origin=beta.md")
        finally:
            SEARCHD.LOG_PATH = None
        rows = [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines()]
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["q"], "distinctivephrase")
        self.assertEqual(rows[0]["vault"], "first")
        self.assertEqual(rows[0]["results"], ["alpha.md"])
        self.assertEqual(rows[0]["origin"], "beta.md")
        self.get("/search?q=distinctivephrase")  # log off again
        self.assertEqual(len(log.read_text(encoding="utf-8").splitlines()), 1)

    def test_each_vault_only_sees_its_own_notes(self):
        _, wrong = self.get("/search?q=separatephrase")
        self.assertEqual(wrong["results"], [])
        _, right = self.get("/search?q=separatephrase&vault=second")
        self.assertEqual([row["path"] for row in right["results"]], ["gamma.md"])
        status, missing = self.get("/search?q=a&vault=nope")
        self.assertEqual(status, 404)
        self.assertIn("unknown vault", missing["error"])

    def test_limit_is_clamped_and_validated(self):
        _, body = self.get("/search?q=a&limit=9999")
        self.assertLessEqual(len(body["results"]), SEARCHD.MAX_LIMIT)
        self.assertEqual(self.get("/search?q=a&limit=abc")[0], 400)
        self.assertEqual(self.get("/search?q=")[0], 400)

    def test_links_resolve_both_directions(self):
        status, body = self.get("/links?note=alpha")
        self.assertEqual(status, 200)
        self.assertEqual([edge["target"] for edge in body["outbound"]], ["beta.md"])
        _, inbound = self.get("/links?note=beta")
        self.assertEqual([edge["source"] for edge in inbound["inbound"]], ["alpha.md"])

    def test_similar_needs_a_note_that_resolves(self):
        # this fixture is indexed without embeddings, so the route is checked
        # here and the ranking itself in test_index_pkm_meta
        self.assertEqual(self.get("/similar")[0], 400)
        self.assertIn("no single indexed note", self.get("/similar?note=nosuchnote")[1]["error"])
        status, body = self.get("/similar?note=alpha")
        self.assertEqual(status, 200)
        self.assertEqual(body["results"], [])

    def test_a_browser_page_cannot_reach_it(self):
        # a cross-site fetch always carries Origin, a real client never does
        self.assertEqual(self.get("/search?q=a", {"Origin": "https://evil.example"})[0], 403)
        # and a rebound hostname shows up in Host
        self.assertEqual(self.get("/health", {"Host": "evil.example"})[0], 403)

    def test_a_token_replaces_the_host_check_when_set(self):
        SEARCHD.STATE.token = "s3cret"
        try:
            self.assertEqual(self.get("/health")[0], 403)
            self.assertEqual(self.get("/health", {"X-PKM-Token": "wrong"})[0], 403)
            self.assertEqual(self.get("/health", {"X-PKM-Token": "s3cret"})[0], 200)
        finally:
            SEARCHD.STATE.token = None

    def test_unknown_routes_and_methods(self):
        self.assertEqual(self.get("/nope")[0], 404)
        self.assertEqual(self.get("/search?q=a", method="POST")[0], 404)


class UnlinkedMentionsTest(unittest.TestCase):
    """The four exclusions the built-in pane gets wrong or does not offer."""

    NOTES = {
        "covariance.md": (
            "---\naliases:\n  - covar shorthand\ntags:\n  - stats\n---\n\n"
            "## Definition\nCovariance measures joint variability.\n"
        ),
        "aliased.md": "## Notes\nThe covar shorthand turns up in this sentence.\n",
        "linked.md": "## Notes\nSee [[covariance]], and covariance again in the same section.\n",
        "fenced.md": "## Code\nNothing plain in this prose.\n\n```python\ncovariance = 1\n```\n",
        "plural.md": "## Stats\nWe computed covariances for the sample.\n",
        "inline.md": "## Notes\nThe `covariance` field of the struct, in prose about nothing else.\n",
        "other link.md": "## Notes\nSee [[covariance matrix]], which is a different note entirely.\n",
        "plain.md": "## Prose\nThe covariance term shows up here with no link.\n",
    }

    @classmethod
    def setUpClass(cls):
        cls.temp_dir = tempfile.TemporaryDirectory()
        vault = build_vault(Path(cls.temp_dir.name) / "stats", "stats", cls.NOTES)
        cls.previous_state = SEARCHD.STATE
        SEARCHD.STATE = SEARCHD.State([vault])
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), SEARCHD.Handler)
        cls.port = cls.server.server_address[1]
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        SEARCHD.STATE = cls.previous_state
        cls.temp_dir.cleanup()

    def mentions(self, note: str = "covariance"):
        status, body = fetch(self.port, f"/unlinked?note={note}")
        self.assertEqual(status, 200)
        return body

    def test_an_alias_counts_as_a_mention(self):
        body = self.mentions()
        rows = {row["path"]: row for row in body["results"]}
        self.assertIn("aliased.md", rows)
        self.assertEqual(rows["aliased.md"]["term"], "covar shorthand")
        self.assertIn("[covar shorthand]", rows["aliased.md"]["snippet"])
        self.assertEqual(rows["aliased.md"]["heading"], "Notes")
        self.assertEqual(rows["aliased.md"]["line"], 2)

    def test_a_linked_mention_is_not_unlinked(self):
        paths = [row["path"] for row in self.mentions()["results"]]
        self.assertIn("plain.md", paths)
        self.assertNotIn("linked.md", paths)

    def test_a_mention_inside_a_fence_is_skipped(self):
        paths = [row["path"] for row in self.mentions()["results"]]
        self.assertNotIn("fenced.md", paths)

    def test_a_mention_nobody_could_link_is_skipped(self):
        # a code span, and a mention sitting inside a link to another note
        paths = [row["path"] for row in self.mentions()["results"]]
        self.assertNotIn("inline.md", paths)
        self.assertNotIn("other link.md", paths)

    def test_the_target_note_is_not_its_own_mention(self):
        paths = [row["path"] for row in self.mentions()["results"]]
        self.assertNotIn("covariance.md", paths)

    def test_a_phrase_match_is_token_based(self):
        # "covariance" must not match "covariances"
        paths = [row["path"] for row in self.mentions()["results"]]
        self.assertNotIn("plural.md", paths)

    def test_a_missing_or_unknown_note(self):
        self.assertEqual(fetch(self.port, "/unlinked")[0], 400)
        self.assertIn("no single indexed note", self.mentions("nosuchnote")["error"])

    def test_the_cli_path_returns_the_same_rows(self):
        client = load("search_vault")
        vault = SEARCHD.STATE.vaults["stats"]
        direct = client.direct_unlinked("covariance", 20, str(vault.db))
        self.assertEqual(
            sorted(row["path"] for row in direct),
            sorted(row["path"] for row in self.mentions()["results"]),
        )


class WatcherTest(unittest.TestCase):
    """The watcher itself is `watchfiles`; what is ours is the filter and the loop."""

    def test_the_indexers_own_writes_are_ignored(self):
        # a reindex writes these inside the watched root, so seeing them would
        # start a loop that never ends
        for path in ("vault/.obsidian/pkm_index.db", "root/.pkm_scan_state.json",
                     "vault/.obsidian/pkm_index.db-wal"):
            self.assertTrue(SEARCHD.index_writes(path), path)
        for path in ("vault/note.md", "root/2026-08-27 a note.md"):
            self.assertFalse(SEARCHD.index_writes(path), path)

    def test_each_batch_of_changes_reindexes_once(self):
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        vault = build_vault(Path(temp_dir.name) / "watched", "watched",
                            {"alpha.md": "## One\nText.\n"})
        (vault.root / "beta.md").write_text("## Two\nMore text.\n", encoding="utf-8")
        SEARCHD.watch_vault(vault, stream=[{("added", "beta.md")}])
        self.assertEqual(vault.counts()["notes"], 2)

    def test_a_failing_reindex_leaves_the_watcher_running(self):
        vault = SEARCHD.Vault("gone", Path("no such root"), Path("no such root/x.db"))
        SEARCHD.watch_vault(vault, stream=[{("added", "a.md")}, {("added", "b.md")}])


if __name__ == "__main__":
    unittest.main()
