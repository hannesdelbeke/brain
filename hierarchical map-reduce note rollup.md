---
tags:
  - ai
  - pkm
  - optimization
  - solved
---
A batch compression pattern based on [[map-reduce]] for recursively synthesizing thousands of [[daily notes]] into cached monthly and multi-year overviews with bounded LLM API usage.

> [!summary] Conclusion
> **Not needed as designed.** The current vault (3,228 notes, 6,550 sections) is handled by local search and flat SQLite metadata indexing via the [[pkm metadata indexer]]. Measured against that index the recursive hierarchy has no level to insert and no time axis to group by; what is worth building is the leaf layer alone. See the Answer section below.

## Answer

The open question is whether to build the recursive hierarchy for this vault and on what unit. Do not build it. Build the leaf layer only, store it in the existing index keyed to the section sha256 that is already there, and run the reduce on demand instead of materialising rollup nodes.

Measured on 2026-08-25 from `--stats` and a pass over the vault root: 3,228 notes, 6,550 sections, 9,256 link edges, 425,987 body words, 3.4 MB of Markdown, roughly 850k tokens raw with frontmatter included. Filename, tags, headings and the `summary_snippet` already sitting in the `notes` table serialise to 720 KB for the entire vault, about 180k tokens, at zero API cost. That fits in one call on any current model. There is no intermediate level to insert, because a reducer with a 1M-token context takes the whole leaf layer as a single batch.

That 720 KB / 180k-token estimate assumed `summary_snippet` was the first 133 characters of a note. It isn't: `extract_key_lines` keeps up to 15 heading and bullet lines per note, each capped at 200 characters, so it's a small multi-line outline, not a one-line snippet. Built and measured for real via the `--digest` flag added below: the whole-vault digest is 1,032,591 characters, about 258k tokens, still one call on any current model, just further from the raw 850k than the estimate claimed (2.6:1, not 4.7:1) and not the 2k-per-tag figure below either.

The time axis does not exist in the note metadata. 18 notes carry a `created` field, 10 carry `date`, 35 have a date-prefixed filename. This is a vault of atomic topic notes, not [[daily notes]], so a monthly rollup has almost nothing to group by frontmatter. Git commit history is a time axis every file has regardless of frontmatter, and this vault's git history runs back to 2024-03-21, but nothing here reduces over it — no day-log or activity-capture layer exists in this vault to serve as the leaf for a time-based rollup. That's a real gap, not a case for building the recursion on its own though: it only becomes worth reducing over once something produces per-period leaves to group, and nothing measured here says whether that's worth building at all. The units that do exist today are tags (396 distinct, 22 of them covering 20 or more notes, `technical` covering 1,944) and the link graph (9,256 edges). Scope a reduce by tag, by a [[vault hybrid search]] result set, or by a link neighbourhood.

## A Recurring Reduce, If a Time-Based Leaf Layer Ever Exists

