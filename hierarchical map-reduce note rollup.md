---
tags:
  - ai
  - pkm
  - optimization
---
A batch compression pattern based on [[map-reduce]] for synthesizing thousands of [[daily notes]] into inspectable monthly and multi-year overviews with bounded LLM API use.

## When to Build It

Start lazy. A flat, searchable leaf index may be sufficient: one short summary and structured metadata per note is small enough for local search even when it is too large to read in one model context. 
Build the recursive hierarchy only when a human needs top-down navigation or a parent node must fit in a model context.

## The Context Window Problem

Feeding 10,000+ raw [[Markdown]] files directly into an [[large language model|LLM]] [[session context|context window]] spends tokens on repeated formatting and low-signal material. Compression is useful only if the resulting artifacts retain provenance, chronology, and unresolved conflicts.

## Pipeline

```
notes/**/*.md
  | local parse, normalize, and index
  v
normalized records + FTS5 index
  | leaf map: structured extraction per note or semantic chunk
  v
leaf.jsonl
  | deterministic groups; bounded fan-in; recursive reduce
  v
monthly / project / cluster summaries
  | final synthesis with sources and limitations
  v
root map
```

1. **Local intake (no LLM):** Parse Markdown, YAML frontmatter, headings, links, and dates. Retain meaningful metadata rather than stripping all frontmatter. Remove only known boilerplate. Index the normalized text with SQLite / FTS5, but use FTS5 for retrieval and ranking rather than as the sole exclusion rule.
2. **Leaf map:** Produce one versioned JSONL artifact per note or semantic chunk. Keep a short human-readable summary plus typed fields for events, decisions, tasks, themes, entities, tags, outlinks, and open questions. Every extracted item must include a source path, heading or block reference, date, and uncertainty where relevant.
3. **Hierarchical reduce:** Group leaves deterministically by time, folder, project, or a deliberately chosen link cluster. Reduce at a bounded fan-in (for example, 40 inputs), recurse as needed, and preserve contradictory claims instead of averaging them into one story. Date windows can be monthly, but token limits and semantic boundaries should determine the actual batches.
4. **Root synthesis:** Give the final model structured intermediate artifacts, not detached prose alone. Require it to cite source notes, distinguish evidence from inference, retain unresolved questions, and state material gaps in coverage. Do not use it to diagnose health or psychological conditions or make unsupported causal claims.

## Artifact and Execution Rules

- Treat source references as part of the data contract. A reducer may summarize a claim only when it retains the relevant leaf or source-note references.
- Version the artifact schema, prompts, model identifier, and preprocessing rules. Cache each node by content hash plus those versions, checkpoint completed work, and invalidate only affected ancestors when a note changes.
- Write generated artifacts outside the source corpus, mark them as generated, and exclude them from ingestion. Handle deleted and renamed notes so stale summaries do not survive unnoticed.
- Use atomic writes, retryable jobs, rate-limit handling, and a run manifest. A failed run must be resumable without mixing partial artifacts with a completed hierarchy.
- Preserve manual edits separately from generated output, or make the generated section replaceable without overwriting human notes.

## Maintaining Chronology Across Rollups

When a rollup is generated months or years after the original notes (e.g. summarizing June 2024 notes in August 2026), its file system creation date and Git commit date reflect the generation day, not the event period. Preserving true chronological integrity requires four conventions:

**1. Explicit Event Time vs Generation Time**
Distinguish the historical period being summarized from the generation run in YAML frontmatter:
```yaml
period: "2024-06"
period_start: 2024-06-01
period_end: 2024-06-30
generated: 2026-08-21
```
Downstream search, Dataview queries, and temporal decay algorithms must sort by `period_start` rather than file creation or Git timestamps.

**2. Lexicographical Naming Convention**
Prefix rollup filenames with the standard schema (`rollup 2024-06.md` or `review 2024-06.md`). This guarantees natural chronological sorting across file explorers, Dataview tables, and CLI tools.

**3. Balancing Note Event Date vs Git Author Date**
Both dates carry distinct semantic meaning:
- **Event Date (`period` / title date):** Tells the AI what era of your life the note describes.
- **Commit Date (`GIT_AUTHOR_DATE`):** Tells the AI when the text was actually authored or modified.
- **Why both matter:** If you write about a 2020 memory in 2024, the event date provides historical placement, while the commit date proves you wrote it with four years of hindsight.
- In the Map phase, feed daily notes to the model in strict chronological order by event date, but preserve author timestamps in metadata to maintain hindsight context and causality.

**4. Backdating Initial Rollup Commits vs Frontmatter Anchoring**
Can we backdate the initial Git commit of a retrospective rollup to match the historical period?
- **Option A (Backdated Creation Commit):** Create the rollup file and commit it using a backdated author timestamp:
  `GIT_AUTHOR_DATE="2024-06-30 23:59:59" git commit -m "docs: generate rollup for 2024-06"`
  Future edits and updates then commit normally with current timestamps. This aligns Git history queries (`git log --before="2024-07-01"`) without requiring a complex Git rebase.
- **Option B (Frontmatter Anchoring):** Record the source commit range in frontmatter (`source_range: "a1b2c3..d4e5f6"`). This links the summary directly to the exact point-in-time state of the vault without altering Git timestamps.
- **Best Practice:** Use frontmatter `period` as the permanent machine-readable source of truth (as Git timestamps can reset when moving files across submodules per [[moving files loses created date]]), and optionally backdate the initial Git author timestamp on creation.

> [!example]- Retrospective Notes: Writing a 2020 memory in 2025
> **The scenario:** In 2025, you author a note reflecting on a 2020 trip (`period: "2020-05"`, `created: 2025-06-12`).
> 
> **How the pipeline resolves it:**
> 1. **2020 Event Rollup (`rollup 2020-05.md`):** Routes the note to the 2020 timeline by `period`. It invalidates and regenerates `rollup 2020-05.md` to add the memory with a hindsight tag: *"Traveled to Malta (recorded retrospectively in 2025)"*.
> 2. **DAG Cache Protection:** Rollups for 2021, 2022, 2023, and 2024 remain cached and are untouched (0 token spend).
> 3. **2025 Authoring Rollup (`rollup 2025.md`):** Tracks the *act of remembering* as reflection activity: *"In mid-2025: Active journaling period reflecting on past 2020 life events."*
> 
> **Why this beats relying on raw Git history alone:**
> - **Semantic synthesis vs raw text diffs:** Git only knows lines were added or deleted; it cannot detect emotional shifts, recurring themes, or summarize life arcs.
> - **Immunity to submodule moves:** Moving notes across folders or submodules resets Git creation dates (per [[moving files loses created date]]), whereas frontmatter `period` preserves the event era permanently.
> - **Token efficiency:** Reading 5 years of monthly rollups takes ~30k tokens; crawling 5 years of raw Git commit diffs takes millions of tokens and dozens of API roundtrips.

### Related
- [[moving files loses created date]] — Why filesystem and Git timestamps drift and why frontmatter is the permanent source of truth.
- [[wikilink temporal integrity]] — Preserving link validity across chronological revisions.
- [[token efficient PKM analysis architecture]] — Overview of vault retrieval and batch analysis economics.