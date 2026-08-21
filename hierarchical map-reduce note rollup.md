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

**2. Lexicographical Date Naming**
Prefix rollup filenames with the ISO period (e.g. `2024-06 rollup.md` or `review 2024-06.md`). This guarantees natural chronological sorting across all file explorers, CLI tools, and vault views.

**3. Sequential Ingestion for Causal Integrity**
During the Map phase, feed daily notes to the model in strict ascending chronological order (`YYYY-MM-DD`). Preserving sequential input prevents the LLM from confusing cause and effect (e.g. attributing a mood drop to an event that happened days later).

**4. Git Source Commit Anchoring**
Record the historical commit range or snapshot SHA in frontmatter (`source_range: "a1b2c3..d4e5f6"`). This links the summary directly to the exact point-in-time state of the vault without modifying historical Git commits.

### Related
- [[moving files loses created date]] — Why filesystem and Git timestamps drift and why frontmatter is the permanent source of truth.
- [[wikilink temporal integrity]] — Preserving link validity across chronological revisions.
- [[token efficient PKM analysis architecture]] — Overview of vault retrieval and batch analysis economics.