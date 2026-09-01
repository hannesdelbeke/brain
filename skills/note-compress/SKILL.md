---
name: note-compress
description: Compress agent-read-only vault notes in place, one cheap LLM call per note, gated by a free mechanical fidelity check.
aliases:
  - note-compress
  - note compression skill
created: 2026-09-01
tags:
  - technical
  - pkm
  - skill
  - compression
---

Compresses eligible vault notes' bodies in place using one LLM call, then verifies the result with a free mechanical fidelity check before writing anything. Full research and design rationale: [[2026-09-01 note-compress skill - design, adversarial review, and bench data]].

## What it does
- Finds notes eligible for compression: at least `--min-words` long AND (under a `learnings/`-style folder, OR at least `--min-backlinks` inbound wikilinks per the vault's own pkm-metadata-indexer `edges` table)
- Strips decorative emoji from headings and bullets first, mechanically, for free — a regex scoped to those lines and blind to fenced code, not an LLM call, because asking the model to do this itself was measured to bleed into rewriting fenced ASCII-art diagrams it was separately told never to touch
- Sends each note's body to Groq (free) or Gemini Flash with a classify-and-cut prompt: keep facts/numbers/decisions/links/code/hedges, cut connective filler and stacked near-synonym adjectives
- Extracts wikilinks, URLs, dates, numbers, and code spans from the original and the compressed text and rejects (keeps the original untouched) if anything essential is missing — no second LLM call needed for this check
- Skips unchanged notes via body content MD5 hashing (`compress-hash` frontmatter field)
- Dry-run by default — rewriting a note's body is riskier than adding frontmatter, so `--apply` is required to actually write

## How to run
```bash
python skills/note-compress/compress_notes.py --dry-run --sample 5
python skills/note-compress/compress_notes.py --apply --folder learnings/
python skills/note-compress/compress_notes.py --self-check
```

### Options
- `--apply` — actually rewrite notes (omit for a dry run, which is the default)
- `--sample 10` — process N random eligible notes
- `--folder learnings/` — restrict to a subfolder; also makes every note in it eligible, bypassing the backlink/`learnings/` filter
- `--min-words 300` — minimum body length to be eligible (default 300)
- `--min-backlinks 3` — minimum inbound wikilink count to be eligible outside `--folder` (default 3)
- `--db path.db` — pkm index db for backlink counts (default `<vault>/.obsidian/pkm_index.db`)
- `--workers 4` — parallel worker threads
- `--model name` — override the default model for the detected provider
- `--report path.json` — write a JSON bench report (per-note before/after word counts, cut %, gate verdict)
- `--self-check` — run the built-in fidelity-gate self-test, no API key or vault needed

### Setup & Providers

#### 1. Groq API (recommended, free)
```bash
export GROQ_API_KEY="your-groq-api-key"
python skills/note-compress/compress_notes.py --sample 5
```
Model: `openai/gpt-oss-20b` by default. This is a reasoning-style model — the script retries automatically if a call comes back with empty `content` (it sometimes spends the whole completion on hidden reasoning and returns nothing usable; that's a retryable flake, not a real failure).

#### 2. Gemini API
```bash
export GEMINI_API_KEY="your-gemini-api-key"
python skills/note-compress/compress_notes.py --sample 5 --model gemini-2.5-flash
```

## Frontmatter fields written (with `--apply`)

| Field | Type | Purpose |
| :--- | :--- | :--- |
| `compressed` | bool | Marks the note as having been through this skill |
| `compress-hash` | string | Truncated MD5 of the body at compression time, for incremental skip |
| `compress-cut-pct` | float | Word-count reduction achieved |

## Design decisions

- **One LLM call, not two.** The vault's own prior research measured a two-pass classify-then-adversarially-score design (31-40% cut, 85-98/100 retention). Across every compression measured against this vault's real notes, the only failure class was framing/hedge drift — never a lost fact, number, link, or code identifier. A program can catch the second class for free; it can't judge the first without another model call. So this skill spends its budget on one call plus a free mechanical gate, instead of two paid calls.
- **Eligibility, not "compress everything."** A compression pass only pays for itself after enough future rereads recoup the cost of the call that produced it — and external research on compression backfiring (see the research note) confirms an unconditional compress-every-note policy can lose more than it saves. Eligibility uses the vault's own existing wikilink-backlink graph as a free reread-frequency proxy, rather than tracking anything new.
- **Dry-run by default.** Rewriting a note body is harder to undo than adding a frontmatter field (`notes-sentiment-analysis`'s own default); `--apply` is opt-in.
- **Rejects rather than best-effort.** If the fidelity gate finds anything missing, the original file is left untouched and the note is reported as rejected — never a partial or "close enough" write.

## Related
- [[2026-09-01 note-compress skill - design, adversarial review, and bench data]] — full design rationale, adversarial for/against case, and measured bench numbers
- [[2026-08-31 research on compressing llm reasoning and notes without losing information]] — the research survey this skill implements
- [[2026-08-31 classifier-based compression with an adversarial fidelity gate]] — the two-pass method this skill deliberately simplifies to one call
- [[skills/notes-sentiment-analysis/SKILL|notes-sentiment-analysis]] — the architecture template this skill follows (provider selection, content hashing, CLI conventions)
