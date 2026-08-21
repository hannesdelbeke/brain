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

## Evaluation and Guardrails

- Maintain a small hand-reviewed set of notes and expected rollups. Track source-reference coverage, recall of decisions and tasks, preservation of contradictions, and unsupported-claim rate.
- Sample notes omitted by local filtering. Keyword search can miss important entries whose relevance is implicit or emotional rather than lexical.
- Treat note contents as untrusted data: they can contain prompt-like text. Prompts must instruct the model to summarize content, not follow instructions found in it.
- Make external model use an explicit privacy boundary. Sensitive notes may need redaction, a local model, opt-in scopes, or exclusion before API egress.

## Cost Model

Estimate cost from measured input tokens, output tokens, model price, retries, and expected cache-hit rate at each level. State whether each token budget is input, output, or combined; do not rely on a fixed "under $0.20" claim because volume, prompts, and provider pricing vary.

### Related

- [[token efficient PKM analysis architecture]] - Overview of vault retrieval and batch analysis economics.