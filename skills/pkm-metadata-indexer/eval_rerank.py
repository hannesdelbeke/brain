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
import os
import re
import sqlite3
import sys
import urllib.error
import urllib.request
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import urlencode

GATEWAY = os.environ.get("GATEWAY", "http://127.0.0.1:8080")
MODEL = os.environ.get("MODEL", "gemini-2.5-flash")
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

# `--withhold-private` keeps a section on this machine rather than sending it to
# the judge. Both runs are scored over the same withheld set, so the comparison
# stays fair; what it costs is that a withheld section counts as not useful, so
# the absolute precision reads low and the judged-only column is the honest one.
PRIVATE = {
    "home path": r"C:\\Users\\|C:/Users/|/home/[a-z]",
    "credential": r"(?i)\b(api[_ -]?key|password|passphrase|client[_ -]?secret|private[_ -]?key)\b"
                  r"|\b(sk-[A-Za-z0-9]{10,}|ghp_[A-Za-z0-9]{10,}|xox[bpsa]-[A-Za-z0-9-]{10,}"
                  r"|AIza[A-Za-z0-9_\-]{10,}|glpat-[A-Za-z0-9_\-]{10,})",
    "network": r"\b(192\.168\.\d{1,3}\.\d{1,3}|10\.\d{1,3}\.\d{1,3}\.\d{1,3}"
               r"|172\.(1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3})\b|\b([0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2}\b",
    "personal identity": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b|\b\+\d{6,}\b",
    "house": r"(?i)\b(home ?assistant|solarsynk|inverter|thermostat|ssid|smart ?plug)\b",
    "health or money": r"(?i)\b(salary|invoice|iban|medical|doctor|prescription|mortgage)\w*\b",
}

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


def judge_request(model: str, prompt: str) -> tuple[str, dict]:
    """URL and body for one judgement, in whichever dialect the model speaks.

    Gemini-shaped when the model name says gemini, OpenAI-shaped otherwise. The
    docstring always promised both; only the Gemini half existed, so a gateway
    serving `/v1/chat/completions` and `/v1/messages` and no `/v1beta` route —
    which is what the vault-b one serves — could not run this at all.
    """
    if model.startswith("gemini"):
        return f"{GATEWAY}/v1beta/models/{model}:generateContent", {
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0, "maxOutputTokens": 8,
                                 "thinkingConfig": {"thinkingBudget": 0}},
        }
    return f"{GATEWAY}/v1/chat/completions", {
        "model": model, "max_tokens": 8, "temperature": 0,
        "messages": [{"role": "user", "content": prompt}],
    }


def judge_answer(model: str, data: dict) -> str:
    """The reply text out of either dialect's response envelope."""
    if model.startswith("gemini"):
        parts = data.get("candidates", [{}])[0].get("content", {}).get("parts", [])
        return "".join(part.get("text", "") for part in parts)
    choices = data.get("choices") or [{}]
    return choices[0].get("message", {}).get("content") or ""


def judge(question: str, text: str) -> bool | None:
    if not text.strip():
        return None
    url, payload = judge_request(
        MODEL, JUDGE.format(question=question, section=text[:SECTION_CHARS]))
    try:
        data = post(url, payload)
    except (urllib.error.URLError, TimeoutError) as error:
        print(f"  judge failed: {error}", flush=True)
        return None
    answer = judge_answer(MODEL, data).strip().upper()
    return answer.startswith("YES") if answer.startswith(("YES", "NO")) else None


def private(text: str) -> list[str]:
    return [name for name, pattern in PRIVATE.items() if re.search(pattern, text)]


