"""Score co_commit's and /similar's neighbours against a blind judge.

The core claim behind co_commit.py is that it finds real relationships pure
vector search misses. This is the test: for a sample of notes with the most
co-commit edges, both `/co-commits` and `/similar` are asked for neighbours.
A model that has only seen the two note titles and a short excerpt of each
says whether the pair is genuinely related, never learning which signal
proposed it, so it cannot reward one source over the other.

    python searchd.py --vault brain=<vault> --port 44781
    python co_commit.py --vault-dir <vault> --vault brain --rebuild
    python eval_related.py --vault brain --vault-dir <vault> --port 44781

Reports precision for co-commit-only, vector-only and both-agree candidates,
plus what fraction of co-commit neighbours vector search would have missed
entirely (the number that matters: if it is near 0, co-commit is redundant
with what /similar already finds; if it is near 1, it is a distinct signal,
whether or not that signal is any good). Judgements cache in
~/.pkm/related-judgements.json.

Anchors are chosen at runtime as the notes with the most co-commit edges,
excluding hubs (same rule as co_commit.py --exclude-hubs) so the sample
is not just index files. Hardcoding a fixed note list, the way
eval_rerank.py does for its questions, does not work here: unlike a
question, an anchor note may not exist in every vault or may be deleted
between runs, and picking real edges from the vault under test is the
straightforward alternative.

Env: GATEWAY (default http://127.0.0.1:8080), MODEL (default gemini-2.5-flash)
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import urlencode

sys.path.insert(0, str(Path(__file__).resolve().parent))

import co_commit
from eval_rerank import GATEWAY, MODEL, post, private, PRIVATE  # noqa: F401 (PRIVATE for callers)

JUDGEMENTS = Path.home() / ".pkm" / "related-judgements.json"
EXCERPT_CHARS = 800

JUDGE = """Two notes from the same personal knowledge vault.

Note A, titled "{a_title}":
---
{a_text}
---

Note B, titled "{b_title}":
---
{b_text}
---

