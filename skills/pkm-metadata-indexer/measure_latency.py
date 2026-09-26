#!/usr/bin/env python3
"""Measure search latency with and without rerank."""

import json
import time
import urllib.request
from urllib.parse import urlencode
from statistics import median

BASE_URL = "http://127.0.0.1:44771"
VAULT = "brain"

# Long natural language questions (>8 tokens)
QUESTIONS = [
    "how did we stop the laptop overheating",
    "what does retrieval cost as the vault grows",
    "why not use a vector database for this",
    "what did the audit find that the notes claimed but the code did not do",
    "how are agent session transcripts turned into searchable documents",
]

def search(query: str, rerank: bool = False, expand: bool = False) -> tuple[dict, float]:
    params = {"vault": VAULT, "q": query, "limit": 8, "expand": "0" if not expand else "1"}
    if rerank:
        params["rerank"] = "1"

    url = f"{BASE_URL}/search?" + urlencode(params)
    start = time.perf_counter()
    with urllib.request.urlopen(url, timeout=120) as response:
        data = json.load(response)
    elapsed = (time.perf_counter() - start) * 1000  # Convert to ms
    return data, elapsed

def main():
    # Warm up
    print("Warming up daemon...")
    for q in QUESTIONS[:1]:
        search(q, rerank=False)
        search(q, rerank=True)

    print("\nMeasuring latency (5 trials per question)...")
    without_rerank = []
    with_rerank = []

    for q in QUESTIONS:
        print(f"\nQuestion: {q}")
        q_without = []
        q_with = []

        for trial in range(5):
            _, latency = search(q, rerank=False)
            q_without.append(latency)
            time.sleep(0.1)

            _, latency = search(q, rerank=True)
            q_with.append(latency)
            time.sleep(0.1)

        print(f"  without rerank: {median(q_without):.0f}ms (trials: {[f'{x:.0f}' for x in q_without]})")
        print(f"  with rerank:    {median(q_with):.0f}ms (trials: {[f'{x:.0f}' for x in q_with]})")

        without_rerank.extend(q_without)
        with_rerank.extend(q_with)

    print(f"\n{'='*60}")
    print(f"Overall p50:")
    print(f"  without rerank: {median(without_rerank):.0f}ms")
    print(f"  with rerank:    {median(with_rerank):.0f}ms")
    print(f"  rerank overhead: +{median(with_rerank) - median(without_rerank):.0f}ms")

if __name__ == "__main__":
    main()
