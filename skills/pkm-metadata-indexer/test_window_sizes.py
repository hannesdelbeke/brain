#!/usr/bin/env python3
"""Test different RERANK_MAX_CHARS settings."""

import os
import sys
import subprocess
import time
import urllib.request
import json

def restart_daemon():
    """Restart the searchd daemon."""
    print("Restarting daemon...")
    subprocess.run(
        ["launchctl", "kickstart", "-k", f"gui/{os.getuid()}/com.fortispkm.searchd"],
        capture_output=True
    )
    time.sleep(2)

    # Poll health until ready
    for _ in range(30):
        try:
            with urllib.request.urlopen("http://127.0.0.1:44771/health", timeout=5) as r:
                health = json.load(r)
                vaults = health.get("vaults", [])
                if len(vaults) == 4 and health.get("default_vault") == "fortis":
                    print(f"Daemon ready with {len(vaults)} vaults")
                    return True
        except Exception:
            pass
        time.sleep(1)

    print("ERROR: Daemon failed to start properly!")
    return False

def measure_config(max_chars_value):
    """Measure latency and precision for a given RERANK_MAX_CHARS value."""
    print(f"\n{'='*60}")
    print(f"Testing RERANK_MAX_CHARS = {max_chars_value}")
    print(f"{'='*60}")

    # Update the constant in index_pkm_meta.py
    import index_pkm_meta
    index_pkm_meta.RERANK_MAX_CHARS = max_chars_value

    # Restart daemon to pick up the change
    if not restart_daemon():
        return None

    # Measure latency
    print("\nRunning latency measurement...")
    result = subprocess.run(
        ["/Users/h/.venvs/pkm-indexer/bin/python",
         "/Users/h/Documents/GitHub/FortisPkm/public/skills/pkm-metadata-indexer/measure_latency.py"],
        capture_output=True,
        text=True
    )
    print(result.stdout)

    # Extract p50 with rerank
    for line in result.stdout.split('\n'):
        if 'with rerank:' in line and 'Overall p50' in result.stdout.split('\n')[result.stdout.split('\n').index(line)-1]:
            latency = int(line.split(':')[1].strip().replace('ms', ''))
            break
    else:
        latency = None

    # Measure precision
    print("\nRunning precision evaluation...")
    result = subprocess.run(
        ["/Users/h/.venvs/pkm-indexer/bin/python",
         "/Users/h/Documents/GitHub/FortisPkm/public/skills/pkm-metadata-indexer/eval_rerank.py",
         "--vault", "brain", "--port", "44771"],
        capture_output=True,
        text=True,
        timeout=300
    )
    print(result.stdout)

    # Extract precision@10 for rerank
    for line in result.stdout.split('\n'):
        if 'all      rerank' in line:
            # Parse "precision@10 66/140 = 47%"
            parts = line.split('precision@10')[1].split('=')
            precision_pct = float(parts[1].split('%')[0].strip())
            break
    else:
        precision_pct = None

    return {"latency_p50": latency, "precision@10": precision_pct}

if __name__ == "__main__":
    # Change to the script directory
    os.chdir("/Users/h/Documents/GitHub/FortisPkm/public/skills/pkm-metadata-indexer")

    results = {}
    for max_chars in [None, 1500, 768, 384]:
        label = "baseline (no truncation)" if max_chars is None else f"{max_chars} chars"
        results[label] = measure_config(max_chars)

    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    print(f"{'Config':<30} {'Latency (ms)':<15} {'Precision@10':<15}")
    print(f"{'-'*60}")
    for config, data in results.items():
        if data:
            print(f"{config:<30} {data['latency_p50']:<15} {data['precision@10']:<15}")
