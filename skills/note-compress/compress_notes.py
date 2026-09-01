"""Compress agent-read reference notes in place, one cheap LLM call per note,
gated by a free mechanical fidelity check instead of a second paid LLM call.

Why one call, not the two-call classify+adversarial-gate design this session
already measured (31-40% cut, 85-98/100 retention, on 5 real notes): across
all 10 compressions measured this session (5 classifier-method, 5
caveman-compress), the only failure class that ever occurred was framing
drift (a hedge softened, a causal connector dropped) — never a lost number,
code identifier, wikilink, or URL. A program can check the second class for
free; it cannot judge the first without another model call. So this script
extracts wikilinks/numbers/dates/URLs/code spans before and after
compression and rejects (keeps the original untouched) if anything essential
went missing, rather than paying for an adversarial LLM pass on every note.

A free mechanical delint pass (`delint()`) strips decorative emoji from
headings and bullets before the LLM ever sees the note. Handing the model
that job instead was tried and measured to bleed into fenced ASCII-art code
blocks it was separately told never to touch - real regressions on this
vault's own emoji-heavy notes, not a hypothetical. A regex scoped to
heading/bullet lines and blind to fenced code can't make that mistake.

Eligibility, not "compress everything": a compression pass only pays for
itself after enough future rereads recoup its own cost (this vault's own
research measured a 2-11 to ~20-48 reread break-even range depending on
design and pricing assumptions — see the research note this skill implements).
So this only targets notes likely to be reread: high-backlink reference notes
(via the vault's own wikilink `edges` table) and anything under `learnings/`
by convention, above a minimum size (short notes rarely justify the call).

    python skills/note-compress/compress_notes.py --dry-run --sample 5
    python skills/note-compress/compress_notes.py --apply --folder learnings/

Uses Groq (free tier, openai/gpt-oss-20b) or Gemini Flash, whichever key
is set — same provider choice as skills/notes-sentiment-analysis, so a vault
that already has one of those keys configured needs nothing new.

Optional `--audit-sample N`: the mechanical gate above can't catch framing
drift, so this runs a second, judge-style LLM call on a sample of passed
notes to at least measure that blind spot instead of leaving it unmonitored.
Rating Roulette (2025, arXiv:2510.27106) measured LLM judges to be highly
inconsistent run-to-run on identical input (intra-rater Krippendorff's alpha
0.265-0.563) and found averaging several independent judge calls, not
majority vote and not temperature=0, is what recovers agreement with human
judgment — so this samples the judge `samples` times per note and averages.
G-Eval (Liu et al. 2023, arXiv:2303.16634) gets a similar effect from
logprob-weighted scoring, but that needs raw token logprobs Groq/Gemini
don't cleanly expose for an arbitrary score token, hence sample-and-average
instead of logprobs here.

The same audit also scores relinking, a distinct failure neither the
mechanical gate nor the framing judge catches: KBRA (2026, arXiv:2606.21732,
"Safe to Check, Unsafe to Use: Relinking at the Compression Boundary of LLM
Agents") names the case where two fragments that were each individually true
in the original get reassembled by the compression into a claim the original
never made — "X happened in March" plus, separately, "Y caused delays"
becoming "X happened in March because Y caused delays". The mechanical gate
only checks that spans survive, not what new claims got built by juxtaposing
them, and the framing judge only checks whether existing hedges/connectors
survived, not whether a new one got invented — so this runs a second judge
prompt (`RELINK_PROMPT`) asking specifically whether the compressed text
asserts any connection between two facts the original left unconnected,
sampled and averaged the same way as the framing score.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import re
import sqlite3
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

MIN_WORDS = 300  # below this, a compression call rarely pays for itself
MIN_BACKLINKS = 3  # in-degree in the wikilink graph, the free reread-frequency proxy
EXCLUDED_FOLDERS = {".obsidian", ".git", ".github", "skills"}

COMPRESS_PROMPT = """Compress the note body below for a future AI reader, not a human skimming it live. Classify each part as ESSENTIAL (facts, numbers, decisions, links, code, technical terms, causal reasoning, hedges like "might" or "usually") or DISPOSABLE (connective filler, restated context, redundant transitions) and rewrite keeping only the essential content in the fewest words that preserve it exactly.

