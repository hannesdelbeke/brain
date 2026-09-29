#!/usr/bin/env python3
"""Test if SQLite cursor creation on persistent connection goes cold."""

import time
import sqlite3

DB_PATH = "/Users/h/Documents/GitHub/FortisPkm/.obsidian/pkm_index.db"

def test_cursor_cold():
    print("Opening persistent connection...")
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True, check_same_thread=False)

    # Warm runs
    print("\n=== WARM RUNS (back-to-back) ===")
    for i in range(3):
        t0 = time.perf_counter()
        cursor = conn.cursor()
        version = cursor.execute("PRAGMA data_version").fetchone()[0]
        took_ms = (time.perf_counter() - t0) * 1000
        print(f"  Run {i+1}: {took_ms:.3f}ms")

    # Wait
    print("\n=== WAITING 15 seconds ===")
    time.sleep(15)

    # Cold run - test cursor creation separately
    print("\n=== COLD RUN (cursor creation) ===")
    t0 = time.perf_counter()
    cursor = conn.cursor()
    cursor_ms = (time.perf_counter() - t0) * 1000
    print(f"  cursor(): {cursor_ms:.3f}ms")

    t0 = time.perf_counter()
    version = cursor.execute("PRAGMA data_version").fetchone()[0]
    pragma_ms = (time.perf_counter() - t0) * 1000
    print(f"  PRAGMA:   {pragma_ms:.3f}ms")
    print(f"  Total:    {cursor_ms + pragma_ms:.3f}ms")

    # Immediate warm run
    print("\n=== WARM RUN (immediately after) ===")
    t0 = time.perf_counter()
    cursor = conn.cursor()
    version = cursor.execute("PRAGMA data_version").fetchone()[0]
    took_ms = (time.perf_counter() - t0) * 1000
    print(f"  {took_ms:.3f}ms")

    conn.close()

if __name__ == "__main__":
    test_cursor_cold()
