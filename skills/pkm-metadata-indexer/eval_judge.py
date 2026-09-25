"""One judge, one cache, one set of metrics, for every eval that asks a model
"would this note help answer the question?".

Extracted rather than copied. eval_rerank.py and eval_outline.py were written as
copies of one another and so carried the same two faults -- a `temperature` the
gateway rejects outright, and a failed call cached as a verdict -- and each fault
had to be found and fixed twice, on two separate days, from two separate wrong
results. A third eval written the same way would have carried them a third time.
The rule this module exists to hold in one place: a judgement that did not happen
is never written to the cache, and the run says so out loud.
"""

from __future__ import annotations

import json
import os
import urllib.error
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from eval_rerank import post, judge_answer

GATEWAY = os.environ.get("GATEWAY", "http://127.0.0.1:8080")

JUDGE_PROMPT = """Someone searching their notes asks: "{question}"

Below is one note from the search results, shown as its title and the section
headings it contains.

---
{content}
---

Would this note help answer the question? Answer with one word, YES or NO."""


def cache_key(question: str, path: str, model: str) -> str:
    """The one place a judgement's identity is spelled.

    The judge model belongs in the key: two judges scoring the same (question,
    note) must not read each other's verdict, and a key that omits the model
    silently fuses them into one voter whose numbers look like agreement.

    The arm does not belong in the key, and that is a constraint on the caller
    rather than a free choice: it holds only while both arms show the judge the
    same text for the same note. An eval whose arms render a note differently
    must key on the content, not reuse this.
    """
    return f"{question}|{path}|{model}"


def judge_request(model: str, prompt: str) -> tuple[str, dict]:
    """URL and body for one judgement, in whichever dialect the model speaks.

    No `temperature`: the gateway rejects it outright for claude-opus-5 and
    claude-sonnet-5 with "temperature is deprecated for this model", and an
    HTTPError is a URLError, so sending it turns every judgement into a caught
    exception and a judge that answered nothing looks like one that rejected
    everything.

    `max_tokens` is 512 and not the 8 a one-word answer needs, because
    claude-opus-5 uses adaptive thinking and spends the budget before it writes
    anything: at 8 and at 64 tokens it returned finish_reason "length" and an
    empty string on 293 of 349 real prompts, at 256 it answered 79% of them and
    at 512 it answers all of them. A one-word verdict needs a paragraph of
    headroom. Sonnet does not engage thinking on this prompt and was unaffected,
    which is exactly why a single-judge eval hid this.
    """
    if model.startswith("gemini"):
        return f"{GATEWAY}/v1beta/models/{model}:generateContent", {
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0, "maxOutputTokens": 8,
                                 "thinkingConfig": {"thinkingBudget": 0}},
        }
    return f"{GATEWAY}/v1/chat/completions", {
        "model": model, "max_tokens": 512,
        "messages": [{"role": "user", "content": prompt}],
    }


def judge(prompt: str, model: str) -> bool | None:
    """Ask one model for one verdict. None means it did not answer."""
    url, payload = judge_request(model, prompt)
    try:
        data = post(url, payload, timeout=120)
    except (urllib.error.URLError, TimeoutError) as error:
        print(f"  judge {model} failed: {error}", flush=True)
        return None

    answer = judge_answer(model, data).strip().upper()
    if answer.startswith(("YES", "NO")):
        return answer.startswith("YES")
    # Said out loud rather than returned quietly. An unparseable reply and a
    # failed call both became None here, so a model that was burning its whole
    # token budget on thinking and returning "" was indistinguishable from one
    # that had judged the note unhelpful -- for two full runs.
    print(f"  judge {model} gave no verdict: {answer[:60]!r}"
          f" (finish {data.get('choices', [{}])[0].get('finish_reason')})", flush=True)
    return None


