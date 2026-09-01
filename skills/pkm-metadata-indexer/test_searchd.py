import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import threading
import time
import unittest
import urllib.error
import urllib.request
import uuid
from http.server import ThreadingHTTPServer
from pathlib import Path


def load(name: str):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).with_name(f"{name}.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


SEARCHD = load("searchd")

# closed before a temp dir is removed, Windows will not delete an open database
VAULTS: list = []


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
    vault = SEARCHD.Vault(name, root, db)
    VAULTS.append(vault)
    return vault


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
        for vault in VAULTS:
            vault.close()
        # co_commit's WAL mode leaves a -wal/-shm sidecar per database this class
        # created; Windows can hold its memory-mapping open a moment past the
        # owning connection's close(), long enough to fail an immediate rmtree.
        # One retry after a short wait is the same tolerance Vault.close() above
        # exists for, for the same reason.
        for attempt in range(3):
            try:
                cls.temp_dir.cleanup()
                return
            except PermissionError:
                if attempt == 2:
                    raise
                time.sleep(0.2)

    def get(self, path: str, headers: dict | None = None, method: str = "GET"):
        return fetch(self.port, path, headers, method)

    def test_health_reports_every_vault(self):
        status, body = self.get("/health")
        self.assertEqual(status, 200)
        self.assertEqual(body["default_vault"], "first")
        self.assertEqual([v["name"] for v in body["vaults"]], ["first", "second"])
        self.assertEqual(body["vaults"][0]["notes"], 2)
        self.assertEqual(body["vaults"][0]["vectors"], 0)
        self.assertEqual(body["vaults"][0]["co_commit_edges"], 0)

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

    def test_a_search_over_several_corpora_logs_one_line_each(self):
        log = Path(self.temp_dir.name) / "many.jsonl"
        SEARCHD.LOG_PATH = log
        try:
            self.get("/search?q=distinctivephrase+OR+separatephrase&vault=all")
        finally:
            SEARCHD.LOG_PATH = None
        rows = [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines()]
        # one line per corpus, each holding only its own paths, or a reader of one
        # corpus sees a vault called "first,second" and pairs across the two
        self.assertEqual([row["vault"] for row in rows], ["first", "second"])
        self.assertEqual(rows[0]["results"], ["alpha.md"])
        self.assertEqual(rows[1]["results"], ["gamma.md"])

    def test_each_vault_only_sees_its_own_notes(self):
        _, wrong = self.get("/search?q=separatephrase")
        self.assertEqual(wrong["results"], [])
        _, right = self.get("/search?q=separatephrase&vault=second")
        self.assertEqual([row["path"] for row in right["results"]], ["gamma.md"])
        status, missing = self.get("/search?q=a&vault=nope")
        self.assertEqual(status, 404)
        self.assertIn("unknown vault", missing["error"])

    def test_one_search_can_span_every_corpus(self):
        # the vault is two repositories on this machine and an agent looking for
        # a note does not know which half holds it
        _, both = self.get("/search?q=separatephrase&vault=all")
        self.assertEqual([row["path"] for row in both["results"]], ["gamma.md"])
        self.assertEqual(both["results"][0]["vault"], "second")
        self.assertEqual(both["vault"], "first,second")
        self.assertEqual(sorted(both["indexed_at"]), ["first", "second"])
        _, listed = self.get("/search?q=distinctivephrase&vault=second,first")
        self.assertEqual([row["vault"] for row in listed["results"]], ["first"])
        self.assertEqual(self.get("/search?q=a&vault=first,nope")[0], 404)

    def test_a_multi_corpus_result_is_ordered_by_rank_not_by_corpus(self):
        # both corpora answer, and the merge must not simply concatenate them
        _, body = self.get("/search?q=phrase+here&vault=all&limit=10")
        scores = [row["score"] for row in body["results"]]
        self.assertEqual(scores, sorted(scores, reverse=True))
        self.assertEqual({row["vault"] for row in body["results"]}, {"first", "second"})

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

    def with_co_commit_db(self, *rows):
        """Point co_commit's DEFAULT_DB at a throwaway file for one test, restored after.

        A fresh file per call, not a shared one reused across tests: uuid4 rather
        than id(rows), since id() is a memory address CPython freely reuses once
        the short-lived *rows tuple is collected, which previously produced two
        tests colliding on the same filename and a UNIQUE constraint failure.
        """
        original = SEARCHD.co_commit.DEFAULT_DB
        db = Path(self.temp_dir.name) / f"co_commit_{uuid.uuid4().hex}.db"
        connection = SEARCHD.co_commit.connect(db)
        with connection:
            connection.executemany(
                "INSERT INTO co_commits VALUES (?, ?, ?, ?, ?, ?, ?)", rows
            )
        connection.execute("PRAGMA wal_checkpoint(TRUNCATE);")
        connection.close()
        SEARCHD.co_commit.DEFAULT_DB = db
        self.addCleanup(setattr, SEARCHD.co_commit, "DEFAULT_DB", original)

    def test_co_commits_route(self):
        self.with_co_commit_db(("first", "alpha.md", "beta.md", 2.5, 3, "2026-08-31", "abc1234"))
        self.assertEqual(self.get("/co-commits")[0], 400)
        # extensionless reference, resolved the same way /similar and /links do
        status, body = self.get("/co-commits?note=alpha")
        self.assertEqual(status, 200)
        self.assertEqual(body["results"][0]["path"], "beta.md")
        self.assertEqual(body["results"][0]["weight"], 2.5)
        self.assertEqual(self.get("/health")[1]["vaults"][0]["co_commit_edges"], 1)

    def test_similar_without_graph_hints_at_it_when_available(self):
        # an agent calling plain /similar has not necessarily read this skill's
        # docs, so the option to fuse in co-commit history has to surface here
        self.with_co_commit_db(("first", "alpha.md", "beta.md", 1.0, 1, "2026-08-31", "abc1234"))
        _, with_edge = self.get("/similar?note=alpha")
        self.assertIn("graph=1", with_edge["graph_hint"])
        # gamma is in a different vault with no co_commit rows at all
        _, without_edge = self.get("/similar?note=gamma&vault=second")
        self.assertNotIn("graph_hint", without_edge)

    def test_similar_graph_folds_in_co_commit_when_vectors_are_empty(self):
        # this fixture has no embeddings, so the vector side of the fusion is
        # empty and the fused result is co_commit's edge alone, taking its
        # heading/snippet from note_snippet since /similar never ranked it
        self.with_co_commit_db(("first", "alpha.md", "beta.md", 1.0, 1, "2026-08-31", "abc1234"))
        status, body = self.get("/similar?note=alpha&graph=1")
        self.assertEqual(status, 200)
        self.assertEqual([row["path"] for row in body["results"]], ["beta.md"])
        self.assertEqual(body["results"][0]["source"], "co_commit")
        self.assertEqual(body["results"][0]["heading"], "Result")
        # without &graph=1 the same query never sees the co_commit edge
        _, plain = self.get("/similar?note=alpha")
        self.assertEqual(plain["results"], [])

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

    def test_every_registered_corpus_is_newer_than_its_newest_file(self):
        # the coverage assertion. On 2026-08-28 the real brain corpus failed
        # this by three days and every search still returned plausible results
        for vault in SEARCHD.STATE.vaults.values():
            with self.subTest(vault=vault.name):
                missing = SEARCHD.pkm.stale_paths(vault.root, vault.db)
                self.assertEqual(missing["count"], 0,
                                 f"{vault.name} holds files its index has not read: {missing['paths']}")
                self.assertIsNotNone(missing["indexed_at"])

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
        self.addCleanup(lambda: [v.close() for v in VAULTS])
        vault = build_vault(Path(temp_dir.name) / "watched", "watched",
                            {"alpha.md": "## One\nText.\n"})
        (vault.root / "beta.md").write_text("## Two\nMore text.\n", encoding="utf-8")
        SEARCHD.watch_vault(vault, stream=[{("added", "beta.md")}])
        self.assertEqual(vault.counts()["notes"], 2)

    def test_startup_catches_up_on_what_changed_while_it_was_down(self):
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        self.addCleanup(lambda: [v.close() for v in VAULTS])
        vault = build_vault(Path(temp_dir.name) / "restarted", "restarted",
                            {"alpha.md": "## One\nText.\n"})
        # the edit lands with no watcher running, which is every reboot
        (vault.root / "beta.md").write_text("## Two\nMore text.\n", encoding="utf-8")
        SEARCHD.catch_up([vault])
        self.assertEqual(vault.counts()["notes"], 2)

    def test_catch_up_skips_a_corpus_with_no_index_and_survives_a_bad_one(self):
        missing = SEARCHD.Vault("gone", Path("no such root"), Path("no such root/x.db"))
        SEARCHD.catch_up([missing])  # skipped, not an error

    def test_a_watched_source_runs_its_command(self):
        # a corpus that is not searched itself but produces notes that are
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        made = Path(temp_dir.name) / "derived.md"
        command = [sys.executable, "-c", f"open({str(made)!r}, 'w').write('## Note\\n')"]
        SEARCHD.watch_command(Path(temp_dir.name), command, 10, stream=[{("added", "x")}])
        self.assertEqual(made.read_text(encoding="utf-8"), "## Note\n")

    def test_a_watched_source_runs_its_command_without_a_console_window(self):
        # the daemon runs under pythonw, so a console child with no flag pops a
        # window on every refresh, once a minute for as long as an agent is writing
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        seen = {}
        original = SEARCHD.subprocess.run
        self.addCleanup(setattr, SEARCHD.subprocess, "run", original)
        SEARCHD.subprocess.run = lambda *args, **kwargs: seen.update(kwargs) or original(*args, **kwargs)
        SEARCHD.watch_command(Path(temp_dir.name), [sys.executable, "-c", "pass"], 10,
                              stream=[{("added", "x")}])
        self.assertEqual(seen["creationflags"], SEARCHD.NO_WINDOW)
        if sys.platform == "win32":
            self.assertEqual(SEARCHD.NO_WINDOW, SEARCHD.subprocess.CREATE_NO_WINDOW)

    def test_a_failing_command_leaves_the_watcher_running(self):
        # the extractor reads someone else's transcripts, so it can fail on a
        # half-written one, and a watcher that dies on that is silent
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        command = [sys.executable, "-c", "import sys; sys.exit(3)"]
        SEARCHD.watch_command(Path(temp_dir.name), command, 10,
                              stream=[{("added", "x")}, {("added", "y")}])
        SEARCHD.watch_command(Path(temp_dir.name), ["no such executable at all"], 10,
                              stream=[{("added", "x")}])

    def test_a_failing_reindex_leaves_the_watcher_running(self):
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        self.addCleanup(lambda: [v.close() for v in VAULTS])
        root = Path(temp_dir.name) / "flaky"
        vault = build_vault(root, "flaky", {"alpha.md": "## One\nText.\n"})
        # a plain file where the database's parent directory has to be, so the
        # mkdir(parents=True) at the top of build_index raises and no index is
        # ever written. A missing root does not fail: build_index creates it.
        blocker = root / ".obsidian" / "blocker"
        blocker.write_text("", encoding="utf-8")
        healthy_db, vault.db = vault.db, blocker / "x.db"

        failed, served, release = [], threading.Event(), threading.Event()

        def stream():
            yield {("added", "beta.md")}  # this reindex cannot succeed
            failed.append(vault.db.exists())
            vault.db = healthy_db
            (root / "beta.md").write_text("## Two\nMore text.\n", encoding="utf-8")
            yield {("added", "beta.md")}  # and the watcher is still here for it
            served.set()
            release.wait(30)

        watcher = threading.Thread(target=SEARCHD.watch_vault, args=(vault,),
                                   kwargs={"stream": stream()}, daemon=True)
        watcher.start()
        self.assertTrue(served.wait(60), "the watcher died on the failing reindex")
        self.assertEqual(failed, [False], "the reindex wrote an index, it did not fail")
        self.assertTrue(watcher.is_alive())
        self.assertEqual(vault.counts()["notes"], 2)
        release.set()
        watcher.join(10)


class StaleIndexTest(unittest.TestCase):
    """A search over a stale index looks exactly like one over a fresh index.

    That cost three days on 2026-08-28: the watcher was never started, notes
    written after the last run matched nothing, and the ranking looked fine.
    """

    def setUp(self):
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        self.addCleanup(lambda: [vault.close() for vault in VAULTS])
        self.vault = build_vault(Path(temp_dir.name) / "aging", "aging",
                                 {"alpha.md": "## One\nIndexed text.\n"})
        previous, SEARCHD.STATE = SEARCHD.STATE, SEARCHD.State([self.vault])
        self.addCleanup(setattr, SEARCHD, "STATE", previous)

    def unindexed(self, name: str = "beta.md"):
        (self.vault.root / name).write_text("## Two\nUnindexed text.\n", encoding="utf-8")
        self.vault.stale_at = 0.0  # the cache is a TTL, and a test does not wait it out

    def test_a_file_written_after_the_last_run_is_named(self):
        self.assertEqual(self.vault.stale()["count"], 0)
        self.unindexed()
        missing = self.vault.stale()
        self.assertEqual(missing["paths"], ["beta.md"])
        self.assertIsNotNone(missing["indexed_at"])

    def test_a_corpus_with_no_index_says_so_rather_than_looking_fresh(self):
        missing = SEARCHD.pkm.stale_paths(self.vault.root, self.vault.root / "nothing.db")
        self.assertTrue(missing["no_index"])
        self.assertIsNone(missing["indexed_at"])

    def test_the_walk_is_cached_between_queries(self):
        self.vault.stale()
        self.unindexed("gamma.md")
        self.vault.stale_at = time.time()  # as if the walk had just run
        self.assertEqual(self.vault.stale()["count"], 0)

    def test_a_search_reports_what_it_could_not_see_and_reindexes_behind_itself(self):
        self.unindexed()
        payload = SEARCHD.do_search([self.vault], "indexed text", 5)
        self.assertEqual([row["path"] for row in payload["results"]], ["alpha.md"])
        self.assertEqual(payload["stale"]["aging"]["paths"], ["beta.md"])
        self.assertTrue(payload["stale"]["aging"]["reindexing"])
        deadline = time.time() + 180
        while self.vault.reindexing and time.time() < deadline:
            time.sleep(0.2)
        self.assertFalse(self.vault.reindexing, "the background reindex never finished")
        self.assertEqual(self.vault.counts()["notes"], 2)
        self.assertEqual(self.vault.stale()["count"], 0)
        self.assertEqual(SEARCHD.do_search([self.vault], "unindexed text", 5)["stale"], {})

    def test_a_search_answers_while_a_reindex_is_running(self):
        """The pass held the query lock, so a search that arrived during one waited it out.

        Fifteen seconds over two corpora, past the CLI's timeout, and the CLI
        reads a timeout as no daemon: it fell back to a direct search of one
        corpus and printed that as the answer.
        """
        answered = []
        with SEARCHD.INDEX_LOCK:  # as if a pass were halfway through
            worker = threading.Thread(target=lambda: answered.append(
                SEARCHD.do_search([self.vault], "indexed text", 5, reindex=False)), daemon=True)
            worker.start()
            worker.join(30)
        self.assertTrue(answered, "the search waited for the reindex to finish")
        self.assertEqual([row["path"] for row in answered[0]["results"]], ["alpha.md"])

    def test_reindex_can_be_asked_for_the_report_without_the_pass(self):
        self.unindexed()
        payload = SEARCHD.do_search([self.vault], "indexed text", 5, reindex=False)
        self.assertEqual(payload["stale"]["aging"]["paths"], ["beta.md"])
        self.assertFalse(payload["stale"]["aging"]["reindexing"])
        self.assertFalse(self.vault.reindexing)


class MatrixCacheTest(unittest.TestCase):
    """A reindex has to reach a search, or the daemon serves the vault it started with."""

    def test_a_reindex_invalidates_the_resident_matrix(self):
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        self.addCleanup(lambda: [v.close() for v in VAULTS])
        vault = build_vault(Path(temp_dir.name) / "cached", "cached",
                            {"alpha.md": "## One\nText.\n"})
        vault.matrix()
        warm = vault.vectors_version
        (vault.root / "beta.md").write_text("## Two\nMore text.\n", encoding="utf-8")
        SEARCHD.do_reindex(vault)
        vault.matrix()
        # a fresh connection per call reads the same data_version forever, which
        # pinned the cache for the life of the daemon
        self.assertNotEqual(vault.vectors_version, warm)


class SemanticGraphTest(unittest.TestCase):
    """Mutual nearest neighbours, on vectors chosen so the answer is known."""

    # two tight pairs and one note far from everything: a and b point at each
    # other, c and d point at each other, e is nobody's nearest.
    META = [
        (1, "a.md", "One", 1), (2, "a.md", "Two", 9),
        (3, "b.md", "One", 1), (4, "c.md", "One", 1),
        (5, "d.md", "One", 1), (6, "e.md", "One", 1),
    ]
    MATRIX = SEARCHD.np.array([
        [1.0, 0.0, 0.0], [1.0, 0.02, 0.0],   # a, pooled from two sections
        [0.99, 0.14, 0.0],                    # b, next to a
        [0.0, 1.0, 0.0], [0.14, 0.99, 0.0],   # c and d, next to each other
        [0.0, 0.0, 1.0],                      # e, orthogonal to all of them
    ], dtype=SEARCHD.np.float32)

    def graph(self, k=1, wikilinks=()):
        return SEARCHD.semantic_graph((self.META, self.MATRIX), list(wikilinks), k)

    def pairs(self, payload):
        nodes = payload["nodes"]
        return {(nodes[edge[0]], nodes[edge[1]]): edge[3] for edge in payload["edges"]}

    def test_sections_pool_into_one_node_per_note(self):
        self.assertEqual(self.graph()["nodes"], ["a.md", "b.md", "c.md", "d.md", "e.md"])

    def test_only_mutual_neighbours_become_edges(self):
        # e's nearest is someone, but nobody's nearest is e, so it draws no edge
        self.assertEqual(set(self.pairs(self.graph())), {("a.md", "b.md"), ("c.md", "d.md")})

    def test_a_wikilink_is_carried_whether_or_not_the_pair_is_near(self):
        edges = self.pairs(self.graph(wikilinks=[("a.md", "b.md"), ("a.md", "e.md")]))
        self.assertEqual(edges[("a.md", "b.md")], 1)  # near and linked
        self.assertEqual(edges[("a.md", "e.md")], 1)  # linked only, and still drawn
        self.assertEqual(edges[("c.md", "d.md")], 0)  # near only

    def test_a_link_to_an_unindexed_note_is_dropped(self):
        self.assertNotIn(("a.md", "gone.md"),
                         self.pairs(self.graph(wikilinks=[("a.md", "gone.md")])))

    def test_a_bigger_k_finds_more_pairs(self):
        self.assertLess(len(self.graph(k=1)["edges"]), len(self.graph(k=3)["edges"]))

    def test_k_is_clamped_to_what_the_corpus_can_answer(self):
        self.assertEqual(self.graph(k=99)["k"], 4)

    def test_a_chunked_pass_gives_the_same_answer(self):
        whole = SEARCHD.semantic_graph((self.META, self.MATRIX), [], 2)
        chunked = SEARCHD.semantic_graph((self.META, self.MATRIX), [], 2, chunk=2)
        self.assertEqual(whole, chunked)

    def test_a_corpus_with_no_vectors_is_empty_rather_than_an_error(self):
        self.assertEqual(SEARCHD.semantic_graph(([], None), [], 10)["nodes"], [])


class DuplicateClustersTest(unittest.TestCase):
    """Pairs above a cutoff, grouped, on vectors chosen so the answer is known."""

    # p, q, r, s are four ways of saying the same thing, x and y are close but
    # not that close, and z is on its own.
    META = [
        (1, "p.md", "One", 1), (2, "q.md", "One", 1), (3, "r.md", "One", 1),
        (4, "s.md", "One", 1), (5, "x.md", "One", 1), (6, "y.md", "One", 1),
        (7, "z.md", "One", 1),
    ]
    MATRIX = SEARCHD.np.array([
        [1.0, 0.0, 0.0], [0.9999, 0.0141, 0.0],
        [0.9995, 0.0316, 0.0], [0.999, 0.0447, 0.0],
        [0.0, 1.0, 0.0], [0.28, 0.96, 0.0],   # 0.96 to each other
        [0.0, 0.0, 1.0],
    ], dtype=SEARCHD.np.float32)

    def clusters(self, threshold=0.99, wikilinks=(), **kwargs):
        return SEARCHD.duplicate_clusters((self.META, self.MATRIX), list(wikilinks),
                                          threshold, **kwargs)

    def test_a_pile_of_duplicates_is_one_row_and_not_every_pair(self):
        payload = self.clusters()
        self.assertEqual(len(payload["clusters"]), 1)
        cluster = payload["clusters"][0]
        self.assertEqual(set(cluster["paths"]), {"p.md", "q.md", "r.md", "s.md"})
        self.assertEqual(len(cluster["pairs"]), 6, "four notes are six pairs, reported once")
        self.assertEqual(payload["pairs"], 6)

    def test_the_threshold_decides_what_counts(self):
        loose = self.clusters(threshold=0.95)
        self.assertEqual({tuple(sorted(cluster["paths"])) for cluster in loose["clusters"]},
                         {("p.md", "q.md", "r.md", "s.md"), ("x.md", "y.md")})
        self.assertEqual(self.clusters(threshold=0.999999)["clusters"], [])

    def test_a_note_is_never_its_own_duplicate(self):
        for cluster in self.clusters(threshold=0.7)["clusters"]:
            for left, right, _, _ in cluster["pairs"]:
                self.assertNotEqual(left, right)

    def test_an_existing_wikilink_is_marked_rather_than_filtered(self):
        cluster = self.clusters(wikilinks=[("p.md", "q.md")])["clusters"][0]
        by_pair = {tuple(sorted((cluster["paths"][left], cluster["paths"][right]))): linked
                   for left, right, _, linked in cluster["pairs"]}
        self.assertEqual(by_pair[("p.md", "q.md")], 1)
        self.assertEqual(by_pair[("p.md", "r.md")], 0)
        self.assertEqual(cluster["unlinked"], 5)

    def test_the_pairs_that_mutual_knn_would_drop_are_found(self):
        # every member of the pile is in every other's top 3, so k=3 mutual
        # nearest neighbours cannot express all six pairs, and the scan does.
        graph = SEARCHD.semantic_graph((self.META, self.MATRIX), [], 3)
        drawn = sum(1 for edge in graph["edges"]
                    if {graph["nodes"][edge[0]], graph["nodes"][edge[1]]} <= {"p.md", "q.md",
                                                                              "r.md", "s.md"})
        self.assertEqual(len(self.clusters()["clusters"][0]["pairs"]), 6)
        self.assertLessEqual(drawn, 6)

    def test_a_chunked_pass_gives_the_same_answer(self):
        self.assertEqual(self.clusters(), self.clusters(chunk=2))

    def test_the_cap_bounds_the_answer_and_says_so(self):
        payload = self.clusters(threshold=0.7, max_pairs=2)
        self.assertTrue(payload["truncated"])
        self.assertLessEqual(payload["pairs"], 3)

    def test_a_corpus_with_no_vectors_is_empty_rather_than_an_error(self):
        self.assertEqual(SEARCHD.duplicate_clusters(([], None), [], 0.95)["clusters"], [])


class GraphRouteTest(unittest.TestCase):
    """The route over a real index, which in this fixture has no vectors."""

    @classmethod
    def setUpClass(cls):
        cls.temp_dir = tempfile.TemporaryDirectory()
        cls.vault = build_vault(Path(cls.temp_dir.name) / "graph", "graph",
                                {"alpha.md": "## One\nSee [[beta]].\n",
                                 "beta.md": "## Two\nText.\n"})
        SEARCHD.STATE = SEARCHD.State([cls.vault])
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), SEARCHD.Handler)
        cls.port = cls.server.server_address[1]
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.vault.close()
        cls.temp_dir.cleanup()

    def test_the_route_answers_and_caches(self):
        status, body = self.get_graph()
        self.assertEqual(status, 200)
        self.assertEqual(body["vault"], "graph")
        self.assertFalse(body["cached"])
        self.assertTrue(self.get_graph()[1]["cached"])
        # this fixture is indexed without embeddings, so there is nothing to place
        self.assertEqual(body["nodes"], [])

    def test_the_wikilinks_are_found_and_the_unresolved_ones_are_not(self):
        pairs = SEARCHD.wikilink_pairs(self.vault)
        self.assertEqual(pairs, [("alpha.md", "beta.md")])

    def test_a_k_that_is_not_a_number(self):
        self.assertEqual(fetch(self.port, "/graph?k=lots")[0], 400)

    def test_the_duplicates_route_answers_and_caches(self):
        status, body = fetch(self.port, "/duplicates")
        self.assertEqual(status, 200)
        self.assertEqual((body["vault"], body["threshold"]), ("graph", 0.95))
        self.assertFalse(body["cached"])
        self.assertTrue(fetch(self.port, "/duplicates")[1]["cached"])
        self.assertEqual(body["clusters"], [])  # no embeddings in this fixture

    def test_a_threshold_below_the_floor_is_clamped_rather_than_refused(self):
        self.assertEqual(fetch(self.port, "/duplicates?threshold=0.1")[1]["threshold"], 0.7)

    def test_a_threshold_that_is_not_a_number(self):
        self.assertEqual(fetch(self.port, "/duplicates?threshold=high")[0], 400)

    def get_graph(self):
        return fetch(self.port, "/graph")