Hard rules:
- Never alter, remove, or paraphrase a [[wikilink]], a URL, a number, a date, a percentage, a dollar amount, an inline code span, or a fenced code block. Copy these byte-for-byte exactly as they appear in the original.
- Never drop a causal connector ("because", "so", "therefore", "since") if removing it would make the reader infer a relationship the original stated explicitly.
- Never drop a hedge or confidence marker ("might", "some", "usually", "observed", "confirmed") — these change what the note claims, not just how it's worded.
- Keep every markdown heading exactly as written, same level, same text.
- DO collapse a stack of near-synonym adjectives that all make the same point into one or two words: "hyper-agreeable, polite, and eager to please" -> "agreeable and pleasing" is a good cut, not a loss.
- Cut prose bulk, not claims: merging two sentences that say the same thing is fine, removing one that says something distinct is not.
- Return ONLY the compressed markdown body. No preamble, no explanation, no code fence around the whole response.

NOTE BODY:
{body}"""

AUDIT_PROMPT = """Score, from 0 to 100, how well the COMPRESSED version below preserves the ORIGINAL's hedges (words like "might", "usually", "some"), confidence/epistemic markers ("observed" vs "confirmed"), and causal or logical connectors ("because", "so", "therefore", "since"). Do not score general quality, fact retention, or wording style — only whether the framing and claimed certainty survived.

Respond with ONLY the integer score, nothing else.

ORIGINAL:
{original}

COMPRESSED:
{compressed}"""

RELINK_PROMPT = """Score, from 0 to 100, how well the COMPRESSED version below avoids asserting a NEW connection between facts that were separate and unconnected in the ORIGINAL.

A relinking failure: the ORIGINAL states two individually true things separately and without connecting them (e.g. "X happened in March." ... elsewhere, unrelated: "Y caused delays."), and the COMPRESSED text combines them into a claim the ORIGINAL never made (e.g. "X happened in March because Y caused delays") — a causal, temporal, or other link built from two true fragments, even though neither fragment alone is false.

100 = every claim and every connection between facts in the COMPRESSED text was already made, in that combination, in the ORIGINAL. 0 = the COMPRESSED text asserts a causal link, sequence, or combined claim between two facts the ORIGINAL never connected.

Do not score general quality, wording, hedges, or omitted content — only whether the COMPRESSED text links two things the ORIGINAL kept separate.

Respond with ONLY the integer score, nothing else.

ORIGINAL:
{original}

