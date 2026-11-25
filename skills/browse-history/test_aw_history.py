#!/usr/bin/env python3
"""Unit tests for aw_history.py."""

from __future__ import annotations

import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import aw_history  # noqa: E402


class TestSearchExtraction(unittest.TestCase):
    def test_google_search_extraction(self) -> None:
        url = "https://www.google.com/search?q=python+activitywatch+api&oq=python"
        self.assertEqual(
            aw_history.extract_search_query(url),
            ("google", "python activitywatch api"),
        )

    def test_google_regional_tld(self) -> None:
        url = "https://www.google.co.uk/search?q=patagonia+outlet"
        self.assertEqual(
            aw_history.extract_search_query(url),
            ("google", "patagonia outlet"),
        )

    def test_duckduckgo_search_extraction(self) -> None:
        url = "https://duckduckgo.com/?q=local+first+sqlite&ia=web"
        self.assertEqual(
            aw_history.extract_search_query(url),
            ("duckduckgo", "local first sqlite"),
        )

    def test_bing_search_extraction(self) -> None:
        url = "https://www.bing.com/search?q=systemd+user+timer"
        self.assertEqual(
            aw_history.extract_search_query(url),
            ("bing", "systemd user timer"),
        )

    def test_non_search_url_with_q_param_ignored(self) -> None:
        url = "https://example.com/items?q=not-a-search-engine"
        self.assertIsNone(aw_history.extract_search_query(url))

    def test_sanitize_url_redacts_sensitive_params(self) -> None:
        url = "https://app.example.com/callback?code=secret123&state=ok&access_token=tok456"
        sanitized = aw_history.sanitize_url(url)
        self.assertIn("code=REDACTED", sanitized)
        self.assertIn("access_token=REDACTED", sanitized)
        self.assertIn("state=ok", sanitized)
        self.assertNotIn("secret123", sanitized)
        self.assertNotIn("tok456", sanitized)

    def test_google_non_search_path_ignored(self) -> None:
        url = "https://www.google.com/maps?q=london"
        self.assertIsNone(aw_history.extract_search_query(url))


class TestDeduplication(unittest.TestCase):
    def test_deduplicates_rapid_heartbeats_within_60s(self) -> None:
        raw = [
            {
                "timestamp": "2026-11-25T10:00:00+00:00",
                "duration": 10.0,
                "data": {"url": "https://example.com/a", "title": "Page A"},
            },
            {
                "timestamp": "2026-11-25T10:00:30+00:00",
                "duration": 15.0,
                "data": {"url": "https://example.com/a", "title": "Page A"},
            },
            {
                "timestamp": "2026-11-25T10:03:00+00:00",
                "duration": 5.0,
                "data": {"url": "https://example.com/a", "title": "Page A"},
            },
        ]
        events = [aw_history.normalize_event(r, "aw-watcher-web-chrome_host") for r in raw]
        deduped = aw_history.deduplicate_events([e for e in events if e is not None])
        self.assertEqual(len(deduped), 2)
        # Newest first: 10:03:00 (5s), then merged 10:00:30 (25s)
        self.assertEqual(deduped[0]["timestamp"], "2026-11-25T10:03:00+00:00")
        self.assertEqual(deduped[1]["timestamp"], "2026-11-25T10:00:30+00:00")
        self.assertAlmostEqual(deduped[1]["duration"], 25.0)

    def test_deduplicates_search_urls_with_different_tracking_params(self) -> None:
        raw = [
            {
                "timestamp": "2026-11-25T10:00:00+00:00",
                "duration": 2.0,
                "data": {"url": "https://www.google.com/search?q=foo+bar&ei=aaa", "title": "foo bar - Google Search"},
            },
            {
                "timestamp": "2026-11-25T10:00:10+00:00",
                "duration": 8.0,
                "data": {"url": "https://www.google.com/search?q=foo+bar&ei=bbb", "title": "foo bar - Google Search"},
            },
        ]
        events = [aw_history.normalize_event(r, "aw-watcher-web-firefox_host") for r in raw]
        deduped = aw_history.deduplicate_events([e for e in events if e is not None])
        self.assertEqual(len(deduped), 1)
        self.assertAlmostEqual(deduped[0]["duration"], 10.0)


class TestFilteringAndAggregation(unittest.TestCase):
    def setUp(self) -> None:
        raw = [
            {
                "timestamp": "2026-11-25T12:00:00+00:00",
                "duration": 20.0,
                "data": {
                    "url": "https://www.google.com/search?q=taskwarrior+hooks",
                    "title": "taskwarrior hooks - Google Search",
                },
            },
            {
                "timestamp": "2026-11-24T09:00:00+00:00",
                "duration": 45.0,
                "data": {
                    "url": "https://docs.python.org/3/library/urllib.request.html",
                    "title": "urllib.request — Extensible library for opening URLs",
                },
            },
            {
                "timestamp": "2026-11-10T08:00:00+00:00",
                "duration": 12.0,
                "data": {
                    "url": "https://github.com/ActivityWatch/activitywatch",
                    "title": "ActivityWatch/activitywatch",
                },
            },
        ]
        self.events = [
            e
            for r in raw
            if (e := aw_history.normalize_event(r, "aw-watcher-web-firefox_host")) is not None
        ]

    def test_keyword_query_matches_url_title_and_search(self) -> None:
        res = aw_history.filter_events(self.events, query="taskwarrior")
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0]["search_query"], "taskwarrior hooks")

        res2 = aw_history.filter_events(self.events, query="extensible library")
        self.assertEqual(len(res2), 1)
        self.assertIn("docs.python.org", res2[0]["url"])

    def test_searches_only_filter(self) -> None:
        res = aw_history.filter_events(self.events, searches_only=True)
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0]["search_engine"], "google")

    def test_domain_filter(self) -> None:
        res = aw_history.filter_events(self.events, domain="python.org")
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0]["domain"], "docs.python.org")

        # Must not match partial suffix without dot boundary
        res_empty = aw_history.filter_events(self.events, domain="hub.com")
        self.assertEqual(len(res_empty), 0)

    def test_date_range_filter(self) -> None:
        now = datetime(2026, 11, 25, 15, 0, 0, tzinfo=timezone.utc)
        start, end = aw_history.compute_date_range(days=7, now=now)
        res = aw_history.filter_events(self.events, start_dt=start, end_dt=end)
        self.assertEqual(len(res), 2)

        start_f, end_f = aw_history.compute_date_range(
            from_date="2026-11-24", to_date="2026-11-24", now=now
        )
        res_f = aw_history.filter_events(self.events, start_dt=start_f, end_dt=end_f)
        self.assertEqual(len(res_f), 1)
        self.assertEqual(res_f[0]["domain"], "docs.python.org")

    def test_top_domains(self) -> None:
        rows = aw_history.aggregate_top_domains(self.events, limit=2)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["domain"], "docs.python.org")
        self.assertEqual(rows[0]["count"], 1)

    def test_timeline_aggregation(self) -> None:
        days = aw_history.aggregate_timeline(self.events, limit=10)
        self.assertEqual(len(days), 3)
        self.assertEqual(days[0]["date"], "2026-11-25")
        self.assertEqual(days[0]["visits"], 1)
        self.assertEqual(days[0]["searches"], ["taskwarrior hooks"])
        self.assertEqual(days[1]["date"], "2026-11-24")
        self.assertEqual(days[1]["top_domains"][0]["domain"], "docs.python.org")


if __name__ == "__main__":
    unittest.main()