def precision(hits: list[dict], verdicts: dict[str, bool | None]) -> tuple[int, int, int | None, int]:
    useful = [rank for rank, hit in enumerate(hits) if verdicts.get(key(hit))]
    judged = sum(1 for hit in hits if verdicts.get(key(hit)) is not None)
    return len(useful), len(hits), (useful[0] + 1 if useful else None), judged


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--vault", default="brain", help="Corpus the daemon serves")
    parser.add_argument("--port", type=int, default=44781)
    parser.add_argument("--db", default=None, help="Index to read section text from, "
                                                   "otherwise the daemon's own")
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--withhold-private", action="store_true",
                        help="Never send a section matching PRIVATE to the judge. It counts as "
                             "not useful in both runs and is reported as withheld")
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
    withheld: Counter[str] = Counter()
    rows = []

    for question, group in QUESTIONS:
        arms = {name: search(base, args.vault, question, args.limit, name == "rerank")
                for name in ("fused", "rerank")}
        seen: dict[str, dict] = {}
        for hit in arms["fused"] + arms["rerank"]:
            seen.setdefault(key(hit), hit)
        need = [hit for identity, hit in seen.items() if f"{question}|{identity}" not in cached]
        texts = [section_text(cursor, hit) for hit in need]  # sqlite is single threaded
        if args.withhold_private:
            flagged = [private(text) for text in texts]
            for names in flagged:
                if names:
                    withheld["sections"] += 1
                    withheld.update(names)
            need = [hit for hit, names in zip(need, flagged) if not names]
            texts = [text for text, names in zip(texts, flagged) if not names]

        with ThreadPoolExecutor(max_workers=8) as pool:
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
        print(f"[{group}] {question}"
              f"\n    fused:  {fused[0]}/{fused[1]} useful, first at {fused[2]}, {fused[3]} judged"
              f"\n    rerank: {rerank[0]}/{rerank[1]} useful, first at {rerank[2]}, "
              f"{rerank[3]} judged", flush=True)

    print()
    for group in ("seen", "holdout", None):
        subset = [row for row in rows if group is None or row["group"] == group]
        for name in ("fused", "rerank"):
            good = sum(row[name][0] for row in subset)
            total = sum(row[name][1] for row in subset)
            judged = sum(row[name][3] for row in subset)
            firsts = [row[name][2] for row in subset if row[name][2]]
            mean = f"{sum(firsts) / len(firsts):.1f}" if firsts else "none"
            print(f"{group or 'all':8} {name:7} precision@{args.limit} {good}/{total} "
                  f"= {good / total:.0%}   over judged only {good}/{judged}"
                  f" = {good / judged:.0%}" if judged else "   nothing judged", flush=True)
            print(f"{'':17} answered {len(firsts)}/{len(subset)}"
                  f"   mean first useful rank {mean}", flush=True)
    if withheld:
        print("\nwithheld from the judge: "
              + ", ".join(f"{count} {name}" for name, count in withheld.most_common()), flush=True)


def self_check():
    verdicts = {"a.md#1": True, "b.md#2": None, "c.md#3": False, "d.md#4": True}
    hits = [{"path": name.split("#")[0], "line": int(name.split("#")[1])}
            for name in ("c.md#3", "b.md#2", "a.md#1", "d.md#4")]
    assert precision(hits, verdicts) == (2, 4, 3, 3)
    assert precision(hits[:1], verdicts) == (0, 1, None, 1)
    assert key({"path": "a.md", "line": 7}) == "a.md#7"
    assert private(r"ran it in C:\Users\someone\vault") == ["home path"]
    assert private("the solarsynk inverter mode") == ["house"]
    assert private("a section about reciprocal rank fusion") == []
    assert [group for _, group in QUESTIONS].count("seen") == 1

    url, payload = judge_request("gemini-2.5-flash", "q")
    assert url.endswith("/v1beta/models/gemini-2.5-flash:generateContent"), url
    assert payload["contents"][0]["parts"][0]["text"] == "q"
    assert judge_answer("gemini-2.5-flash",
                        {"candidates": [{"content": {"parts": [{"text": "YES"}]}}]}) == "YES"

    url, payload = judge_request("claude-haiku-4-5-20251001", "q")
    assert url.endswith("/v1/chat/completions"), url
    assert payload["messages"][0]["content"] == "q"
    assert judge_answer("claude-haiku-4-5-20251001",
                        {"choices": [{"message": {"content": "NO"}}]}) == "NO"
    assert judge_answer("claude-haiku-4-5-20251001", {}) == ""
    print("self-check ok")


if __name__ == "__main__":
    main()
