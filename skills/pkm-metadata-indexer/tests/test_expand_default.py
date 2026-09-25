"""Entity expansion is opt-in, and the default has to reach the wire.

A judged a/b over 20 questions found expansion costing 39 points of precision@10
(20.5% against 59.5%) and 360ms at p50, while leaving mean first-useful rank
unchanged at 1.3 against 1.4. So it degrades results 2 through 10 without
improving the top hit, which is what the RRF arithmetic predicts: expansion buys
extra list memberships, and below a pool depth of 62 membership dominates rank
position in the fused score, so the tail fills with sections that are merely
present in some list.

Asserting `parse_args([]).expand is False` alone would be thin -- it restates the
default rather than testing it. The flag matters only if it reaches the daemon, so
the test that earns its place captures the outbound query string from a stub
daemon and checks for `expand=0`. That catches the regression the parser test
cannot see: a default left False while something downstream re-enables expansion.
"""

import importlib.util
import json
import subprocess
import sys
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

SKILL = Path(__file__).resolve().parents[1]

SPEC = importlib.util.spec_from_file_location("expand_default_search_vault",
                                              SKILL / "search_vault.py")
SEARCH = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SEARCH)

PAYLOAD = {
    "vault": "stub",
    "results": [],
    # A dict of corpus name -> missing files, not a list; print_stale calls .items().
    "stale": {},
    "indexed_at": {"stub": "2026-09-25T00:00:00"},
    "took_ms": 1,
}


class CapturingDaemon(BaseHTTPRequestHandler):
    """Answers /search with an empty result set and records the query string."""

    searches: list[dict] = []

    def do_GET(self):  # noqa: N802 - BaseHTTPRequestHandler's spelling
        parsed = urlparse(self.path)
        if parsed.path == "/search":
            type(self).searches.append(parse_qs(parsed.query))
        body = json.dumps(PAYLOAD).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass


class ExpandReachesTheWireTest(unittest.TestCase):
    def setUp(self):
        CapturingDaemon.searches = []
        self.server = HTTPServer(("127.0.0.1", 0), CapturingDaemon)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base = f"http://127.0.0.1:{self.server.server_port}"

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)

    def run_search(self, *extra: str) -> subprocess.CompletedProcess:
        completed = subprocess.run(
            [sys.executable, str(SKILL / "search_vault.py"), "anything",
             "--daemon", self.base, "--no-spawn", *extra],
            capture_output=True, text=True, timeout=60,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        return completed

    def sent(self) -> dict:
        self.assertEqual(len(CapturingDaemon.searches), 1, CapturingDaemon.searches)
        return CapturingDaemon.searches[0]

    def test_the_default_asks_the_daemon_not_to_expand(self):
        self.run_search()
        self.assertEqual(self.sent()["expand"], ["0"])

    def test_the_flag_still_turns_expansion_on(self):
        self.run_search("--expand")
        self.assertEqual(self.sent()["expand"], ["1"])

    def test_no_expand_is_explicit_about_it(self):
        self.run_search("--no-expand")
        self.assertEqual(self.sent()["expand"], ["0"])


class ExpandDefaultTest(unittest.TestCase):
    """The CLI contract, independent of whether a daemon is reachable."""

    def test_expansion_is_opt_in(self):
        self.assertIs(SEARCH.build_parser().parse_args(["query"]).expand, False)

    def test_both_directions_are_spellable(self):
        parser = SEARCH.build_parser()
        self.assertIs(parser.parse_args(["query", "--expand"]).expand, True)
        self.assertIs(parser.parse_args(["query", "--no-expand"]).expand, False)

    def test_the_help_text_says_why_it_is_off(self):
        # The measurement is the justification, so it travels with the flag
        # rather than living only in a commit message nobody reads at the prompt.
        help_text = SEARCH.build_parser().format_help()
        self.assertIn("59.5%", help_text)


if __name__ == "__main__":
    unittest.main()
