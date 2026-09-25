#!/usr/bin/env python
"""Measure whether a fact in the vault is retrievable by its symptom, not just its answer.

Every probe carries two phrasings of one fact. `symptom` is what a caller has at
the moment it hits the problem -- an error string, a surprising behaviour. `answer`
is the phrasing it could only produce if it already knew the fix. A vault that
scores well on the second and badly on the first holds the knowledge and cannot
deliver it, which is the failure this measures: the only query that retrieves is
the one nobody can type yet.

Runs offline against the index database, so it needs no daemon and cannot disturb
one. Probes live outside this repo, because a symptom is usually a private error
string; pass the set with --probes.

usage:
    python symptom_recall.py --probes /path/to/probes.json --tag baseline
    env PKM_QUERY_INSTRUCTION= python symptom_recall.py --probes ... --tag no-prefix
"""
from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import index_pkm_meta as pkm  # noqa: E402


def rank_of(results, expect):
    """1-based rank of the first result whose path matches any expected substring."""
    pats = [e.lower() for e in expect]
    for position, row in enumerate(results, 1):
        path = str(row.get("path", "")).lower()
        if any(e in path for e in pats):
            return position, row
    return None, None


def run_query(query, vault, db, limit, vectors, rerank):
    t0 = time.time()
    results = pkm.search_index(query, vault_path=vault, db_path=db, limit=limit,
                               vectors=vectors, rerank=rerank)
    return results, (time.time() - t0) * 1000.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--probes", required=True)
    # No default: the corpus under test is the caller's, and naming one here put
    # a private vault path in a public repo.
    ap.add_argument("--vault", required=True, help="vault root whose index to search")
    ap.add_argument("--db", default=None)
    ap.add_argument("--limit", type=int, default=10)
    ap.add_argument("--tag", required=True)
    ap.add_argument("--no-rerank", action="store_true")
    ap.add_argument("--outdir", default=None)
    ap.add_argument("--show", action="store_true", help="print top-3 paths for each symptom miss")
    args = ap.parse_args()

    probes = json.load(open(args.probes))["probes"]
    db = args.db or str(pkm.default_db_path(Path(args.vault)))
    rerank = not args.no_rerank

    # Load the matrix once. Per-query loading dominates the measurement otherwise
    # and would make a ranking change look like a latency change.
    connection = sqlite3.connect(db, timeout=60.0)
    vectors = pkm.load_vectors(connection.cursor())
    connection.close()

    instruction = pkm.QUERY_INSTRUCTION
    print("tag=%s  rerank=%s  limit=%s" % (args.tag, rerank, args.limit))
    print("query instruction=%r" % instruction)
    print("db=%s\n" % db)

    rows = []
    for probe in probes:
        s_res, s_ms = run_query(probe["symptom"], args.vault, db, args.limit, vectors, rerank)
        a_res, a_ms = run_query(probe["answer"], args.vault, db, args.limit, vectors, rerank)
        s_rank, s_row = rank_of(s_res, probe["expect"])
        a_rank, a_row = rank_of(a_res, probe["expect"])
        row = {
            "id": probe["id"],
            "symptom_rank": s_rank,
            "answer_rank": a_rank,
            "symptom_logit": s_row.get("rerank_score") if s_row else None,
            "answer_logit": a_row.get("rerank_score") if a_row else None,
            "symptom_top_logit": s_res[0].get("rerank_score") if s_res else None,
            "symptom_ms": round(s_ms),
            "symptom_top3": [r.get("path") for r in s_res[:3]],
        }
        rows.append(row)
        lg = row["symptom_logit"]
        print("%-4s %-18s symptom=%-4s answer=%-4s hit_logit=%s" % (
            "OK " if s_rank else "MISS", probe["id"],
            s_rank or "-", a_rank or "-",
            ("%+.2f" % lg) if lg is not None else "-"))
        if args.show and not s_rank:
            for p in row["symptom_top3"]:
                print("        got: %s" % p)

    n = len(rows)

    def pct(key, k):
        return round(100.0 * sum(1 for r in rows if r[key] and r[key] <= k) / n, 1)

    summary = {
        "tag": args.tag,
        "n": n,
        "instruction": instruction,
        "rerank": rerank,
        "symptom_hit@1": pct("symptom_rank", 1),
        "symptom_hit@3": pct("symptom_rank", 3),
        "symptom_hit@5": pct("symptom_rank", 5),
        "symptom_hit@10": pct("symptom_rank", 10),
        "answer_hit@5": pct("answer_rank", 5),
        "answer_hit@10": pct("answer_rank", 10),
        "median_ms": sorted(r["symptom_ms"] for r in rows)[n // 2],
    }
    # A hit the guard would discard is a hit the caller never sees, so the logit
    # distribution of correct sections is the number that sets the cutoff.
    hit_logits = sorted(r["symptom_logit"] for r in rows if r["symptom_logit"] is not None)
    summary["symptom_hit_logits"] = [round(v, 2) for v in hit_logits]
    summary["hits_above_zero"] = sum(1 for v in hit_logits if v > 0)
    summary["hits_total"] = len(hit_logits)

    print("\n=== %s (n=%d) ===" % (args.tag, n))
    for k in ("symptom_hit@1", "symptom_hit@3", "symptom_hit@5", "symptom_hit@10",
              "answer_hit@5", "answer_hit@10", "median_ms"):
        print("  %-16s %s" % (k, summary[k]))
    print("  %-16s %d of %d correct sections score above ANSWER_LOGIT=0" % (
        "guard survival", summary["hits_above_zero"], summary["hits_total"]))
    print("  %-16s %s" % ("hit logits", summary["symptom_hit_logits"]))

    outdir = Path(args.outdir or (Path.home() / ".pkm" / "symptom-recall"))
    outdir.mkdir(parents=True, exist_ok=True)
    out = outdir / (args.tag + ".json")
    json.dump({"summary": summary, "rows": rows}, open(out, "w"), indent=2)
    print("\nwrote %s" % out)


if __name__ == "__main__":
    main()
