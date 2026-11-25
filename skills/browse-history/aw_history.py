#!/usr/bin/env python3
"""Query local ActivityWatch browser and search history across aw-watcher-web-* buckets."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any

DEFAULT_BASE_URL = "http://127.0.0.1:5600/api/0"
WEB_BUCKET_PREFIX = "aw-watcher-web-"
DEDUP_WINDOW_SECONDS = 60.0

_GOOGLE_HOST_RE = re.compile(r"^(?:www\.)?google\.[a-z]{2,}(?:\.[a-z]{2,})?$")
_DDG_HOST_RE = re.compile(r"^(?:[a-z0-9-]+\.)?duckduckgo\.com$")
_BING_HOST_RE = re.compile(r"^(?:www\.)?bing\.com$")


def parse_timestamp(ts: str) -> datetime:
    """Parse an ISO 8601 timestamp string into a timezone-aware datetime."""
    if ts.endswith("Z"):
        ts = ts[:-1] + "+00:00"
    dt = datetime.fromisoformat(ts)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def extract_domain(url: str) -> str:
    """Extract normalized lowercase hostname (without port or leading www.) from a URL."""
    if not url:
        return ""
    parsed = urllib.parse.urlparse(url)
    host = (parsed.hostname or "").lower()
    if host.startswith("www."):
        host = host[4:]
    return host


def extract_search_query(url: str) -> tuple[str, str] | None:
    """Return (engine, query) if url is a Google, DuckDuckGo, or Bing search URL, else None."""
    if not url:
        return None
    parsed = urllib.parse.urlparse(url)
    host = (parsed.hostname or "").lower()
    path = parsed.path or "/"
    params = urllib.parse.parse_qs(parsed.query)
    q_values = params.get("q")
    if not q_values:
        return None
    query = q_values[0].strip()
    if not query:
        return None

    if _GOOGLE_HOST_RE.match(host) and path.startswith("/search"):
        return ("google", query)
    if _DDG_HOST_RE.match(host) and path in ("/", "/html/", "/lite/"):
        return ("duckduckgo", query)
    if _BING_HOST_RE.match(host) and path.startswith("/search"):
        return ("bing", query)
    return None


def infer_browser(bucket_id: str) -> str:
    """Infer a short browser/source label from an aw-watcher-web-* bucket id."""
    rest = bucket_id[len(WEB_BUCKET_PREFIX) :] if bucket_id.startswith(WEB_BUCKET_PREFIX) else bucket_id
    for token in ("chrome", "firefox", "android", "brave", "edge", "safari", "vivaldi", "opera"):
        if token in rest.lower():
            return token
    return rest.split("_")[0].split("-")[0] or "web"


def domain_matches(url: str, target_domain: str) -> bool:
    """Return True if url's host matches target_domain exactly or as a subdomain."""
    host = extract_domain(url)
    target = target_domain.strip().lower()
    if target.startswith("www."):
        target = target[4:]
    if not host or not target:
        return False
    return host == target or host.endswith("." + target)


def compute_date_range(
    days: int = 7,
    today: bool = False,
    from_date: str | None = None,
    to_date: str | None = None,
    now: datetime | None = None,
) -> tuple[datetime, datetime]:
    """Resolve CLI date flags into a (start_dt, end_dt) pair in local timezone."""
    current = now if now is not None else datetime.now().astimezone()
    tz = current.tzinfo or timezone.utc

    if today:
        start = current.replace(hour=0, minute=0, second=0, microsecond=0)
        end = current
        return start, end

    if from_date:
        d_from = datetime.strptime(from_date, "%Y-%m-%d").replace(tzinfo=tz)
        start = d_from.replace(hour=0, minute=0, second=0, microsecond=0)
    else:
        start = None

    if to_date:
        d_to = datetime.strptime(to_date, "%Y-%m-%d").replace(tzinfo=tz)
        end = d_to.replace(hour=23, minute=59, second=59, microsecond=999999)
    else:
        end = current

    if start is None:
        start = end - timedelta(days=days)

    return start, end


def normalize_event(raw: dict[str, Any], bucket_id: str) -> dict[str, Any] | None:
    """Normalize a raw ActivityWatch event dict; return None if it has no URL."""
    data = raw.get("data") or {}
    url = (data.get("url") or "").strip()
    if not url:
        return None
    title = (data.get("title") or "").strip()
    ts_str = raw.get("timestamp") or ""
    if not ts_str:
        return None
    ts = parse_timestamp(ts_str)
    duration = float(raw.get("duration") or 0.0)
    search_info = extract_search_query(url)
    return {
        "timestamp": ts_str,
        "dt": ts,
        "duration": duration,
        "bucket": bucket_id,
        "browser": infer_browser(bucket_id),
        "url": url,
        "title": title,
        "domain": extract_domain(url),
        "search_engine": search_info[0] if search_info else None,
        "search_query": search_info[1] if search_info else None,
    }


