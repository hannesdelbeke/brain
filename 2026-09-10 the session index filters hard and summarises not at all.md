---
date: 2026-09-10
tags:
  - technical
  - search
  - pkm
  - sessions
---
Agent session transcripts get into the index by being cut down, not by being summarised. Those are two different things and only one of them is built, which is worth writing down because the filtering is so aggressive that it reads like summarisation from the outside. Part of [[pkm-search]].

## What gets dropped, and what it costs

`index_sessions.py` throws away most of a transcript before anything is embedded:

- **Tool results, entirely.** They hold the API keys and the file dumps, and whatever they read is still on disk and searchable in place.
- **Thinking blocks, entirely.**
- **Prose under 30 characters**, or 10 for a user turn, plus a synthetic-prose regex. "yes", "continue" and "do it" cost a vector and return nothing.
- **Most tool arguments.** Tool calls survive, but only ten whitelisted keys — `description`, `command`, `file_path`, `notebook_path`, `path`, `pattern`, `query`, `url`, `prompt`, `subagent_type` — each truncated at 300 characters. `old_string` and its friends would paste whole files back into the index for nothing.

The whitelist is the part worth copying elsewhere. It inverts the usual instinct: rather than listing what to strip, which fails silently the first time a new tool ships a fat argument, it lists the handful of fields that make "which session ran that migration" answerable and drops everything else by default.

Measured over 11 transcripts, 43.1 MB on disk:

| block type | count | MB | share |
| --- | --- | --- | --- |
| tool_result | 1382 | 17.15 | 88.2% |
| thinking | 720 | 1.19 | 6.1% |
| tool_use | 1383 | 0.77 | 4.0% |
| text | 439 | 0.33 | 1.7% |

94.3% of the corpus by size goes before indexing starts, and that is before the whitelist trims the surviving 4% of tool calls. The docstring's own figure, 1.49 GB down to about 95 MB, is 93.6%, so the ratio holds across corpus sizes and is not an artefact of a small sample. Prose — the thing a person would call the content of a session — is under 2% of what a transcript actually weighs.

Dropping tool results and thinking is a settled decision rather than an oversight, and the reasoning is in the module docstring: four fifths of the corpus by size, redundant with the working tree, and where the secrets are.

## There is no rollup, anywhere

Neither layer of the index is generative. Nothing calls a model to say what a document is about.

- A **note's** `summary_snippet` comes from `extract_key_lines()`: the first 15 lines that start with `#`, `- `, or a checkbox, each truncated at 200 characters. Extractive, zero API cost, and it works because notes carry headings and bullets that are already a skeleton of the argument.
- A **session's** snippet is the first user message, truncated to 240 characters. Its title is the same message at 80 characters, or the subagent's `description` when one exists.

So the digest layer, the one that prints a line per document straight from the index, tells you what each session was *asked to do* and never what happened. A four-hour session that pivoted three times is represented by its opening sentence. A session whose first message was "continue" is represented by nothing at all, since the snippet takes the first user turn that clears the length floor.

This does not hurt search. Retrieval runs on chunk-level embeddings over the body, so the turn where the thing actually got decided is indexed and findable on its own terms. What it hurts is every use that reads the index instead of searching it: the digest, "what did I work on last week", any attempt to roll sessions up into a day log without opening all of them.

## Why the existing argument against rollup does not settle this

There is a good standing argument against building a rollup tier over a *repo catalog*: a few hundred summaries fit in one context, so the reduce can run on demand over whatever a query returned, and a precomputed tree caches an answer nobody asked for and invalidates on every push. See [[map rollup]] for the general shape.

That argument turns on two properties sessions do not share. Repo summaries are small, bounded and change only when someone pushes. Sessions are append-only, unbounded, and grow monotonically — the corpus only ever gets bigger, and a transcript is finished the moment its session ends, so a summary of a closed session never invalidates. That is close to the ideal case for precomputation and the opposite of the catalog's.

The counter-argument that does apply is cost: a generative summary per session is the first thing in this whole pipeline to need a model call at index time, and everything else here was built to avoid exactly that. The honest framing is that session rollup is unbuilt because it would be the first paid layer, not because the catalog's reasoning covers it. Whether it earns the cost depends on whether anything actually reads the digest, which on current evidence is nothing.

The cheap middle option, if it ever matters, is extractive rather than generative: take the **last** substantive assistant turn alongside the first user message. A session's closing turn is usually a summary of what happened, written for free by the agent at the time, and it costs one more field on a row that is already being written.

## Checking it yourself

There is no session row in an index until `index_sessions.py --root ~/.claude/projects` has run against it; a vault index built from notes alone holds notes alone, and sessions are a separate [[corpus]] that a daemon mounts by name. Worth confirming before concluding the session index is missing something, since an empty session corpus and a badly summarised one look identical from the query side.