COMPRESSED:
{compressed}"""

SCORE_RE = re.compile(r"-?\d+")

WIKILINK_RE = re.compile(r"\[\[([^\]|#]+)")
MD_LINK_URL_RE = re.compile(r"\]\((https?://[^\s)]+)\)")
BARE_URL_RE = re.compile(r"(?<!\()https?://\S+")
DATE_RE = re.compile(r"\b\d{4}-\d{2}-\d{2}\b")
NUMBER_RE = re.compile(r"(?<![\w.])\d[\d,]*\.?\d*%?(?![\w])")
FENCED_CODE_RE = re.compile(r"```.*?```", re.DOTALL)
INLINE_CODE_RE = re.compile(r"`[^`\n]+`")
EMOJI_RE = re.compile(
    "[\U0001F300-\U0001FAFF\U00002600-\U000027BF\U0001F1E6-\U0001F1FF️]+\\s*"
)


def delint(text: str) -> str:
    """Strip decorative emoji from headings and list markers, free and zero-risk.

    A judgment prompt asked to do this itself ("strip decorative styling")
    was measured to bleed that permission into fenced ASCII-art code blocks
    it was separately told never to touch - a real regression found by
    testing against this vault's own emoji-heavy notes, not a hypothetical.
    A regex that only touches heading/bullet lines and skips fenced code
    entirely can't make that mistake, so this runs unconditionally before
    the LLM ever sees the note, instead of being left to the model's
    judgment.
    """
    parts = re.split(r"(```.*?```)", text, flags=re.DOTALL)
    for i, part in enumerate(parts):
        if part.startswith("```"):
            continue  # never touch fenced code
        lines = part.split("\n")
        parts[i] = "\n".join(
            EMOJI_RE.sub("", line) if line.lstrip().startswith(("#", "*", "-")) else line
            for line in lines
        )
    return "".join(parts)


def find_vault_root() -> Path:
    current = Path(__file__).resolve().parent
    for p in [Path.cwd(), current, current.parent, current.parent.parent]:
        if (p / ".obsidian").exists() or (p / ".git").exists():
            return p
    return current.parent.parent


VAULT_ROOT = find_vault_root()


def content_hash(text: str) -> str:
    return hashlib.md5(text.encode("utf-8")).hexdigest()[:8]


def extract_invariants(text: str) -> dict[str, set[str]]:
    """Everything a compression pass must never lose, as comparable sets.

    Wikilink targets are normalised (lowercased, trailing/leading space
    stripped) since aliasing or case shouldn't count as a loss; everything
    else is compared as the exact substring the source used, since exact
    reproduction is the whole point of the "preserve exactly" rule.
    """
    fenced = FENCED_CODE_RE.findall(text)
    without_fences = FENCED_CODE_RE.sub(" ", text)  # avoid double-counting code-in-code
    # Both regexes are greedy about trailing characters that are usually
    # sentence punctuation, not part of the token: a bare URL's \S+ swallows
    # a trailing "." before end-of-sentence, and the number pattern's
    # thousands-separator comma can't tell "1,000" from "27," at a clause
    # boundary. Stripped here rather than by tightening the regexes further,
    # since a regex that never over-matches trailing punctuation also can't
    # simply require 3-digit groups after a comma without breaking on partial
    # numbers like "12,3".
    strip_trailing = lambda values: {v.rstrip(".,;:!?)'\"") for v in values}
    return {
        "wikilinks": {m.strip().lower() for m in WIKILINK_RE.findall(text)},
        "urls": strip_trailing(set(MD_LINK_URL_RE.findall(text)) | set(BARE_URL_RE.findall(text))),
        "dates": set(DATE_RE.findall(text)),
        "numbers": strip_trailing(set(NUMBER_RE.findall(without_fences))),
        "inline_code": set(INLINE_CODE_RE.findall(without_fences)),
        "fenced_code": set(fenced),
    }


def verify_invariants(original: str, compressed: str) -> tuple[bool, list[str]]:
    """True (and no reasons) only if compressed lost nothing essential.

    A subset check, not equality: the compressed version keeping extra
    copies of a number or repeating a link is not a loss. Missing something
    the original had is.
    """
    before, after = extract_invariants(original), extract_invariants(compressed)
    reasons = []
    for category, before_set in before.items():
        missing = before_set - after[category]
        if missing:
            sample = ", ".join(sorted(missing)[:5])
            reasons.append(f"{category}: lost {len(missing)} ({sample})")
    return not reasons, reasons


def word_count(text: str) -> int:
    return len(text.split())


def backlink_counts(db_path: Path) -> dict[str, int]:
    """path -> inbound wikilink count, the free reread-frequency proxy.

    Missing index (never built, or a fresh vault) degrades to "nobody
    qualifies by backlinks" rather than an error - `learnings/` membership
    alone can still make a note eligible.
    """
    if not db_path.exists():
        return {}
    connection = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        rows = connection.execute(
            "SELECT resolved_target_path, COUNT(*) FROM edges "
            "WHERE resolved_target_path IS NOT NULL GROUP BY resolved_target_path"
        ).fetchall()
        return dict(rows)
    finally:
        connection.close()


def is_excluded(path: Path, vault_root: Path) -> bool:
    parts = path.relative_to(vault_root).parts
    return any(part in EXCLUDED_FOLDERS for part in parts)


def find_eligible_notes(vault_root: Path, db_path: Path, folder: str | None,
                        min_words: int, min_backlinks: int) -> list[Path]:
    import frontmatter
    root = (vault_root / folder) if folder else vault_root
    backlinks = backlink_counts(db_path)
    eligible = []
    for path in root.rglob("*.md"):
        if is_excluded(path, vault_root):
            continue
        try:
            body = frontmatter.load(path, encoding="utf-8").content
        except Exception:
            continue
        if word_count(body) < min_words:
            continue
        rel = path.relative_to(vault_root).as_posix()
        under_learnings = "learnings/" in rel or rel.startswith("learnings/")
        has_backlinks = backlinks.get(rel, 0) >= min_backlinks
        if folder or under_learnings or has_backlinks:
            eligible.append(path)
    return sorted(eligible)


def call_llm(client, provider: str, model: str, body: str = "", max_retries: int = 3,
             prompt: str | None = None) -> str | None:
    """Reasoning-style Groq models (gpt-oss-*) sometimes spend the whole
    completion on the hidden `reasoning` field and leave `content` empty -
    observed non-deterministically on identical input, not tied to a
    specific note. Treat empty content as a retryable failure, same as a
    rate limit, rather than returning it as if it were a real compression.

    `prompt`, if given, is sent as-is (already formatted, e.g. AUDIT_PROMPT)
    instead of building COMPRESS_PROMPT from `body`.
    """
    prompt = prompt if prompt is not None else COMPRESS_PROMPT.format(body=body)
    for attempt in range(max_retries):
        try:
            if provider == "groq":
                # gpt-oss-* is a reasoning model: at the default max_tokens
                # it can spend the whole budget on hidden reasoning and hit
                # finish_reason="length" before writing any content.
                # reasoning_effort="low" and a larger cap fix that instead
                # of just retrying into the same wall.
                response = client.chat.completions.create(
                    model=model, messages=[{"role": "user", "content": prompt}],
                    max_tokens=4096, reasoning_effort="low",
                )
                content = (response.choices[0].message.content or "").strip()
            else:
                response = client.models.generate_content(model=model, contents=prompt)
                content = (response.text or "").strip()
            if content:
                return content
            time.sleep(1)
        except Exception as error:
            err = str(error)
            if "429" in err or "rate_limit" in err or "RESOURCE_EXHAUSTED" in err:
                time.sleep(3 * (attempt + 1))
            else:
                time.sleep(1)
    return None


def parse_score(response: str) -> int | None:
    match = SCORE_RE.search(response)
    return int(match.group()) if match else None


def _judge_score(client, provider: str, model: str, prompt_template: str, original: str,
                 compressed: str, samples: int) -> float | None:
    """Run one judge prompt `samples` times and average, per Rating Roulette
    (arXiv:2510.27106): averaging repeat judge calls, not majority vote or
    temperature=0, is what recovers agreement with human judgment.
    """
    prompt = prompt_template.format(original=original, compressed=compressed)
    scores = []
    for _ in range(samples):
        response = call_llm(client, provider, model, prompt=prompt)
        if response is None:
            continue
        score = parse_score(response)
        if score is not None:
            scores.append(score)
    return sum(scores) / len(scores) if scores else None


def audit_note(client, provider: str, model: str, original: str, compressed: str,
               samples: int = 3) -> tuple[float | None, float | None]:
    """Judge framing-fidelity and relinking-fidelity, each averaged over
    `samples` independent judge calls, and return (framing_score, relink_score).

    Two separate prompts and two separate score series rather than one prompt
    asking for both numbers: framing fidelity ("did a hedge/connector
    survive") and relinking ("did a NEW connection get invented") are
    different questions, and mixing them into one judge call risks one
    answer anchoring the other. The relinking score exists because of KBRA
    (arXiv:2606.21732): fragments that were each individually true in the
    original can get reassembled by compression into a claim the original
    never made, and neither the mechanical invariant gate (which only checks
    spans survive) nor the framing judge (which only checks existing
    hedges/connectors survive) catches a brand new one being added.
    """
    framing = _judge_score(client, provider, model, AUDIT_PROMPT, original, compressed, samples)
    relinking = _judge_score(client, provider, model, RELINK_PROMPT, original, compressed, samples)
    return framing, relinking


def process_note(path: Path, vault_root: Path, client, provider: str, model: str,
                 apply: bool) -> dict:
    import frontmatter
    post = frontmatter.load(path, encoding="utf-8")
    body = post.content
    before_hash = content_hash(body)
    if post.metadata.get("compress-hash") == before_hash:
        return {"path": str(path), "status": "skipped-unchanged"}

    body = delint(body)  # free, zero-risk emoji strip before spending the one LLM call
    compressed = call_llm(client, provider, model, body)
    if compressed is None:
        return {"path": str(path), "status": "error-no-response"}

    ok, reasons = verify_invariants(body, compressed)
    before_words, after_words = word_count(body), word_count(compressed)
    result = {
        "path": str(path.relative_to(vault_root)),
        "words_before": before_words,
        "words_after": after_words,
        "cut_pct": round((1 - after_words / before_words) * 100, 1) if before_words else 0.0,
    }
    if not ok:
        result["status"] = "rejected"
        result["reasons"] = reasons
        return result

    result["status"] = "applied" if apply else "would-apply"
    result["_body"] = body
    result["_compressed"] = compressed
    if apply:
        post.content = compressed
        post["compressed"] = True
        post["compress-hash"] = before_hash
        post["compress-cut-pct"] = result["cut_pct"]
        path.write_text(frontmatter.dumps(post) + "\n", encoding="utf-8")
    return result


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--apply", action="store_true",
                        help="Actually rewrite notes. Without this, nothing is written "
                             "(dry-run is the default, not opt-in, since this rewrites bodies)")
    parser.add_argument("--sample", type=int, default=None, help="Process N random eligible notes")
    parser.add_argument("--folder", type=str, default=None,
                        help="Restrict to a subfolder (also makes every note in it eligible, "
                             "bypassing the backlink/learnings filter)")
    parser.add_argument("--min-words", type=int, default=MIN_WORDS)
    parser.add_argument("--min-backlinks", type=int, default=MIN_BACKLINKS)
    parser.add_argument("--db", type=Path, default=None,
                        help="pkm index db for backlink counts, defaults to <vault>/.obsidian/pkm_index.db")
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--model", type=str, default=None)
    parser.add_argument("--report", type=Path, default=None, help="Write a JSON bench report here")
    parser.add_argument("--audit-sample", type=int, default=0,
                        help="Judge framing-fidelity and relinking-fidelity on N passed notes, "
                             "3 averaged LLM calls each per score (0 = off, default)")
    parser.add_argument("--self-check", action="store_true")
    args = parser.parse_args()

    if args.self_check:
        return self_check()

    db_path = args.db or (VAULT_ROOT / ".obsidian" / "pkm_index.db")
    notes = find_eligible_notes(VAULT_ROOT, db_path, args.folder, args.min_words, args.min_backlinks)
    print(f"Vault: {VAULT_ROOT}\nEligible notes: {len(notes)}")
    if args.sample and len(notes) > args.sample:
        notes = random.sample(notes, args.sample)
        print(f"Sampled: {len(notes)}")
    if not notes:
        return

    provider = "gemini"
    model = args.model or "gemini-2.5-flash"
    api_key = os.environ.get("GEMINI_API_KEY")
    groq_key = os.environ.get("GROQ_API") or os.environ.get("GROQ_API_KEY")
    if groq_key:
        provider, api_key, model = "groq", groq_key, (args.model or "openai/gpt-oss-20b")
        from groq import Groq
        client = Groq(api_key=api_key)
    elif api_key:
        from google import genai
        client = genai.Client(api_key=api_key)
    else:
        print("Error: set GROQ_API (free) or GEMINI_API_KEY.")
        sys.exit(1)

    if not args.apply:
        print("DRY RUN — no files will be modified (pass --apply to write)\n")

    results = []
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {executor.submit(process_note, path, VAULT_ROOT, client, provider, model,
                                   args.apply): path for path in notes}
        for future in as_completed(futures):
            result = future.result()
            results.append(result)
            print(f"  {result['status']:16} {result.get('cut_pct', 0):5.1f}%  {result['path']}")
            if result["status"] == "rejected":
                for reason in result["reasons"]:
                    print(f"                     rejected: {reason}")

    applied = [r for r in results if r["status"] in ("applied", "would-apply")]
    rejected = [r for r in results if r["status"] == "rejected"]
    print(f"\n{len(applied)} compressed, {len(rejected)} rejected by the fidelity gate, "
          f"{len(results) - len(applied) - len(rejected)} skipped/errored")
    if applied:
        mean_cut = sum(r["cut_pct"] for r in applied) / len(applied)
        print(f"Mean cut on applied notes: {mean_cut:.1f}%")

    if args.report:
        args.report.write_text(json.dumps(results, indent=1), encoding="utf-8")
        print(f"Report written to {args.report}")

    if args.audit_sample > 0:
        candidates = applied
        if len(candidates) > args.audit_sample:
            candidates = random.sample(candidates, args.audit_sample)
        print(f"\nAuditing framing fidelity and relinking on {len(candidates)} note(s), "
              f"3 judge calls each:")
        framing_scores, relink_scores = [], []
        for result in candidates:
            framing, relinking = audit_note(client, provider, model, result["_body"],
                                            result["_compressed"])
            framing_str = f"{framing:5.1f}" if framing is not None else "(none)"
            relink_str = f"{relinking:5.1f}" if relinking is not None else "(none)"
            print(f"  framing={framing_str}  relink={relink_str}  {result['path']}")
            if framing is not None:
                framing_scores.append(framing)
            if relinking is not None:
                relink_scores.append(relinking)
        if framing_scores:
            print(f"Mean framing-fidelity score: {sum(framing_scores) / len(framing_scores):.1f}")
        if relink_scores:
            print(f"Mean relinking-fidelity score: {sum(relink_scores) / len(relink_scores):.1f}")


def self_check():
    original = (
        "## Finding\nThe daemon [[searchd.py|search daemon]] was burning 12 cores because "
        "the ONNX pool busy-spins. Measured 11.93 of 12 cores idle. Fixed on 2026-08-27 "
        "by capping `QUERY_THREADS = 1`. See https://example.com/onnx for the upstream issue."
    )
    # A faithful compression: cuts filler, keeps every invariant exactly.
    faithful = (
        "## Finding\n[[searchd.py|search daemon]] burned 12 cores, ONNX pool busy-spins. "
        "11.93 of 12 cores idle. Fixed 2026-08-27, capped `QUERY_THREADS = 1`. "
        "See https://example.com/onnx."
    )
    ok, reasons = verify_invariants(original, faithful)
    assert ok, f"a faithful compression must pass: {reasons}"

    # An unfaithful one: drops the wikilink and a number.
    unfaithful = "the search daemon burned cores because of a busy-spin. fixed by capping threads."
    ok, reasons = verify_invariants(original, unfaithful)
    assert not ok, "dropping a wikilink and every number must fail the gate"
    joined = " ".join(reasons)
    assert "wikilinks" in joined and "numbers" in joined

    assert word_count("a b c") == 3
    assert content_hash("x") == content_hash("x") and content_hash("x") != content_hash("y")

    decorated = (
        "## \U0001F680 Launch Plan\n"
        "- ✅ ship it\n"
        "plain prose keeps its \U0001F600 untouched, only heading/bullet markers are cleaned\n"
        "```\n\U0001F680 this fenced emoji must survive, code is never touched\n```"
    )
    cleaned = delint(decorated)
    assert cleaned.startswith("## Launch Plan"), cleaned
    assert "- ship it" in cleaned
    assert "\U0001F600" in cleaned, "delint must only touch heading/bullet lines, not prose"
    assert "\U0001F680 this fenced emoji must survive" in cleaned, "fenced code must never be touched"

    assert parse_score("87") == 87
    assert parse_score("Score: 42") == 42
    assert parse_score("  95  ") == 95
    assert parse_score("no number here") is None

    # Synthetic relinking case (KBRA, arXiv:2606.21732): two facts that are
    # true and stated but never connected in the original. "good" repeats
    # them separately; "bad" invents a causal link between them.
    relink_original = (
        "## Timeline\nThe [[migration]] to the new billing service happened in March 2026. "
        "Separately, the vendor's API had an outage that caused a two-week delay in Q1 2026."
    )
    relink_good = (
        "## Timeline\n[[migration]] to new billing service: March 2026. "
        "Separately, vendor API outage caused a two-week delay, Q1 2026."
    )
    relink_bad = (
        "## Timeline\nThe [[migration]] to the new billing service happened in March 2026 "
        "because the vendor's API outage caused a two-week delay."
    )

    class _FakeModels:
        def __init__(self, texts):
            self._texts = iter(texts)

        def generate_content(self, model, contents):
            return type("R", (), {"text": next(self._texts)})()

    class _FakeClient:
        def __init__(self, texts):
            self.models = _FakeModels(texts)

    # audit_note calls the framing prompt `samples` times, then the relink
    # prompt `samples` times: feed framing scores first, then relink scores.
    good_client = _FakeClient(["90", "88", "92", "95", "97", "96"])
    framing, relinking = audit_note(good_client, "gemini", "fake-model",
                                    relink_original, relink_good, samples=3)
    assert framing == 90.0, framing
    assert relinking == 96.0, relinking

    bad_client = _FakeClient(["85", "80", "83", "10", "15", "5"])
    framing, relinking = audit_note(bad_client, "gemini", "fake-model",
                                    relink_original, relink_bad, samples=3)
    assert abs(framing - 82.67) < 0.01, framing
    assert relinking == 10.0, relinking
    assert relinking < 96.0, "a bad (invented-link) compression must score lower than a good one"

    print("self-check ok")


if __name__ == "__main__":
    main()