If this vault ever grows a per-period leaf layer (a daily or weekly capture note, however it's produced), rolling it up over time would look like the same pattern as the tag/link reduce above, one level added:

**trigger:** on demand ("what happened in August"), not scheduled. Matches the "regenerate on read" principle below.

**map:** the per-period leaf itself — already condensed if the capture layer is doing its job, so a month's worth of it is a few thousand tokens, not raw source material.

**reduce:** group leaves by month, one call over that month's worth, output a month rollup. Month rollups group the same way into a year rollup. This is the one shape where the recursion in this note would actually earn its keep, because there's a real hierarchy (period → month → year) instead of a flat note set.

**invalidation:** same pattern as the `sections.sha256` approach below, one level up — store the month rollup beside a hash of the period-leaves it was built from. Stale exactly when a leaf inside the month changes or a new one is added.

**cost:** trivial and infrequent, same shape as the whole-vault digest reduce above — a month of already-condensed leaves is a few thousand tokens in, a few hundred out, paid once when someone asks for that month or year.

None of this is built here; it's the design to reach for only once a time-based leaf layer exists to reduce over.

Regenerate on read, not on write. Writes happen daily; whole-vault syntheses happen a few times a year. A materialised `technical` rollup spans 1,944 notes, costs about $0.24 to regenerate on Sonnet 5, and is invalidated by an edit to any one of those 1,944 notes, so a maintained tree pays that repeatedly for an artifact nobody read. On demand the same reduce costs the same $0.24, once, when someone asks. The maintained tree also has to live outside the vault under the artifact rules above, which removes the only thing it was good for, being browsable in Obsidian. It loses on cost and on the one benefit it had.

Invalidation needs no DAG and no run manifest. `sections.sha256` is recomputed on every index run. Store the summary beside it with the hash it was generated from; a summary is stale exactly when `summary_sha != sha256`. Renamed and deleted notes fall out on their own because their section rows do.

```sql
ALTER TABLE sections ADD COLUMN summary TEXT;
ALTER TABLE sections ADD COLUMN summary_sha TEXT;
ALTER TABLE sections ADD COLUMN summary_model TEXT;
-- work queue for one incremental pass; IS NOT is null-safe, so an
-- unsummarised row and a changed row are the same case
SELECT id, path, heading FROM sections WHERE summary_sha IS NOT sha256;
```

Cost of an LLM leaf pass, if the free digest in step 1 turns out too thin: 6,550 sections grouped one call per note is 3,228 calls, roughly 1.0M input and 260k output tokens, about $2.30 on Haiku 4.5 at $1/$5 per MTok, or $1.15 through the Batch API at its 50% discount. An incremental run is the changed sections only, around $0.0005 each, so a normal editing day costs under a cent. A reduce over the leaf layer is a 200k-token input: $0.20 on Haiku 4.5, $0.40 on Sonnet 5, $1.00 on Opus 5.

## Plan

1. Zero-cost digest first. Done — `--digest` on [[index_pkm_meta.py]] prints one line per note straight out of the DB: path, tags, headings, `summary_snippet`. No API key, no schema change. The whole vault measures 258k tokens, not the 180k estimated above; a tag scope like `pkm` measures 51k, not the 2k estimated, because `summary_snippet` is up to 15 heading/bullet lines per note, not a 133-character snippet.
   `python skills/pkm-metadata-indexer/index_pkm_meta.py --digest --tag pkm`
2. Ask the actual synthesis questions against that digest and see what breaks. The snippet is up to 15 heading and bullet lines, not full prose, so the likely failure is notes whose headings and bullets don't cover the claim being asked about.
3. Only if step 2 fails, add the three `sections` columns above and a `--summarize` pass over the stale-row query, with `--limit` so the first run costs cents rather than $2.30. One call per note, output capped at about 80 tokens, Batch API for the cold pass.
4. Call `--summarize` at the end of a normal index run, after embedding, driven by the same `summary_sha != sha256` test. A summary then cannot outlive the text it came from.
5. Serve it as `GET /digest?vault=brain&tag=pkm` on the existing daemon alongside `/search` and `/links`. The reduce itself stays in the agent's context; nothing is written back into the vault.
6. Reach for the recursion in the pipeline above only when a single scope stops fitting the reducer's context, which needs roughly a 5x larger vault. It is the fallback, not the design.

## When to Build It

Start lazy. A flat, searchable leaf index may be sufficient: one short summary and structured metadata per note is small enough for local search even when it is too large to read in one model context (see [[agentic tooling upgrades over grep]]). Measured on this vault that leaf layer is about 180k tokens, which does fit one model context, so the "too large to read" case has not arrived. 
Build the recursive hierarchy only when a human needs top-down navigation or a parent node must fit in a model context.

## The Context Window Problem

Feeding 10,000+ raw [[Markdown]] files directly into an [[large language model|LLM]] [[session context|context window]] spends tokens on repeated formatting and low-signal material. Compression is useful only if the resulting artifacts retain provenance, chronology, and unresolved conflicts, preventing runaway [[vault graph complexity]].

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
3. **Hierarchical reduce:** Group leaves deterministically by time, folder, project, or a deliberately chosen link cluster. Bound the fan-in by the reducer's context window rather than by a fixed count; a fixed 40 is a leftover from 8k-context models. At a 1M-token context this vault's whole leaf layer is one batch and the recursion never fires. Recurse only when a scope does not fit, and preserve contradictory claims instead of averaging them into one story. Date windows can be monthly, but token limits and semantic boundaries should determine the actual batches.
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
  Future edits and updates then commit normally with current timestamps. This aligns [[git history|Git history]] queries (`git log --before="2024-07-01"`) without requiring a complex Git rebase.
- **Option B (Frontmatter Anchoring):** Record the source commit range in frontmatter (`source_range: "a1b2c3..d4e5f6"`). This links the summary directly to the exact point-in-time state of the vault without altering Git timestamps.
- **Best Practice:** Use frontmatter `period` as the permanent machine-readable source of truth (as Git timestamps can reset when moving files across submodules per [[moving files across submodules loses created date]]), and optionally backdate the initial Git author timestamp on creation.

> [!example]- Retrospective Notes: Writing a 2020 memory in 2025
> **The scenario:** In 2025, you author a note reflecting on a 2020 trip (`period: "2020-05"`, `created: 2025-06-12`).
> 
> **How the pipeline resolves it:**
> 1. **2020 Event Rollup (`rollup 2020-05.md`):** Routes the note to the 2020 timeline by `period`. It invalidates and regenerates `rollup 2020-05.md` to add the memory with a hindsight tag: *"Traveled to Malta (recorded retrospectively in 2025)"*.
> 2. **DAG Cache Protection:** Rollups for 2021, 2022, 2023, and 2024 remain cached and are untouched (0 token spend).
> 3. **2025 Authoring Rollup (`rollup 2025.md`):** Tracks the *act of remembering* as reflection activity: *"In mid-2025: Active journaling period reflecting on past 2020 life events."*
> 
> **Why this beats relying on raw [[git history|Git history]] alone:**
> - **Semantic synthesis vs raw text diffs:** Git only knows lines were added or deleted; it cannot detect emotional shifts, recurring themes, or summarize life arcs.
> - **Immunity to submodule moves:** Moving notes across folders or submodules resets Git creation dates (per [[moving files across submodules loses created date]]), whereas frontmatter `period` preserves the event era permanently.
> - **Token efficiency:** Reading 5 years of monthly rollups takes ~30k tokens; crawling 5 years of raw Git commit diffs takes millions of tokens and dozens of API roundtrips.

keep context from this note in mind when planning [[git history]]: 
- [[human vs AI git history transfers between notes]] — Rules for preserving author intent across notes.
- [[rewrite git history for ai authorship migration]] — Rewriting commit metadata when attributing generated summaries.
- [[algo to differentiate between AI and human notes]] — Classifying machine vs human authorship in historical commits.

### Related
- [[wikilink temporal integrity]] — Preserving link validity across chronological revisions.
- [[token efficient PKM analysis architecture]] — Overview of vault retrieval and batch analysis economics.
- [[vault synapse pruning]] — Managing link decay and graph density across aging notes.
- [[vault hybrid search]] — Combining lexical FTS5 and semantic retrieval.
- [[extract historic wikilinks from git]] — Reconstructing graph references from past commit states.