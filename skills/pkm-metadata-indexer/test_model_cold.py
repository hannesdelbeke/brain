#!/usr/bin/env python3
"""Test if the embedding model goes cold after idle."""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import index_pkm_meta as pkm

def test_model_cold():
    print("Getting embedding model...")
    model = pkm.get_embedding_model(pkm.QUERY_PROVIDERS, pkm.QUERY_THREADS)

    # Warm runs
    print("\n=== WARM RUNS (back-to-back) ===")
    for i in range(3):
        t0 = time.perf_counter()
        vec = list(model.embed(["test query"]))
        took_ms = (time.perf_counter() - t0) * 1000
        print(f"  Run {i+1}: {took_ms:.1f}ms")

    # Wait
    print("\n=== WAITING 15 seconds ===")
    time.sleep(15)

    # Cold run
    print("\n=== COLD RUN (after 15s idle) ===")
    t0 = time.perf_counter()
    vec = list(model.embed(["test query cold"]))
    took_ms = (time.perf_counter() - t0) * 1000
    print(f"  {took_ms:.1f}ms")

    # Immediate warm run
    print("\n=== WARM RUN (immediately after) ===")
    t0 = time.perf_counter()
    vec = list(model.embed(["test query warm"]))
    took_ms = (time.perf_counter() - t0) * 1000
    print(f"  {took_ms:.1f}ms")

    # Now test with keepalive simulation
    print("\n=== TESTING WITH SIMULATED KEEPALIVE ===")
    print("Encoding every 250ms for 10 seconds...")

    import threading
    stop_event = threading.Event()

    def keepalive_thread():
        while not stop_event.is_set():
            list(model.embed(["."])  )
            time.sleep(0.25)

    thread = threading.Thread(target=keepalive_thread, daemon=True)
    thread.start()

    time.sleep(10)

    print("\n=== AFTER 10s WITH KEEPALIVE ===")
    t0 = time.perf_counter()
    vec = list(model.embed(["test query with keepalive"]))
    took_ms = (time.perf_counter() - t0) * 1000
    print(f"  {took_ms:.1f}ms")

    stop_event.set()
    thread.join(timeout=1)

if __name__ == "__main__":
    test_model_cold()
