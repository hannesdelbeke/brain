#!/usr/bin/env python3
"""Test cold vs warm search latency by timing internal phases."""

import time
import urllib.request
import urllib.parse
import json

SEARCHD_URL = "http://127.0.0.1:44771"

def search(query: str, vault: str = "fortis") -> dict:
    """Call the searchd /search endpoint."""
    params = urllib.parse.urlencode({"q": query, "vault": vault, "limit": 5, "rerank": 0, "reindex": 0})
    url = f"{SEARCHD_URL}/search?{params}"
    began = time.perf_counter()
    with urllib.request.urlopen(url, timeout=2.0) as response:
        result = json.load(response)
    took = (time.perf_counter() - began) * 1000
    return {"wall_ms": took, "server_ms": result.get("took_ms"), "result": result}

def main():
    # Do two back-to-back searches (warm)
    print("=== WARM (back-to-back) ===")
    for i in range(2):
        result = search("test query warm")
        print(f"  Call {i+1}: wall={result['wall_ms']:.1f}ms, server={result['server_ms']:.1f}ms")

    # Wait 15 seconds
    print("\n=== WAITING 15 seconds ===")
    time.sleep(15)

    # Do a cold search
    print("\n=== COLD (after 15s idle) ===")
    result = search("test query cold")
    print(f"  wall={result['wall_ms']:.1f}ms, server={result['server_ms']:.1f}ms")

    # Immediately do another search (should be warm again)
    print("\n=== WARM (immediately after) ===")
    result = search("test query warm again")
    print(f"  wall={result['wall_ms']:.1f}ms, server={result['server_ms']:.1f}ms")

if __name__ == "__main__":
    main()