class RecencyRouteTest(unittest.TestCase):
    """A real git-committed fixture, since &recency= needs actual commit
    timestamps, not the plain build_vault fixture the other classes use."""

    @classmethod
    def setUpClass(cls):
        cls.temp_dir = tempfile.TemporaryDirectory()
        cls.vault = build_vault(Path(cls.temp_dir.name) / "recency", "recency", {
            "alpha.md": "## Alpha\ntext\n",
            "beta.md": "## Beta\ncompanion, committed 30 minutes after alpha\n",
            "gamma.md": "## Gamma\nunrelated, committed years apart\n",
        })
        root = cls.vault.root
        run = lambda *args, when=None: subprocess.run(
            ["git", *args], cwd=root, check=True, capture_output=True,
            env={**os.environ, "GIT_AUTHOR_DATE": when, "GIT_COMMITTER_DATE": when} if when else None,
        )
        run("init", "-q")
        run("config", "user.email", "t@t")
        run("config", "user.name", "t")
        run("add", "alpha.md")
        run("commit", "-q", "-m", "alpha", when="2026-01-01T10:00:00+00:00")
        run("add", "beta.md")
        run("commit", "-q", "-m", "beta", when="2026-01-01T10:30:00+00:00")  # 30 min later, inside RECENCY_TAU_HOURS
        run("add", "gamma.md")
        run("commit", "-q", "-m", "gamma", when="2020-01-01T00:00:00+00:00")  # years away

        SEARCHD.STATE = SEARCHD.State([cls.vault])
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), SEARCHD.Handler)
        cls.port = cls.server.server_address[1]
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.vault.close()
        for attempt in range(3):
            try:
                cls.temp_dir.cleanup()
                return
            except PermissionError:
                if attempt == 2:
                    raise
                time.sleep(0.2)

    def test_recency_surfaces_a_same_session_note_when_vectors_are_empty(self):
        # this fixture has no embeddings, so without &recency= /similar finds
        # nothing for alpha; with it, beta (30 minutes later) should appear
        # from the recency window alone, scored at exactly RECENCY_LAMBDA
        # since its base vector score is unknown (0.0, the conservative floor)
        _, plain = fetch(self.port, "/similar?note=alpha")
        self.assertEqual(plain["results"], [])
        status, body = fetch(self.port, "/similar?note=alpha&recency=1")
        self.assertEqual(status, 200)
        self.assertEqual([row["path"] for row in body["results"]], ["beta.md"])
        self.assertAlmostEqual(body["results"][0]["score"], SEARCHD.RECENCY_LAMBDA)
        self.assertEqual(body["results"][0]["heading"], "Beta")

    def test_gamma_is_too_far_away_to_be_surfaced(self):
        _, body = fetch(self.port, "/similar?note=gamma&recency=1")
        self.assertEqual(body["results"], [])

    def test_similar_without_recency_hints_when_a_near_note_exists(self):
        _, near = fetch(self.port, "/similar?note=alpha")
        self.assertIn("recency=1", near["recency_hint"])
        _, far = fetch(self.port, "/similar?note=gamma")
        self.assertNotIn("recency_hint", far)