def judge_all(pending: list[tuple[str, str, str, str]], cached: dict,
              failures: dict[str, int], workers: int = 8) -> None:
    """Judge every (question, path, model, prompt) not already answered.

    Mutates `cached` and `failures`. A failure is retried on the next run and
    never remembered: a cached null is indistinguishable from "the judge said
    no", and scoring it as not-useful reads a broken call as a verdict -- which
    is how one poisoned run made a better ranking look like a regression.
    """
    if not pending:
        return
    with ThreadPoolExecutor(max_workers=workers) as pool:
        verdicts = pool.map(lambda job: judge(job[3], job[2]), pending)
        for (question, path, model, _prompt), verdict in zip(pending, verdicts):
            if verdict is None:
                failures[model] += 1
            else:
                cached[cache_key(question, path, model)] = verdict


def load_cache(path: Path) -> dict:
    path.parent.mkdir(parents=True, exist_ok=True)
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def save_cache(path: Path, cached: dict) -> None:
    path.write_text(json.dumps(cached, indent=1, sort_keys=True), encoding="utf-8")


def load_questions(path: str) -> list[tuple[str, str]]:
    """Read a question set: [[question, group], ...]."""
    rows = json.loads(Path(path).read_text(encoding="utf-8"))
    return [(row[0], row[1]) for row in rows]


def precision_at_k(ranked: list[str], verdicts: dict[str, bool | None],
                   k: int) -> tuple[int, int]:
    """Useful notes in the top k, over the slots that exist."""
    useful = sum(1 for path in ranked[:k] if verdicts.get(path))
    return useful, min(k, len(ranked))


def first_useful_rank(ranked: list[str], verdicts: dict[str, bool | None]) -> int | None:
    """1-indexed rank of the first useful note, or None if none is."""
    for rank, path in enumerate(ranked):
        if verdicts.get(path):
            return rank + 1
    return None


def compute_metrics(ranked: list[str], verdicts: dict[str, bool | None]) -> dict:
    first = first_useful_rank(ranked, verdicts)
    return {
        "p5": precision_at_k(ranked, verdicts, 5),
        "p10": precision_at_k(ranked, verdicts, 10),
        "first_rank": first,
        "has_useful": first is not None,
    }


def report_arms(results: list[dict], model: str, arms: tuple[str, ...]) -> None:
    """Print one judge's numbers for each arm."""
    for arm in arms:
        p5_useful = sum(r["judges"][model][arm]["p5"][0] for r in results)
        p5_total = sum(r["judges"][model][arm]["p5"][1] for r in results)
        p10_useful = sum(r["judges"][model][arm]["p10"][0] for r in results)
        p10_total = sum(r["judges"][model][arm]["p10"][1] for r in results)
        first_ranks = [r["judges"][model][arm]["first_rank"]
                       for r in results if r["judges"][model][arm]["first_rank"]]
        mean_first = sum(first_ranks) / len(first_ranks) if first_ranks else None

        p5_pct = f"{p5_useful/p5_total:.1%}" if p5_total else "n/a"
        p10_pct = f"{p10_useful/p10_total:.1%}" if p10_total else "n/a"
        mean_str = f"{mean_first:.1f}" if mean_first else "none"
        print(f"  {arm}: precision@5 {p5_useful}/{p5_total} = {p5_pct}  "
              f"precision@10 {p10_useful}/{p10_total} = {p10_pct}", flush=True)
        print(f"       answered {len(first_ranks)}/{len(results)}  "
              f"mean first useful rank {mean_str}", flush=True)


def report_coverage(results: list[dict], cached: dict, model: str,
                    failures: dict[str, int]) -> float:
    """Print how much of its work a judge actually did, and warn if it is thin.

    Coverage, not abstention, is the number that catches an unusable judge. A
    judge can be missing verdicts two ways: it was asked and failed, or the run
    stopped before it was asked at all. The second is invisible in the failure
    count, and it is the one that actually happened -- one judge answered 332
    pairs and the other 32, and both reported zero failures.
    """
    want = sum(len(r["notes"]) for r in results)
    got = sum(1 for r in results for path in r["notes"]
              if cache_key(r["question"], path, model) in cached)
    share = got / want if want else 0.0
    print(f"  coverage: {got}/{want} pairs judged = {share:.1%}"
          f"   calls that failed this run: {failures.get(model, 0)}", flush=True)
    if share < 0.90:
        print(f"  WARNING: {model} judged only {share:.0%} of its pairs. Its numbers "
              f"above are NOT comparable to a judge with full coverage -- an unjudged "
              f"note scores the same as a rejected one.", flush=True)
    return share