def deduplicate_events(
    events: list[dict[str, Any]],
    window_seconds: float = DEDUP_WINDOW_SECONDS,
) -> list[dict[str, Any]]:
    """Deduplicate rapid/consecutive (url, title) heartbeats within window_seconds.

    Returns events sorted newest-first.
    """
    sorted_asc = sorted(events, key=lambda e: e["dt"])
    kept: list[dict[str, Any]] = []
    last_idx_by_key: dict[tuple[str, str], int] = {}

    for ev in sorted_asc:
        if ev.get("search_query"):
            key: tuple[str, ...] = ("search", ev["search_engine"] or "", ev["search_query"])
        else:
            key = (ev["url"], ev["title"])
        prev_idx = last_idx_by_key.get(key)
        if prev_idx is not None:
            prev = kept[prev_idx]
            delta = (ev["dt"] - prev["dt"]).total_seconds()
            if 0 <= delta <= window_seconds:
                prev["duration"] = round(prev["duration"] + ev["duration"], 3)
                prev["dt"] = ev["dt"]
                prev["timestamp"] = ev["timestamp"]
                continue
        last_idx_by_key[key] = len(kept)
        kept.append(dict(ev))

    kept.sort(key=lambda e: e["dt"], reverse=True)
    return kept


def filter_events(
    events: list[dict[str, Any]],
    query: str | None = None,
    searches_only: bool = False,
    domain: str | None = None,
    start_dt: datetime | None = None,
    end_dt: datetime | None = None,
) -> list[dict[str, Any]]:
    """Apply date, search-only, domain, and substring query filters."""
    q_lower = query.lower() if query else None
    result: list[dict[str, Any]] = []

    for ev in events:
        if start_dt is not None and ev["dt"] < start_dt:
            continue
        if end_dt is not None and ev["dt"] > end_dt:
            continue
        if searches_only and not ev.get("search_query"):
            continue
        if domain and not domain_matches(ev["url"], domain):
            continue
        if q_lower:
            haystack = " ".join(
                part
                for part in (ev.get("url", ""), ev.get("title", ""), ev.get("search_query") or "")
                if part
            ).lower()
            if q_lower not in haystack:
                continue
        result.append(ev)

    return result


def aggregate_top_domains(events: list[dict[str, Any]], limit: int = 30) -> list[dict[str, Any]]:
    """Aggregate event counts and total duration per domain, sorted by count desc."""
    stats: dict[str, dict[str, Any]] = defaultdict(lambda: {"count": 0, "duration": 0.0})
    for ev in events:
        dom = ev.get("domain") or "(unknown)"
        stats[dom]["count"] += 1
        stats[dom]["duration"] += float(ev.get("duration") or 0.0)

    rows = [
        {"domain": dom, "count": info["count"], "duration": round(info["duration"], 1)}
        for dom, info in stats.items()
    ]
    rows.sort(key=lambda r: (r["count"], r["duration"]), reverse=True)
    return rows[:limit]


def _http_get_json(url: str, timeout: float = 10.0) -> Any:
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def fetch_web_buckets(base_url: str) -> list[str]:
    """Return sorted list of aw-watcher-web-* bucket IDs from ActivityWatch."""
    buckets = _http_get_json(f"{base_url.rstrip('/')}/buckets/")
    return sorted(bid for bid in buckets.keys() if bid.startswith(WEB_BUCKET_PREFIX))


def fetch_bucket_events(
    base_url: str,
    bucket_id: str,
    start_dt: datetime,
    end_dt: datetime,
) -> list[dict[str, Any]]:
    """Fetch raw events for a bucket within [start_dt, end_dt]."""
    params = urllib.parse.urlencode(
        {
            "start": start_dt.astimezone(timezone.utc).isoformat(),
            "end": end_dt.astimezone(timezone.utc).isoformat(),
            "limit": -1,
        }
    )
    url = f"{base_url.rstrip('/')}/buckets/{urllib.parse.quote(bucket_id, safe='')}/events?{params}"
    return _http_get_json(url)


def _format_local_time(dt: datetime) -> str:
    return dt.astimezone().strftime("%Y-%m-%d %H:%M")


