"""Score the cross-encoder rerank against a blind judge.

The same questions are asked twice of the same corpus, once with `&rerank=1`
and once without, so the only difference between the two runs is the reorder.
For every section either run returns, a model that has seen only the question
and that section's text says whether the section is a useful answer. The judge
never learns which run produced the section, or at what rank, so it cannot
reward the reorder it is measuring.

    python searchd.py --vault brain=<vault> --port 44781
    python eval_rerank.py --vault brain --port 44781

Reports precision at k and the rank of the first useful section, per question,
split into the question that was already used while building the rerank and a
set written before any result was looked at. Judgements are cached in
~/.pkm/rerank-judgements.json, keyed by question and section, so a rerun costs
nothing for pairs already seen.

Env: GATEWAY (default http://127.0.0.1:8080), MODEL (default gemini-2.5-flash),
an OpenAI-shaped or Gemini-shaped local endpoint, whichever the machine runs.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import urlencode

GATEWAY = "http://127.0.0.1:8080"
MODEL = "gemini-2.5-flash"
JUDGEMENTS = Path.home() / ".pkm" / "rerank-judgements.json"
SECTION_CHARS = 3000

# Written before any result was looked at. `seen` marks the one question the
# rerank was tried on while it was being built, so its numbers are not evidence.
QUESTIONS = [
    ("how did we stop the laptop overheating", "seen"),
    ("what does retrieval cost as the vault grows", "holdout"),
    ("why not use a vector database for this", "holdout"),
    ("what did the audit find that the notes claimed but the code did not do", "holdout"),
    ("how are agent session transcripts turned into searchable documents", "holdout"),
    ("what does a link graph give you that grep cannot", "holdout"),
    ("how do you measure whether a ranking change helped", "holdout"),
    ("what happens when two copies of the same tool drift apart", "holdout"),
    ("how do i control the home battery charge mode", "holdout"),
    ("how would duplicate notes be caught before one is written", "holdout"),
    ("which obsidian features could be rebuilt on the index", "holdout"),
    ("how fast can this machine embed text locally", "holdout"),
    ("what does an agent pay in tokens for a search result", "holdout"),
    ("why keep the embedding model resident in memory", "holdout"),
]

JUDGE = """Someone searching their notes asks: "{question}"

Below is one section of one note, as the search returned it.

---
{section}
---