def agreement(results: list[dict], cached: dict, j1: str, j2: str) -> list[bool]:
    """Did the two judges say the same thing, over the pairs both actually saw.

    Per question, from that question's own note list. Counted only where both
    judges have a verdict -- a pair one judge never answered is not a
    disagreement, and folding it in would make a thin judge look contrary.
    """
    return [cached[cache_key(result["question"], path, j1)]
            == cached[cache_key(result["question"], path, j2)]
            for result in results for path in result["notes"]
            if cache_key(result["question"], path, j1) in cached
            and cache_key(result["question"], path, j2) in cached]


def report_agreement(results: list[dict], cached: dict, judges: list[str]) -> None:
    if len(judges) != 2:
        return
    j1, j2 = judges
    agreements = agreement(results, cached, j1, j2)
    if agreements:
        agree, total = sum(agreements), len(agreements)
        print(f"Inter-judge agreement: {agree}/{total} = {agree/total:.1%}", flush=True)
        print(f"  ({j1} vs {j2} on {total} (question, note) pairs)", flush=True)


def self_check() -> None:
    """Assertions on the shared harness. Called by every eval's own --self-check."""
    # The cache key must separate judges. Asserted through the function the run
    # actually calls -- a test that rebuilds the key with its own f-string passes
    # even when the caller's key has no model in it, which is the bug this catches.
    assert cache_key("q", "a.md", "judge-one") != cache_key("q", "a.md", "judge-two")
    assert cache_key("q", "a.md", "j") == cache_key("q", "a.md", "j")
    assert cache_key("q1", "a.md", "j") != cache_key("q2", "a.md", "j")
    assert cache_key("q", "a.md", "j") != cache_key("q", "b.md", "j")

    # Agreement is counted per question. This once read a loop variable left over
    # from the judging loop, so every question was scored against the last
    # question's notes and 31 comparable pairs were reported as 2.
    results = [{"question": "q1", "notes": ["a.md"]}, {"question": "q2", "notes": ["b.md"]}]
    cached = {cache_key("q1", "a.md", "j1"): True, cache_key("q1", "a.md", "j2"): True,
              cache_key("q2", "b.md", "j1"): True, cache_key("q2", "b.md", "j2"): False}
    assert agreement(results, cached, "j1", "j2") == [True, False]
    # A pair only one judge answered is not a disagreement.
    assert agreement(results, {cache_key("q1", "a.md", "j1"): True}, "j1", "j2") == []

    # A failed judgement is counted and never cached, so the next run retries it
    # instead of reading it back as a NO. This is the invariant the module exists
    # to hold, so it is asserted against the real judge_all with the model call
    # swapped out, not against a reimplementation of it.
    global judge
    real_judge = judge
    try:
        judge = lambda prompt, model: None if model == "broken" else True
        cached, failures = {}, {"broken": 0, "fine": 0}
        judge_all([("q", "a.md", "broken", "p"), ("q", "b.md", "fine", "p")],
                  cached, failures, workers=1)
        assert cached == {cache_key("q", "b.md", "fine"): True}, cached
        assert failures == {"broken": 1, "fine": 0}, failures
    finally:
        judge = real_judge

    # Metrics: a None verdict is not useful, and does not stop the scan.
    verdicts = {"a": True, "b": False, "c": None, "d": True}
    metrics = compute_metrics(["b", "c", "a", "d"], verdicts)
    assert metrics["p5"] == (2, 4), metrics["p5"]
    assert metrics["p10"] == (2, 4), metrics["p10"]
    assert metrics["first_rank"] == 3, metrics["first_rank"]
    assert first_useful_rank(["b", "c"], verdicts) is None

    # No judge was asked, so nothing was answered: an empty pending list is not
    # an error and must not be recorded as a failure.
    cached, failures = {}, {"m": 0}
    judge_all([], cached, failures)
    assert cached == {} and failures == {"m": 0}