class FusionRouteTest(unittest.TestCase):
    """`&fusion=1`: the calibrated additive stack (recency + co-commit + AA),
    same real git-committed fixture RecencyRouteTest needs since fusion folds
    the recency term in too."""

    @classmethod
    def setUpClass(cls):
        cls.temp_dir = tempfile.TemporaryDirectory()
        cls.vault = build_vault(Path(cls.temp_dir.name) / "fusion", "fusion", {
            "alpha.md": "## Alpha\ntext\n",
            "beta.md": "## Beta\ncompanion, committed 30 minutes after alpha\n",
            "gamma.md": "## Gamma\nunrelated, committed years apart\n",
            "epsilon.md": "## Epsilon\nno recency link, committed years apart, "
                          "but co-committed with alpha\n",
        })
        root = cls.vault.root
        run = lambda *args, when=None: subprocess.run(
            ["git", *args], cwd=root, check=True, capture_output=True,
            env={**os.environ, "GIT_AUTHOR_DATE": when, "GIT_COMMITTER_DATE": when} if when else None,
        )
        run("init", "-q")
        run("config", "user.email", "t@t")
        run("config", "user.name", "t")
        run("add", "alpha.md")
        run("commit", "-q", "-m", "alpha", when="2026-01-01T10:00:00+00:00")
        run("add", "beta.md")
        run("commit", "-q", "-m", "beta", when="2026-01-01T10:30:00+00:00")  # inside RECENCY_TAU_HOURS
        run("add", "gamma.md")
        run("commit", "-q", "-m", "gamma", when="2020-01-01T00:00:00+00:00")
        run("add", "epsilon.md")
        run("commit", "-q", "-m", "epsilon", when="2021-01-01T00:00:00+00:00")

        SEARCHD.STATE = SEARCHD.State([cls.vault])
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), SEARCHD.Handler)
        cls.port = cls.server.server_address[1]
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.vault.close()
        for attempt in range(3):
            try:
                cls.temp_dir.cleanup()
                return
            except PermissionError:
                if attempt == 2:
                    raise
                time.sleep(0.2)

    def with_co_commit_db(self, *rows):
        """Same throwaway-file swap SearchDaemonTest.with_co_commit_db uses,
        copied rather than shared across classes since each owns its own
        temp_dir and cleanup order."""
        original = SEARCHD.co_commit.DEFAULT_DB
        db = Path(self.temp_dir.name) / f"co_commit_{uuid.uuid4().hex}.db"
        connection = SEARCHD.co_commit.connect(db)
        with connection:
            connection.executemany("INSERT INTO co_commits VALUES (?, ?, ?, ?, ?, ?, ?)", rows)
        connection.execute("PRAGMA wal_checkpoint(TRUNCATE);")
        connection.close()
        SEARCHD.co_commit.DEFAULT_DB = db
        self.addCleanup(setattr, SEARCHD.co_commit, "DEFAULT_DB", original)

    def test_fusion_surfaces_a_fused_ranking_beyond_recency_alone(self):
        # weight 10 caps at cc_prox=1.0 (min(10/5, 1)), so epsilon's co-commit
        # term (FUSION_LAMBDA_COCOMMIT * 1.0 = 1.5) dominates beta's recency
        # term (FUSION_LAMBDA_RECENCY = 0.05) - epsilon ranks first even
        # though it has no recency relationship to alpha at all, which
        # &recency=1 alone could never surface.
        self.with_co_commit_db(("fusion", "alpha.md", "epsilon.md", 10.0, 4, "2026-08-31", "abc1234"))
        status, body = fetch(self.port, "/similar?note=alpha&fusion=1")
        self.assertEqual(status, 200)
        self.assertEqual([row["path"] for row in body["results"]], ["epsilon.md", "beta.md"])
        self.assertAlmostEqual(body["results"][0]["score"], SEARCHD.FUSION_LAMBDA_COCOMMIT)
        self.assertAlmostEqual(body["results"][1]["score"], SEARCHD.FUSION_LAMBDA_RECENCY)
        # gamma has neither signal, so it is never even a candidate
        self.assertNotIn("gamma.md", [row["path"] for row in body["results"]])

    def test_fusion_hint_appears_when_either_signal_exists_and_not_when_fused(self):
        _, plain = fetch(self.port, "/similar?note=alpha")
        self.assertIn("fusion=1", plain["fusion_hint"])
        # already fused, so the hint recommending it would be circular
        _, fused = fetch(self.port, "/similar?note=alpha&fusion=1")
        self.assertNotIn("fusion_hint", fused)

    def test_fusion_hint_absent_when_neither_signal_exists(self):
        # gamma has no near-in-time note and (with the default empty
        # co_commit db restored by the previous test's cleanup) no co-commit
        # edge either
        _, body = fetch(self.port, "/similar?note=gamma")
        self.assertNotIn("fusion_hint", body)

    def test_fusion_ignores_graph_and_recency_when_combined_not_double_counted(self):
        # &fusion=1 already folds recency and co-commit in; stacking either
        # flag alongside it must not add the same boost a second time - the
        # elif chain in do_similar means fusion simply wins and the other
        # flags are inert here, which this checks by exact score equality
        # rather than by inspecting the implementation.
        self.with_co_commit_db(("fusion", "alpha.md", "epsilon.md", 10.0, 4, "2026-08-31", "abc1234"))
        _, fusion_only = fetch(self.port, "/similar?note=alpha&fusion=1")
        _, with_recency = fetch(self.port, "/similar?note=alpha&fusion=1&recency=1")
        _, with_graph = fetch(self.port, "/similar?note=alpha&fusion=1&graph=1")
        self.assertEqual(fusion_only["results"], with_recency["results"])
        self.assertEqual(fusion_only["results"], with_graph["results"])


