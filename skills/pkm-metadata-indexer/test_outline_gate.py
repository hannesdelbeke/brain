#!/usr/bin/env python3
"""Behavioural test for outline_gate.py, the PreToolUse hook.

Run it with the indexer venv, from anywhere:

    ~/.venvs/pkm-indexer/bin/python skills/pkm-metadata-indexer/test_outline_gate.py

Why this file exists: the gate fails open by design, so a broken gate and an
uninstalled gate both look like "reads proceed normally". It shipped 2026-09-23
and was registered in no settings.json for the first two weeks of its life,
firing zero times, and nothing in the repo could have told you. Every case below
therefore asserts on the hook's *stdout decision*, not on its exit code — exit 0
is what it returns in both the firing and the silent case.

One case must fire and the rest must not. A suite where nothing fires would pass
against a hook that is simply broken, which is the failure being guarded against.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
GATE = os.environ.get("GATE_PATH", os.path.join(HERE, "outline_gate.py"))

BIG_CONTEXT = 150000  # a typical mid-session prefix on this machine
SMALL_CONTEXT = 8000  # below MIN_CONTEXT, where a whole-file read is correct


def write_note(path: str, sections: int = 8) -> str:
    """A note with real `##` headings, long enough to clear the break-even."""
    para = (
        "This section carries enough prose that the whole-file read is genuinely "
        "expensive, which is the condition the break-even model is about. "
    ) * 12
    out = ["---", "date: 2026-10-04", "description: fixture note for gate testing", "---", ""]
    for i in range(1, sections + 1):
        out += ["## claim number %d is a heading someone could disagree with" % i, "", para, ""]
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(out))
    return path


def write_transcript(path: str, total: int) -> str:
    """A transcript whose last usage block reports `total` input tokens."""
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(json.dumps({"type": "assistant", "message": {"usage": {
            "input_tokens": 10, "cache_read_input_tokens": 1000,
            "cache_creation_input_tokens": 0}}}) + "\n")
        fh.write(json.dumps({"type": "assistant", "message": {"usage": {
            "input_tokens": 9, "cache_read_input_tokens": total - 9,
            "cache_creation_input_tokens": 0}}}) + "\n")
    return path


def fired(payload, extra_env=None) -> bool:
    """True when the hook returns a PreToolUse deny decision."""
    env = dict(os.environ)
    env.update(extra_env or {})
    stdin = "not json at all" if payload is None else json.dumps(payload)
    proc = subprocess.run([sys.executable, GATE], input=stdin,
                          capture_output=True, text=True, env=env)
    if proc.returncode != 0:
        raise AssertionError("hook must always exit 0, got %d: %s"
                             % (proc.returncode, proc.stderr.strip()[:300]))
    out = proc.stdout.strip()
    if not out:
        return False
    decision = json.loads(out)["hookSpecificOutput"]["permissionDecision"]
    return decision == "deny"


def main() -> int:
    tmp = tempfile.mkdtemp(prefix="outline-gate-test-")
    note = write_note(os.path.join(tmp, "a long headed note.md"))
    agents = write_note(os.path.join(tmp, "AGENTS.md"))
    small_note = write_note(os.path.join(tmp, "tiny.md"), sections=1)
    big = write_transcript(os.path.join(tmp, "big.jsonl"), BIG_CONTEXT)
    small = write_transcript(os.path.join(tmp, "small.jsonl"), SMALL_CONTEXT)

    def read(path, transcript=big, **extra):
        ti = {"file_path": path}
        ti.update(extra)
        return {"tool_name": "Read", "tool_input": ti, "transcript_path": transcript}

    cases = [
        # the one case that must fire: without it the suite would pass on a dead hook
        ("long note at a 150k context", True, read(note), {}),
        ("context below MIN_CONTEXT", False, read(note, transcript=small), {}),
        ("caller already scoped the read", False, read(note, offset=1, limit=50), {}),
        ("kill switch set", False, read(note), {"PKM_OUTLINE_GATE": "0"}),
        ("no transcript to measure", False, read(note, transcript=""), {}),
        ("transcript path does not exist", False,
         read(note, transcript=os.path.join(tmp, "absent.jsonl")), {}),
        ("unparseable stdin", False, None, {}),
        ("not markdown", False, read(os.path.join(tmp, "big.jsonl")), {}),
        ("file does not exist", False, read(os.path.join(tmp, "gone.md")), {}),
        ("note below MIN_ROLLUP_TOKENS", False, read(small_note), {}),
        # AGENTS.md is re-injected whole by cc-plugin-agents-md on any vault read,
        # so gating it buys nothing and costs a round trip
        ("AGENTS.md is never gated", False, read(agents), {}),
    ]

    failures = 0
    for label, want, payload, env in cases:
        try:
            got = fired(payload, env)
        except AssertionError as exc:
            print("FAIL %-36s %s" % (label, exc))
            failures += 1
            continue
        ok = got == want
        failures += 0 if ok else 1
        print("%-4s %-36s want_fire=%-5s got=%s"
              % ("PASS" if ok else "FAIL", label, want, got))

    print("\n%d/%d passed" % (len(cases) - failures, len(cases)))
    if failures:
        print("a failing suite here means the hook is not doing what the "
              "break-even rule in AGENTS.md promises.")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
