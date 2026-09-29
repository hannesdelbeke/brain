#!/usr/bin/env python3
"""Quick interleaved comparison of pool=20 vs pool=12 reranking."""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import index_pkm_meta

QUERIES = [
    "how do I configure the search daemon indexing schedule",
    "what are the best practices for writing automation triggers",
    "explain the difference between semantic and keyword search",
    "how does the cross encoder reranking actually work here",
    "what files contain the git commit scanning implementation",
]

def measure_pool(pool_size: int, trials: int = 6) -> list[float]:
    """Measure search latency with given pool size, discard first trial."""
    old_value = index_pkm_meta.RERANK_CANDIDATES
    index_pkm_meta.RERANK_CANDIDATES = pool_size

    times = []
    for query in QUERIES:
        for _ in range(trials):
            start = time.perf_counter()
            index_pkm_meta.search_index(
                query=query,
                limit=10,
                rerank=True,
                vault_path="/Users/h/Documents/GitHub/FortisPkm/public"
            )
            elapsed = (time.perf_counter() - start) * 1000
            times.append(elapsed)

    index_pkm_meta.RERANK_CANDIDATES = old_value
    # Discard first trial per query (5 warmups total)
    filtered = [times[i] for i in range(len(times)) if i % trials != 0]
    return sorted(filtered)

# Interleaved measurement
print("Measuring pool=20...")
times_20 = measure_pool(20)
print("Measuring pool=12...")
times_12 = measure_pool(12)

median_20 = times_20[len(times_20) // 2]
median_12 = times_12[len(times_12) // 2]
ratio = median_20 / median_12

print(f"\nPool=20: p50={median_20:.1f}ms")
print(f"Pool=12: p50={median_12:.1f}ms")
print(f"Ratio: {ratio:.2f}x (pool=20 / pool=12)")
