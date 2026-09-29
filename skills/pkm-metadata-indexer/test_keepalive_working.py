#!/usr/bin/env python3
"""Test if the daemon's keepalive is actually preventing the model from going cold."""

import time
import urllib.request
import urllib.parse
import json

SEARCHD_URL = "http://127.0.0.1:44771"

def search(query: str) -> float:
    """Call searchd and return server-reported took_ms."""
    params = urllib.parse.urlencode({"q": query, "vault": "fortis", "limit": 5, "rerank": 0, "reindex": 0, "expand": 0})
    url = f"{SEARCHD_URL}/search?{params}"
    with urllib.request.urlopen(url, timeout=2.0) as response:
        result = json.load(response)
    return result.get("took_ms", 0)

def main():
    # Baseline warm
    print("=== BASELINE (back-to-back) ===")
    took1 = search("baseline 1")
    took2 = search("baseline 2")
    print(f"  Call 1: {took1:.1f}ms")
    print(f"  Call 2: {took2:.1f}ms")

    # If keepalive is working, query should stay warm after 5s, 10s, 15s
    for wait_s in [5, 10, 15, 20]:
        print(f"\n=== AFTER {wait_s}s IDLE ===")
        time.sleep(wait_s)
        took = search(f"query after {wait_s}s")
        print(f"  {took:.1f}ms")

        # Immediate follow-up to confirm it's warm again
        took_after = search(f"immediately after {wait_s}s test")
        print(f"  Immediate follow-up: {took_after:.1f}ms")

    print("\n=== ANALYSIS ===")
    print("If keepalive is working:")
    print("  - All queries should be ~25-35ms")
    print("If keepalive is NOT working:")
    print("  - After 10s+: first query ~250-350ms, second query ~25-35ms")
    print("  - After 5s: both queries ~25-35ms (model hasn't gone cold yet)")

if __name__ == "__main__":
    main()
