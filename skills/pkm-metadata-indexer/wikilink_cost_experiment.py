"""Measure what wikilink markup costs a machine reader of a markdown vault.

Four deterministic measurements over a real vault, no API calls:

  tokens   how many tokens the `[[ ]]` markup itself adds (tiktoken cl100k)
  broken   share of wikilinks whose target note does not exist
  grep     share of wikilinks that sit mid-phrase, breaking literal substring search
  embed    cosine shift between a chunk with links and the same chunk stripped (fastembed)

The embed pass needs fastembed and downloads BAAI/bge-small-en-v1.5 on first run;
it is skipped with --no-embed. Everything else is stdlib plus tiktoken.

    python wikilink_cost_experiment.py <vault-dir> [--sample 200] [--no-embed]
"""

import argparse
import random
import re
import statistics
import sys
from pathlib import Path

WIKILINK = re.compile(r"\[\[([^\]\[|]+)(?:\|([^\]\[]*))?\]\]")
FRONTMATTER = re.compile(r"\A---\n.*?\n---\n", re.S)
CODE_FENCE = re.compile(r"```.*?```", re.S)


def display_text(match):
    """What a reader sees once the markup is gone: the alias if present, else the target."""
    alias = match.group(2)
    target = match.group(1)
    return alias if alias else target.split("/")[-1].split("#")[0]


def strip_links(text):
    return WIKILINK.sub(display_text, text)


def notes(vault):
    for p in sorted(vault.rglob("*.md")):
        if ".git" in p.parts or "node_modules" in p.parts:
            continue
        try:
            yield p, p.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue


def measure_tokens(docs, encoder):
    raw = stripped = 0
    per_note = []
    for path, text in docs:
        r = len(encoder.encode(text))
        s = len(encoder.encode(strip_links(text)))
        raw += r
        stripped += s
        if r:
            per_note.append(((r - s) / r * 100, path.name, r - s))
    per_note.sort(reverse=True)
    return raw, stripped, per_note


def classify_links(docs):
    """name-only `[[a]]`, alias `[[a|b]]`, path-alias `[[dir/a|a]]` - the last is the wasteful form."""
    counts = {"name-only": 0, "alias": 0, "path-alias": 0}
    for _, text in docs:
        for m in WIKILINK.finditer(text):
            if not m.group(2):
                counts["name-only"] += 1
            elif "/" in m.group(1):
                counts["path-alias"] += 1
            else:
                counts["alias"] += 1
    return counts


def measure_broken(vault, docs):
    """A link resolves if some note's stem matches its target, case-insensitively (Obsidian's rule)."""
    stems = {p.stem.lower() for p in vault.rglob("*.md")}
    total = broken = 0
    examples = []
    for path, text in docs:
        for m in WIKILINK.finditer(text):
            target = m.group(1).split("#")[0].split("/")[-1].strip().lower()
            if not target:
                continue
            total += 1
            if target not in stems:
                broken += 1
                if len(examples) < 8:
                    examples.append(f"{path.name} -> [[{m.group(1)}]]")
    return total, broken, examples


def measure_grep_breakage(docs):
    """A link with a word right before or after it breaks a literal two-word substring search.

    `unloading [[dishwasher]]` does not contain the substring "unloading dishwasher",
    so grep for the phrase misses a note that plainly says it.
    """
    total = mid_phrase = 0
    for _, text in docs:
        body = CODE_FENCE.sub("", FRONTMATTER.sub("", text))
        for line in body.split("\n"):
            for m in WIKILINK.finditer(line):
                total += 1
                before = line[: m.start()].rstrip()
                after = line[m.end():].lstrip()
                prev_word = bool(before) and before[-1].isalnum()
                next_word = bool(after) and after[0].isalnum()
                if prev_word or next_word:
                    mid_phrase += 1
    return total, mid_phrase


def measure_embedding_shift(docs, sample_size, seed=0):
    from fastembed import TextEmbedding
    import numpy as np

    chunks = []
    for _, text in docs:
        body = CODE_FENCE.sub("", FRONTMATTER.sub("", text))
        for para in body.split("\n\n"):
            para = para.strip()
            if len(para) > 120 and WIKILINK.search(para):
                chunks.append(para)
    random.Random(seed).shuffle(chunks)
    chunks = chunks[:sample_size]
    if not chunks:
        return None

    model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
    linked = np.array(list(model.embed(chunks)))
    plain = np.array(list(model.embed([strip_links(c) for c in chunks])))
    linked /= np.linalg.norm(linked, axis=1, keepdims=True)
    plain /= np.linalg.norm(plain, axis=1, keepdims=True)
    cos = (linked * plain).sum(axis=1)

    # a shift only matters next to the gap between unrelated chunks, so measure that too
    off_diagonal = linked @ linked.T
    n = len(chunks)
    baseline = (off_diagonal.sum() - np.trace(off_diagonal)) / (n * n - n) if n > 1 else float("nan")
    return len(chunks), float(cos.mean()), float(cos.min()), float(baseline)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("vault", type=Path)
    ap.add_argument("--sample", type=int, default=200, help="paragraphs for the embedding pass")
    ap.add_argument("--no-embed", action="store_true")
    args = ap.parse_args()

    import tiktoken

    encoder = tiktoken.get_encoding("cl100k_base")
    docs = list(notes(args.vault))
    print(f"vault: {args.vault}  notes: {len(docs)}")

    raw, stripped, per_note = measure_tokens(docs, encoder)
    overhead = (raw - stripped) / raw * 100
    print(f"\ntokens         raw {raw:,}  stripped {stripped:,}  markup {raw - stripped:,} ({overhead:.2f}%)")
    worst = per_note[:5]
    print("  worst notes: " + ", ".join(f"{name} {pct:.1f}% (+{d})" for pct, name, d in worst))
    pcts = [p for p, _, _ in per_note]
    print(f"  per-note median {statistics.median(pcts):.2f}%  p95 {sorted(pcts)[int(len(pcts) * 0.95)]:.2f}%")

    forms = classify_links(docs)
    print(f"\nlink forms     {forms}")

    total, broken, examples = measure_broken(args.vault, docs)
    print(f"\nbroken links   {broken:,} of {total:,} ({broken / total * 100:.1f}%) point at no note")
    for e in examples:
        print(f"  {e}")

    gtotal, mid = measure_grep_breakage(docs)
    print(f"\ngrep breakage  {mid:,} of {gtotal:,} ({mid / gtotal * 100:.1f}%) links sit mid-phrase")

    if not args.no_embed:
        result = measure_embedding_shift(docs, args.sample)
        if result:
            n, mean_cos, min_cos, baseline = result
            print(f"\nembedding      n={n}  cos(linked, stripped) mean {mean_cos:.4f}  min {min_cos:.4f}")
            print(f"  baseline cosine between unrelated chunks in the same sample: {baseline:.4f}")


def demo():
    """Self-check: the regex and the two text-level measurements behave on known input."""
    assert strip_links("unloading [[dishwasher]] now") == "unloading dishwasher now"
    assert strip_links("see [[public/foo|foo]]") == "see foo"
    assert strip_links("[[a#heading]]") == "a"
    assert strip_links("no links here") == "no links here"
    docs = [(Path("t.md"), "unloading [[dishwasher]]\n\nstandalone [[link]]\n\n[[alone]] here\n")]
    total, mid = measure_grep_breakage(docs)
    assert (total, mid) == (3, 3), (total, mid)
    docs = [(Path("t.md"), "[[alone]]\n")]
    assert measure_grep_breakage(docs) == (1, 0)
    print("demo ok")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--demo":
        demo()
    else:
        main()
