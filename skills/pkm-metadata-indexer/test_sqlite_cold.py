#!/usr/bin/env python3
"""Test if SQLite PRAGMA data_version query goes cold after idle."""

import time
import sqlite3
from pathlib import Path

DB_PATH = "/Users/h/Documents/GitHub/FortisPkm/.obsidian/pkm_index.db"

def test_pragma_cold():
    print("Opening persistent connection...")
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True, check_same_thread=False)

    # Warm runs
    print("\n=== WARM RUNS (back-to-back) ===")
    for i in range(3):
        t0 = time.perf_counter()
        cursor = conn.cursor()
        version = cursor.execute("PRAGMA data_version").fetchone()[0]
        took_ms = (time.perf_counter() - t0) * 1000
        print(f"  Run {i+1}: {took_ms:.3f}ms (version={version})")

    # Wait
    print("\n=== WAITING 15 seconds ===")
    time.sleep(15)

    # Cold run
    print("\n=== COLD RUN (after 15s idle) ===")
    t0 = time.perf_counter()
    cursor = conn.cursor()
    version = cursor.execute("PRAGMA data_version").fetchone()[0]
    took_ms = (time.perf_counter() - t0) * 1000
    print(f"  {took_ms:.3f}ms (version={version})")

    # Immediate warm run
    print("\n=== WARM RUN (immediately after) ===")
    t0 = time.perf_counter()
    cursor = conn.cursor()
    version = cursor.execute("PRAGMA data_version").fetchone()[0]
    took_ms = (time.perf_counter() - t0) * 1000
    print(f"  {took_ms:.3f}ms (version={version})")

    conn.close()

if __name__ == "__main__":
    test_pragma_cold()
