#!/usr/bin/env python3
"""Decide whether to read a note's outline or the whole note, and serve either.

Two-step retrieval (read the `##` outline, then fetch one section) is not always
cheaper than reading the file outright. It buys a smaller context at the price of
one extra API round trip, and a round trip re-reads the entire conversation
prefix from cache. This script prices both paths and prints the answer.

    note_outline.py NOTE.md --context 60000
        verdict + the outline, one line per section with its line range

    note_outline.py NOTE.md --section-n 7
        just that section's text, ready to paste or pipe

    note_outline.py NOTE.md --context 60000 --decide
        one word, WHOLE or OUTLINE, for scripts and hooks

No index, no daemon, no network: it parses the markdown directly, so it cannot
go stale and works on any repo of markdown.

THE MODEL
---------
Prices are in units of the base input-token price. Under prompt caching a token
admitted to context is not paid for once, it is paid for on every later API call
in the session:

    write it once          1.25
    read it back           0.10  per later call
    lifetime of X tokens   X * (1.25 + 0.10 * T)  =  k * X    with T calls left

An extra round trip costs one more cache read of the whole prefix, 0.10 * P.
That is the entire penalty of the two-step, and it is 10% of the prefix, not
100% of it.

    read the whole note      C_whole   = k * F
    outline then maybe drill C_outline = k * H  +  p * (0.10 * P  +  k * S)

so the outline wins when the tokens it avoids beat the round trip it adds:

    F - H - p*S  >  0.10 * p * P / k

With H ~ 5% of F (measured across ~1500 headed notes) and S = F/N, that solves
to a break-even file size of

    F* = 0.10 * p * P / ( k * (1 - h - p/N) )

which for typical values lands near 2.5% of the current context size, near enough
to constant across two orders of magnitude of P. Batching M notes into one
outline call shares the single round trip between them, so the penalty term is
divided by M and the threshold collapses with it. That is why a search result set
should always come back as outlines.

The cost model prices tokens and says nothing about wall-clock. A round trip
costs a second or two no matter how small the note, so MIN_ROLLUP_TOKENS puts a
floor under the verdict that the arithmetic alone would not.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

# --- cost model constants, all overridable from the CLI ----------------------

CACHE_WRITE = 1.25      # price of writing a token into the cache
CACHE_READ = 0.10       # price of reading a cached token back, per API call
CHARS_PER_TOKEN = 3.6   # english markdown; a rough estimate is fine for a threshold

DEFAULT_TURNS = 10      # API calls the content is expected to sit in context for
DEFAULT_DRILL = 0.5     # P(the outline is not enough and a section is needed)
DEFAULT_BATCH = 1       # notes sharing one outline round trip
DEFAULT_CONTEXT = 60000 # fallback prefix size when the caller cannot measure it

MIN_ROLLUP_TOKENS = 800 # latency floor: never two-step a note smaller than this
MIN_SECTIONS = 2        # an outline with one entry routes nowhere

HEADING_RE = re.compile(r"^(#{2,6})\s+(.*)$")


def est_tokens(text: str) -> int:
    return int(len(text) / CHARS_PER_TOKEN)


# --- parsing -----------------------------------------------------------------


class Section:
    __slots__ = ("index", "heading", "level", "start_line", "end_line", "text")

    def __init__(self, index, heading, level, start_line):
        self.index = index
        self.heading = heading
        self.level = level
        self.start_line = start_line
        self.end_line = start_line
        self.text = ""

    @property
    def tokens(self) -> int:
        return est_tokens(self.text)


def parse(path: str):
    """Return (full_text, [Section]).

    Headings inside fenced code blocks are ignored, which a naive regex sweep
    gets wrong on any note that quotes a shell prompt or a markdown example.
    """
    with open(path, encoding="utf-8", errors="replace") as fh:
        text = fh.read()
    lines = text.splitlines()

    fenced = False
    marks = []  # (line_index, level, heading)
    for i, line in enumerate(lines):
        stripped = line.lstrip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            fenced = not fenced
            continue
        if fenced:
            continue
        m = HEADING_RE.match(line)
        if m:
            marks.append((i, len(m.group(1)), m.group(2).strip()))

    sections = []
    if not marks:
        s = Section(0, "(no headings)", 0, 1)
        s.end_line = max(len(lines), 1)
        s.text = text
        return text, [s]

    if marks[0][0] > 0:
        pre = Section(0, "(preamble)", 0, 1)
        pre.end_line = marks[0][0]
        pre.text = "\n".join(lines[: marks[0][0]])
        if pre.text.strip():
            sections.append(pre)

    for n, (line_i, level, heading) in enumerate(marks):
        nxt = marks[n + 1][0] if n + 1 < len(marks) else len(lines)
        s = Section(len(sections), heading, level, line_i + 1)
        s.end_line = nxt
        s.text = "\n".join(lines[line_i:nxt])
        sections.append(s)

    for n, s in enumerate(sections):
        s.index = n
    return text, sections


def outline_text(path: str, sections) -> str:
    """The tokens the model actually pays for in the outline step."""
    return os.path.basename(path) + "\n" + "\n".join(
        "#" * max(s.level, 2) + " " + s.heading for s in sections
    )


def render_outline(path: str, sections) -> str:
    """Human- and agent-readable outline with line ranges and sizes."""
    out = [
        "%3d  L%-6d %6d tok  %s%s"
        % (s.index, s.start_line, s.tokens, "  " * max(s.level - 2, 0), s.heading)
        for s in sections
    ]
    return "\n".join(out)


# --- the decision ------------------------------------------------------------


def decide(full_tokens, outline_tokens, n_sections, context,
           turns=DEFAULT_TURNS, drill=DEFAULT_DRILL, batch=DEFAULT_BATCH,
           window=None):
    """Price both paths. Returns a dict; 'verdict' is WHOLE or OUTLINE."""
    k = CACHE_WRITE + CACHE_READ * max(turns, 0)
    n = max(n_sections, 1)
    section_tokens = full_tokens / n

    # one round trip is shared by every note in the batch
    penalty = CACHE_READ * drill * context / max(batch, 1)

    cost_whole = k * full_tokens
    cost_outline = k * outline_tokens + drill * (penalty + k * section_tokens)
    saving = cost_whole - cost_outline

    # smallest note for which the outline path would still win, same assumptions
    h = outline_tokens / full_tokens if full_tokens else 0
    denom = 1.0 - h - drill / n
    break_even = (penalty / (k * denom)) if denom > 0 else float("inf")

    verdict = "OUTLINE" if saving > 0 else "WHOLE"
    reason = ("saves ~%d tok-equivalents" % saving if saving > 0
              else "round trip costs more than the note")

    # hard constraints and the latency floor override the arithmetic
    if window and context + full_tokens > window * 0.9:
        verdict, reason = "OUTLINE", "whole note does not fit the remaining window"
    elif n_sections < MIN_SECTIONS:
        verdict, reason = "WHOLE", "no usable headings to route on"
    elif full_tokens < MIN_ROLLUP_TOKENS:
        verdict, reason = "WHOLE", ("under the %d tok latency floor; a round trip "
                                    "costs more wall-clock than the note costs tokens"
                                    % MIN_ROLLUP_TOKENS)

    return {
        "verdict": verdict,
        "reason": reason,
        "full_tokens": int(full_tokens),
        "outline_tokens": int(outline_tokens),
        "sections": n_sections,
        "break_even_tokens": int(break_even) if break_even != float("inf") else None,
        "cost_whole": round(cost_whole),
        "cost_outline": round(cost_outline),
        "saving": round(saving),
        "k": round(k, 2),
        "assumptions": {
            "context": int(context), "turns": turns,
            "drill_rate": drill, "batch": batch,
        },
    }


def analyse(path, context, turns=DEFAULT_TURNS, drill=DEFAULT_DRILL,
            batch=DEFAULT_BATCH, window=None):
    """parse + price in one call, for importers such as the PreToolUse hook."""
    text, sections = parse(path)
    real = [s for s in sections if s.level >= 2]
    result = decide(est_tokens(text), est_tokens(outline_text(path, sections)),
                    len(real), context, turns, drill, batch, window)
    return result, sections


# --- CLI ---------------------------------------------------------------------


def main(argv=None):
    ap = argparse.ArgumentParser(
        prog="note_outline.py",
        description="Decide between an outline read and a whole-file read, and serve either.",
    )
    ap.add_argument("note", help="path to a markdown file")
    ap.add_argument("--context", type=int, default=None,
                    help="tokens already in the conversation (prefix size P). "
                         "Defaults to $CLAUDE_CONTEXT_TOKENS then %d." % DEFAULT_CONTEXT)
    ap.add_argument("--turns", type=int, default=DEFAULT_TURNS,
                    help="API calls the content will sit in context for (default %d)" % DEFAULT_TURNS)
    ap.add_argument("--hit-rate", type=float, default=None, metavar="P",
                    help="probability the outline alone answers the question "
                         "(default %.2f); drill rate is 1 minus this" % (1 - DEFAULT_DRILL))
    ap.add_argument("--batch", type=int, default=DEFAULT_BATCH,
                    help="notes sharing one outline round trip (default 1)")
    ap.add_argument("--window", type=int, default=None,
                    help="model context window, to catch notes that cannot fit")
    ap.add_argument("--section-n", type=int, default=None, metavar="N",
                    help="print only section N's text and exit")
    ap.add_argument("--section", default=None, metavar="TEXT",
                    help="print only the section whose heading contains TEXT")
    ap.add_argument("--decide", action="store_true",
                    help="print one word, WHOLE or OUTLINE, and exit")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    args = ap.parse_args(argv)

    if not os.path.isfile(args.note):
        sys.stderr.write("no such file: %s\n" % args.note)
        return 2

    text, sections = parse(args.note)

    # serving a single section needs no cost model
    if args.section_n is not None or args.section:
        if args.section_n is not None:
            if not 0 <= args.section_n < len(sections):
                sys.stderr.write("section %d out of range 0..%d\n"
                                 % (args.section_n, len(sections) - 1))
                return 2
            picked = [sections[args.section_n]]
        else:
            needle = args.section.lower()
            picked = [s for s in sections if needle in s.heading.lower()]
            if not picked:
                sys.stderr.write("no heading contains %r\n" % args.section)
                return 2
        for s in picked:
            sys.stdout.write("%s:%d-%d\n%s\n" % (args.note, s.start_line, s.end_line, s.text))
        return 0

    context = args.context
    if context is None:
        context = int(os.environ.get("CLAUDE_CONTEXT_TOKENS") or DEFAULT_CONTEXT)
    drill = DEFAULT_DRILL if args.hit_rate is None else max(0.0, 1.0 - args.hit_rate)

    real = [s for s in sections if s.level >= 2]
    result = decide(est_tokens(text), est_tokens(outline_text(args.note, sections)),
                    len(real), context, args.turns, drill, args.batch, args.window)

    if args.decide:
        sys.stdout.write(result["verdict"] + "\n")
        return 0
    if args.json:
        result["outline"] = [
            {"n": s.index, "heading": s.heading, "level": s.level,
             "start_line": s.start_line, "end_line": s.end_line, "tokens": s.tokens}
            for s in sections
        ]
        json.dump(result, sys.stdout, indent=2)
        sys.stdout.write("\n")
        return 0

    be = result["break_even_tokens"]
    sys.stdout.write("%s\n" % os.path.basename(args.note))
    sys.stdout.write(
        "%d tok, %d sections, outline %d tok (%.1f%%)\n"
        % (result["full_tokens"], result["sections"], result["outline_tokens"],
           100.0 * result["outline_tokens"] / max(result["full_tokens"], 1))
    )
    sys.stdout.write(
        "verdict %s: %s (break-even at %s tok, context %d, batch %d)\n\n"
        % (result["verdict"], result["reason"],
           be if be is not None else "n/a", context, args.batch)
    )
    sys.stdout.write(render_outline(args.note, sections) + "\n")
    sys.stdout.write("\nread one: note_outline.py %s --section-n N\n" % json.dumps(args.note))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
