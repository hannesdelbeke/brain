#!/usr/bin/env python3
"""PreToolUse hook: intercept a whole-file Read of a large headed note.

When an agent asks to Read a markdown note that the break-even model says should
be routed through its outline first, this returns the outline instead, plus the
one command that fetches any single section. The agent spends ~5% of the note's
tokens and only pays for the section it actually needs.

Wire it up in .claude/settings.json:

    {"hooks": {"PreToolUse": [{"matcher": "Read", "hooks": [{
        "type": "command",
        "command": "~/.venvs/pkm-indexer/bin/python /path/to/outline_gate.py"
    }]}]}}

Design rules, in priority order:

  fail open      any exception, any unreadable transcript, any parse problem
                 exits 0 with no output, and the Read proceeds untouched. A
                 cost optimisation must never be able to block a file read.
  never guess P  the prefix size comes from the transcript's own usage blocks,
                 not from a constant. If it cannot be measured, the hook does
                 nothing, because at small P the whole-file read is correct
                 anyway and a wrong guess would block reads that should happen.
  stay out of the way
                 an explicit offset/limit means the caller has already decided
                 how much to read. Non-markdown, small, and heading-less files
                 are passed through.

Kill switch: export PKM_OUTLINE_GATE=0
"""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Below this prefix size the round trip never pays for itself on any note this
# vault contains, so the hook stays silent rather than measuring every read.
MIN_CONTEXT = 20000

# Tuned for retrieval reads: the agent is mid-task, so the note will sit in
# context for a while, and one section usually answers the question.
TURNS = 10
DRILL = 0.4


def prefix_tokens(transcript_path: str) -> int:
    """True P: the total input the last API call actually billed for.

    Every assistant turn records its own usage. The most recent one is the best
    available estimate of what the *next* call will re-send, which is exactly
    the quantity the round-trip penalty is charged against.
    """
    if not transcript_path or not os.path.isfile(transcript_path):
        return 0
    last = 0
    with open(transcript_path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            line = line.strip()
            if not line or '"usage"' not in line:
                continue
            try:
                rec = json.loads(line)
            except ValueError:
                continue
            usage = (rec.get("message") or {}).get("usage") or rec.get("usage")
            if not isinstance(usage, dict):
                continue
            total = (
                usage.get("input_tokens", 0)
                + usage.get("cache_read_input_tokens", 0)
                + usage.get("cache_creation_input_tokens", 0)
            )
            if total:
                last = total
    return last


def main() -> int:
    if os.environ.get("PKM_OUTLINE_GATE") == "0":
        return 0

    try:
        payload = json.load(sys.stdin)
    except Exception:
        return 0

    tool_input = payload.get("tool_input") or {}
    path = tool_input.get("file_path") or ""

    # the caller already scoped the read; leave it alone
    if tool_input.get("offset") or tool_input.get("limit"):
        return 0
    if not path.endswith(".md") or not os.path.isfile(path):
        return 0

    context = prefix_tokens(payload.get("transcript_path") or "")
    if context < MIN_CONTEXT:
        return 0

    from note_outline import analyse, render_outline

    result, sections = analyse(path, context, turns=TURNS, drill=DRILL)
    if result["verdict"] != "OUTLINE":
        return 0

    tool = "%s %s" % (
        sys.executable,
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "note_outline.py"),
    )
    reason = (
        "Read blocked by outline_gate: this note is %d tokens and the outline is "
        "%d (%.0f%%). At the current context of ~%d tokens the break-even is %s "
        "tokens, so reading the whole file costs more than routing through the "
        "outline. The outline is below; read one section, or re-Read with an "
        "explicit offset/limit to override.\n\n%s\n\n"
        "one section:  %s %s --section-n N\n"
        "by heading:   %s %s --section \"text\"\n"
        "read anyway:  set offset/limit, or PKM_OUTLINE_GATE=0"
        % (
            result["full_tokens"], result["outline_tokens"],
            100.0 * result["outline_tokens"] / max(result["full_tokens"], 1),
            context, result["break_even_tokens"],
            render_outline(path, sections),
            tool, json.dumps(path), tool, json.dumps(path),
        )
    )

    json.dump({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }, sys.stdout)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        # fail open, always
        sys.exit(0)
