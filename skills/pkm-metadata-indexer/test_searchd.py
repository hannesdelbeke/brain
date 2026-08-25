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


class SearchDaemonTest(unittest.TestCase):
    """Runs against a real index built without embeddings, so no model is loaded."""

    @classmethod
    def build_vault(cls, name: str, notes: dict[str, str]):
        root = Path(cls.temp_dir.name) / name
        (root / ".obsidian").mkdir(parents=True)
        for filename, text in notes.items():
            (root / filename).write_text(text, encoding="utf-8")
        db = root / ".obsidian" / "pkm_index.db"
        SEARCHD.pkm.build_index(vault_path=str(root), db_path=str(db), skip_embeddings=True)
        return SEARCHD.Vault(name, root, db)

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
        request = urllib.request.Request(
            f"http://127.0.0.1:{self.port}{path}", headers=headers or {}, method=method
        )
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                return response.status, json.loads(response.read())
        except urllib.error.HTTPError as error:
            return error.code, json.loads(error.read())

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


if __name__ == "__main__":
    unittest.main()