Are these genuinely related in subject or theme, such that someone reading
one would want to see the other? Answer with one word, YES or NO."""


def anchor_notes(db_path: Path, vault: str, count: int, hub_degree: int) -> list[str]:
    """Notes with the most co-commit edges, hubs excluded, for a representative sample."""
    connection = co_commit.connect(db_path)
    try:
        clause = "WHERE vault = ?" if vault else ""
        params = (vault,) if vault else ()
        rows = connection.execute(
            f"""
            SELECT note, COUNT(*) AS degree FROM (
                SELECT note_a AS note FROM co_commits {clause}
                UNION ALL
                SELECT note_b AS note FROM co_commits {clause}
            )
            GROUP BY note ORDER BY degree DESC
            """,
            params + params,
        ).fetchall()
    finally:
        connection.close()
    hubs = co_commit.hub_notes(db_path, vault, hub_degree)
    return [note for note, _ in rows if note not in hubs][:count]


def excerpt(vault_dir: Path, path: str) -> str:
    full = vault_dir / path
    if not full.exists():
        return ""
    return full.read_text(encoding="utf-8", errors="replace")[:EXCERPT_CHARS]


def title(path: str) -> str:
    return Path(path).stem


def fetch_similar(base: str, vault: str, note: str, limit: int) -> list[str]:
    params = urlencode({"note": note, "vault": vault, "limit": limit})
    try:
        with urllib.request.urlopen(f"{base}/similar?{params}", timeout=30) as response:
            body = json.load(response)
    except (urllib.error.URLError, TimeoutError) as error:
        print(f"  /similar failed for {note}: {error}", flush=True)
        return []
    return [row["path"] for row in body.get("results", [])]


def judge(a_path: str, a_text: str, b_path: str, b_text: str) -> bool | None:
    if not a_text.strip() or not b_text.strip():
        return None
    payload = {
        "contents": [{"role": "user", "parts": [{"text": JUDGE.format(
            a_title=title(a_path), a_text=a_text, b_title=title(b_path), b_text=b_text)}]}],
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


def pair_key(a: str, b: str) -> str:
    return f"{min(a, b)}|{max(a, b)}"


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--vault", default="brain", help="Corpus the daemon serves")
    parser.add_argument("--vault-dir", help="Path to read note excerpts from, required unless --self-check")
    parser.add_argument("--port", type=int, default=44781)
    parser.add_argument("--db", type=Path, default=co_commit.DEFAULT_DB)
    parser.add_argument("--anchors", type=int, default=8, help="Notes to sample")
    parser.add_argument("--limit", type=int, default=5, help="Neighbours per side, per anchor")
    parser.add_argument("--hub-degree", type=int, default=20)
    parser.add_argument("--withhold-private", action="store_true",
                        help="Never send an excerpt matching eval_rerank.PRIVATE to the judge")
    parser.add_argument("--self-check", action="store_true")
    args = parser.parse_args()
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    if args.self_check:
        return self_check()
    if not args.vault_dir:
        parser.error("--vault-dir is required unless --self-check")

    vault_dir = Path(args.vault_dir).resolve()
    base = f"http://127.0.0.1:{args.port}"
    anchors = anchor_notes(args.db, args.vault, args.anchors, args.hub_degree)
    if not anchors:
        print(f"no co-commit edges for vault {args.vault!r} in {args.db}. "
              f"run co_commit.py --rebuild first.")
        return

    JUDGEMENTS.parent.mkdir(parents=True, exist_ok=True)
    cached = json.loads(JUDGEMENTS.read_text(encoding="utf-8")) if JUDGEMENTS.exists() else {}
    withheld = 0
    totals = {"co_commit": [0, 0], "vector": [0, 0], "both": [0, 0]}
    co_commit_only_paths = set()
    vector_paths_total = 0

    for anchor in anchors:
        co_rows = co_commit.query_associations(args.db, anchor, args.vault, args.limit,
                                               exclude_hubs=True, hub_degree=args.hub_degree)
        co_neighbors = [row[1] for row in co_rows]
        vec_neighbors = fetch_similar(base, args.vault, anchor, args.limit)
        vector_paths_total += len(vec_neighbors)
        co_set, vec_set = set(co_neighbors), set(vec_neighbors)
        co_commit_only_paths |= (co_set - vec_set)

        anchor_text = excerpt(vault_dir, anchor)
        pairs_to_judge, sources = [], {}
        for candidate in co_set | vec_set:
            source = "both" if candidate in co_set and candidate in vec_set else \
                     ("co_commit" if candidate in co_set else "vector")
            sources[candidate] = source
            key = pair_key(anchor, candidate)
            if key in cached:
                continue
            candidate_text = excerpt(vault_dir, candidate)
            if args.withhold_private and (private(anchor_text) or private(candidate_text)):
                withheld += 1
                cached[key] = None
                continue
            pairs_to_judge.append((candidate, anchor_text, candidate_text))

        with ThreadPoolExecutor(max_workers=8) as pool:
            verdicts = pool.map(
                lambda item: judge(anchor, item[1], item[0], item[2]), pairs_to_judge)
        for (candidate, _, _), verdict in zip(pairs_to_judge, verdicts):
            cached[pair_key(anchor, candidate)] = verdict
        JUDGEMENTS.write_text(json.dumps(cached, indent=1, sort_keys=True), encoding="utf-8")

        for candidate in co_set | vec_set:
            verdict = cached.get(pair_key(anchor, candidate))
            if verdict is None:
                continue
            bucket = totals[sources[candidate]]
            bucket[1] += 1
            bucket[0] += int(verdict)
        print(f"{anchor}: {len(co_set)} co-commit, {len(vec_set)} vector, "
              f"{len(co_set & vec_set)} overlap", flush=True)

    print()
    for name, (good, judged) in totals.items():
        rate = f"{good}/{judged} = {good / judged:.0%}" if judged else "nothing judged"
        print(f"{name:10} precision {rate}")
    print(f"\nco-commit-only neighbours vector search never surfaced: "
          f"{len(co_commit_only_paths)} distinct notes across {len(anchors)} anchors "
          f"({vector_paths_total} vector neighbours fetched total)")
    if args.withhold_private:
        print(f"withheld from judge: {withheld} pairs")


def self_check():
    assert pair_key("a.md", "b.md") == pair_key("b.md", "a.md"), "pair key is order-independent"
    assert title("folder/my note.md") == "my note"
    print("self-check ok")


if __name__ == "__main__":
    main()