def _serialize_event(ev: dict[str, Any]) -> dict[str, Any]:
    out = {
        "timestamp": ev["timestamp"],
        "browser": ev["browser"],
        "bucket": ev["bucket"],
        "url": ev["url"],
        "title": ev["title"],
        "domain": ev["domain"],
        "duration": round(ev["duration"], 3),
    }
    if ev.get("search_query"):
        out["search_engine"] = ev["search_engine"]
        out["search_query"] = ev["search_query"]
    return out


def format_text_events(events: list[dict[str, Any]], searches_only: bool = False) -> str:
    """Format events as compact lines for agents and terminal users."""
    if not events:
        return "No matching browsing history found."
    lines: list[str] = []
    for ev in events:
        ts = _format_local_time(ev["dt"])
        browser = ev["browser"]
        if searches_only and ev.get("search_query"):
            lines.append(f"[{ts}] ({browser}) [{ev['search_engine']}] {ev['search_query']}")
        else:
            title = ev["title"] or "(no title)"
            lines.append(f"[{ts}] ({browser}) {title} — {ev['url']}")
    return "\n".join(lines)


def format_text_domains(rows: list[dict[str, Any]]) -> str:
    """Format top domains summary as compact lines."""
    if not rows:
        return "No matching browsing history found."
    lines = [
        f"{r['count']:>5} visits  {r['duration']:>7.1f}s  {r['domain']}"
        for r in rows
    ]
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="aw-history",
        description="Query ActivityWatch browser and search history across all aw-watcher-web-* buckets.",
    )
    parser.add_argument(
        "query",
        nargs="?",
        help="Case-insensitive substring match against url, title, and extracted search query.",
    )
    parser.add_argument("--days", type=int, default=7, help="Look back N days (default: 7).")
    parser.add_argument("--today", action="store_true", help="Restrict to today (local time).")
    parser.add_argument("--from", dest="from_date", metavar="YYYY-MM-DD", help="Start date (inclusive).")
    parser.add_argument("--to", dest="to_date", metavar="YYYY-MM-DD", help="End date (inclusive).")
    parser.add_argument(
        "--searches",
        action="store_true",
        help="Filter to Google, DuckDuckGo, and Bing search URLs and extract q=.",
    )
    parser.add_argument("--domain", help="Filter to URLs matching domain (exact or subdomain).")
    parser.add_argument(
        "--top-domains",
        action="store_true",
        help="Rank top domains by visit count across matching events.",
    )
    parser.add_argument("--limit", type=int, default=30, help="Max results to return (default: 30).")
    parser.add_argument("--json", action="store_true", dest="as_json", help="Output JSON.")
    parser.add_argument(
        "--base-url",
        default=os.environ.get("AW_BASE_URL", DEFAULT_BASE_URL),
        help=argparse.SUPPRESS,
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        start_dt, end_dt = compute_date_range(
            days=args.days,
            today=args.today,
            from_date=args.from_date,
            to_date=args.to_date,
        )
    except ValueError as exc:
        print(f"aw-history: invalid date format: {exc}", file=sys.stderr)
        return 2

    try:
        bucket_ids = fetch_web_buckets(args.base_url)
    except urllib.error.URLError as exc:
        print(
            f"aw-history: could not connect to ActivityWatch at {args.base_url} ({exc.reason})",
            file=sys.stderr,
        )
        return 1

    normalized: list[dict[str, Any]] = []
    for bid in bucket_ids:
        try:
            raw_events = fetch_bucket_events(args.base_url, bid, start_dt, end_dt)
        except urllib.error.URLError as exc:
            print(f"aw-history: warning: failed to fetch bucket {bid}: {exc}", file=sys.stderr)
            continue
        for raw in raw_events:
            ev = normalize_event(raw, bid)
            if ev is not None:
                normalized.append(ev)

    deduped = deduplicate_events(normalized)
    filtered = filter_events(
        deduped,
        query=args.query,
        searches_only=args.searches,
        domain=args.domain,
        start_dt=start_dt,
        end_dt=end_dt,
    )

    if args.top_domains:
        rows = aggregate_top_domains(filtered, limit=args.limit)
        if args.as_json:
            print(json.dumps(rows, indent=2))
        else:
            print(format_text_domains(rows))
        return 0

    limited = filtered[: args.limit]
    if args.as_json:
        print(json.dumps([_serialize_event(ev) for ev in limited], indent=2))
    else:
        print(format_text_events(limited, searches_only=args.searches))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