class FusionZHubDegreeTest(unittest.TestCase):
    """`&fusion=1`'s AA term, z_hub_degree-cut: the same-batch/same-template
    false positive named in shared_neighbor_experiment.py's score_all
    docstring and the survey note's "the same-batch/same-template false
    positive: investigated" section - two notes whose only connection is a
    wikilink to a shared high-degree hub note must not get a nonzero AA
    contribution from it once FUSION_Z_HUB_DEGREE is exceeded, while a note
    sharing a genuinely narrow (low-degree) neighbour still does. No git
    fixture needed here (unlike Recency/FusionRouteTest): the AA term reads
    the wikilink graph, not commit timestamps, and creation_index() degrades
    to an empty `near` set with no git history rather than erroring."""

    @classmethod
    def setUpClass(cls):
        cls.temp_dir = tempfile.TemporaryDirectory()
        notes = {
            "north.md": "## North\nanchor note. [[hub]] [[narrow]]\n",
            "south.md": "## South\nshares only the hub with north - no real relationship. [[hub]]\n",
            "east.md": "## East\nshares narrow, a genuinely specific neighbour, with north. [[narrow]]\n",
            "hub.md": "## Hub\na same-session catalog/index note linked from everywhere.\n",
            "narrow.md": "## Narrow\na specific note linked from exactly two others.\n",
        }
        # 19 filler notes linking only to hub, plus north and south already
        # linking to it, pushes hub's wikilink degree to 21 - past the
        # default FUSION_Z_HUB_DEGREE of 20. narrow stays at degree 2.
        for i in range(19):
            notes[f"filler{i:02d}.md"] = f"## Filler {i}\nlinks only to the hub. [[hub]]\n"
        cls.vault = build_vault(Path(cls.temp_dir.name) / "zhub", "zhub", notes)

        SEARCHD.STATE = SEARCHD.State([cls.vault])
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), SEARCHD.Handler)
        cls.port = cls.server.server_address[1]
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.vault.close()
        for attempt in range(3):
            try:
                cls.temp_dir.cleanup()
                return
            except PermissionError:
                if attempt == 2:
                    raise
                time.sleep(0.2)

    def with_co_commit_db(self, *rows):
        """Same throwaway-file swap SearchDaemonTest/FusionRouteTest use."""
        original = SEARCHD.co_commit.DEFAULT_DB
        db = Path(self.temp_dir.name) / f"co_commit_{uuid.uuid4().hex}.db"
        connection = SEARCHD.co_commit.connect(db)
        with connection:
            connection.executemany("INSERT INTO co_commits VALUES (?, ?, ?, ?, ?, ?, ?)", rows)
        connection.execute("PRAGMA wal_checkpoint(TRUNCATE);")
        connection.close()
        SEARCHD.co_commit.DEFAULT_DB = db
        self.addCleanup(setattr, SEARCHD.co_commit, "DEFAULT_DB", original)

    def test_hub_bridge_scores_zero_aa_while_a_narrow_shared_neighbour_still_scores(self):
        # sanity: the fixture actually stresses the cutoff under test
        wl_neighbors = SEARCHD.shared_neighbor.build_neighbor_sets(SEARCHD.wikilink_pairs(self.vault))
        self.assertGreater(len(wl_neighbors["hub.md"]), SEARCHD.FUSION_Z_HUB_DEGREE)
        self.assertLessEqual(len(wl_neighbors["narrow.md"]), SEARCHD.FUSION_Z_HUB_DEGREE)

        # identical co-commit weight for both, so south and east differ only
        # on the AA term - south's only shared neighbour is the hub (over the
        # cutoff, zeroed), east's is narrow (under it, kept)
        self.with_co_commit_db(
            ("zhub", "north.md", "south.md", 1.0, 1, "2026-08-31", "abc1234"),
            ("zhub", "north.md", "east.md", 1.0, 1, "2026-08-31", "abc1235"),
        )
        status, body = fetch(self.port, "/similar?note=north&fusion=1")
        self.assertEqual(status, 200)
        scores = {row["path"]: row["score"] for row in body["results"]}
        cc_only = round(SEARCHD.FUSION_LAMBDA_COCOMMIT * min(1.0 / 5.0, 1.0), 6)
        # south's shared neighbour (hub) is over the cutoff - AA contributes
        # nothing, so its score is exactly the co-commit term alone
        self.assertAlmostEqual(scores["south.md"], cc_only)
        # east's shared neighbour (narrow) is under the cutoff - AA still
        # contributes, so east outranks south despite identical co-commit weight
        self.assertGreater(scores["east.md"], scores["south.md"])
        self.assertEqual([row["path"] for row in body["results"]], ["east.md", "south.md"])


if __name__ == "__main__":
    unittest.main()