Would reading this section help answer the question, either because it answers
it or because it says where the answer is? Answer with one word, YES or NO."""


def post(url: str, payload: dict, timeout: int = 120) -> dict:
    request = urllib.request.Request(
        url, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.load(response)


def search(base: str, vault: str, question: str, limit: int, rerank: bool) -> list[dict]:
    params = {"vault": vault, "q": question, "limit": limit}
    if rerank:
        params["rerank"] = "1"
    with urllib.request.urlopen(f"{base}/search?" + urlencode(params), timeout=120) as response:
        return json.load(response)["results"]


def key(hit: dict) -> str:
    return f"{hit['path']}#{hit['line']}"


def section_text(cursor: sqlite3.Cursor, hit: dict) -> str:
    row = cursor.execute(
        "SELECT content FROM sections_fts JOIN sections ON sections.id = sections_fts.section_id "
        "WHERE sections.path = ? AND sections.start_line = ?",
        (hit["path"], hit["line"]),
    ).fetchone()
    return row[0] if row else (hit.get("snippet") or "")


def judge(question: str, text: str) -> bool | None:
    if not text.strip():
        return None
    payload = {
        "contents": [{"role": "user", "parts": [{"text": JUDGE.format(
            question=question, section=text[:SECTION_CHARS])}]}],
        "generationConfig": {"temperature": 0, "maxOutputTokens": 8,
                             "thinkingConfig": {"thinkingBudget": 0}},
    }
    try:
        data = post(f"{GATEWAY}/v1beta/models/{MODEL}:generateContent", payload)
    except (urllib.error.URLError, TimeoutError) as error:
        print(f"  judge failed: {error}", flush=True)
        return None
    parts = data.get("candidates", [{}])[0].get("content", {}).get("parts", [])
    answer = "".join(part.get("text", "") for part in parts).strip().upper()
    return answer.startswith("YES") if answer.startswith(("YES", "NO")) else None


def precision(hits: list[dict], verdicts: dict[str, bool | None]) -> tuple[int, int, int | None]:
    useful = [rank for rank, hit in enumerate(hits) if verdicts.get(key(hit))]
    return len(useful), len(hits), (useful[0] + 1 if useful else None)


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--vault", default="brain", help="Corpus the daemon serves")
    parser.add_argument("--port", type=int, default=44781)
    parser.add_argument("--db", default=None, help="Index to read section text from, "
                                                   "otherwise the daemon's own")
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--self-check", action="store_true")
    args = parser.parse_args()
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    if args.self_check:
        return self_check()

    base = f"http://127.0.0.1:{args.port}"
    db = args.db
    if not db:
        with urllib.request.urlopen(f"{base}/health", timeout=30) as response:
            health = json.load(response)
        db = next(v["db"] for v in health["vaults"] if v["name"] == args.vault)
    cursor = sqlite3.connect(db).cursor()

    JUDGEMENTS.parent.mkdir(parents=True, exist_ok=True)
    cached = json.loads(JUDGEMENTS.read_text(encoding="utf-8")) if JUDGEMENTS.exists() else {}
    rows = []

    for question, group in QUESTIONS:
        arms = {name: search(base, args.vault, question, args.limit, name == "rerank")
                for name in ("fused", "rerank")}
        seen: dict[str, dict] = {}
        for hit in arms["fused"] + arms["rerank"]:
            seen.setdefault(key(hit), hit)
        need = [hit for identity, hit in seen.items() if f"{question}|{identity}" not in cached]

        with ThreadPoolExecutor(max_workers=8) as pool:
            texts = [section_text(cursor, hit) for hit in need]  # sqlite is single threaded
            for hit, verdict in zip(need, pool.map(lambda pair: judge(*pair),
                                                   [(question, text) for text in texts])):
                cached[f"{question}|{key(hit)}"] = verdict
        JUDGEMENTS.write_text(json.dumps(cached, indent=1, sort_keys=True), encoding="utf-8")

        verdicts = {identity: cached.get(f"{question}|{identity}") for identity in seen}
        row = {"question": question, "group": group}
        for name, hits in arms.items():
            row[name] = precision(hits, verdicts)
        rows.append(row)
        fused, rerank = row["fused"], row["rerank"]
        print(f"[{group}] {question}\n    fused:  {fused[0]}/{fused[1]} useful, first at {fused[2]}"
              f"\n    rerank: {rerank[0]}/{rerank[1]} useful, first at {rerank[2]}", flush=True)

    print()
    for group in ("seen", "holdout", None):
        subset = [row for row in rows if group is None or row["group"] == group]
        for name in ("fused", "rerank"):
            good = sum(row[name][0] for row in subset)
            total = sum(row[name][1] for row in subset)
            firsts = [row[name][2] for row in subset if row[name][2]]
            mean = f"{sum(firsts) / len(firsts):.1f}" if firsts else "none"
            print(f"{group or 'all':8} {name:7} precision@{args.limit} {good}/{total} "
                  f"= {good / total:.0%}   answered {len(firsts)}/{len(subset)}"
                  f"   mean first useful rank {mean}", flush=True)


def self_check():
    verdicts = {"a.md#1": True, "b.md#2": None, "c.md#3": False, "d.md#4": True}
    hits = [{"path": name.split("#")[0], "line": int(name.split("#")[1])}
            for name in ("c.md#3", "b.md#2", "a.md#1", "d.md#4")]
    assert precision(hits, verdicts) == (2, 4, 3)
    assert precision(hits[:1], verdicts) == (0, 1, None)
    assert key({"path": "a.md", "line": 7}) == "a.md#7"
    assert [group for _, group in QUESTIONS].count("seen") == 1
    print("self-check ok")


if __name__ == "__main__":
    main()
