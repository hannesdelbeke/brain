---
tags:
  - ai-generated
---
## The official Obsidian CLI (v1.12, 2026)
Obsidian shipped an **official CLI** in v1.12 (early access 2026-02-10, GA in v1.12.4 2026-02-27, ~100+ commands). It is **not** a file-scraper — it connects to a **running Obsidian instance over IPC**, so it reads the app's live link graph and metadata cache, not just raw text.
### Relevant commands (all support `format=json`)
- `obsidian backlinks file="…"` — linked backlinks (`counts`, `total`, `path=` too)
- `obsidian links file="…"` — outgoing links
- `obsidian search query="…"` — full-text; `path=` scoping, `limit=`, `matches` for context; JSON/TSV/CSV
- `obsidian unresolved`, `obsidian orphans` — graph health
- `obsidian eval "…"` — arbitrary JS against `app.vault` / `app.metadataCache` (escape hatch for anything without a first-class command)

This resolves the earlier worry: the agent can pull the **same graph the UI renders**.

## Unlinked mentions specifically
There is still **no first-class `unlinked-mentions` command** — `backlinks` returns *linked* only. But it's a derived set:

```
unlinked mentions of X  =  search(X)  −  backlinks(X)
```

```bash
obsidian search query="TASK-10" format=json > all.json      # every occurrence
obsidian backlinks file="task-10 - Add core search..." format=json > linked.json
# files in all.json not present in linked.json = the unlinked mentions
```

Occurrence-level nuance: one file can hold both a link *and* a bare mention; file-level subtraction is usually enough, or drop to `obsidian eval` to hit the internal API for exact UI parity.

> [!caution] The CLI needs the app **running** (IPC). For headless/CI with no GUI, fall back to `ripgrep` over the `.md` files — `search − linked` still works because a wikilink is just literal `[[…]]` text. rg over 4k notes is instant; you only lose the live cache.

## The 4k-note scaling problem — the real point

Rule: **query, don't ingest.** Never read the vault into context. Treat it as a service you retrieve small answers from. Search happens *outside* the model and returns bounded results.

Tactics, cheapest first:

1. **Metadata is small; bodies are huge — separate them.** 4k titles + aliases + tags + link edges is tens of KB and fits fine; 4k bodies don't. Load a compact catalog once (`obsidian files`, `obsidian tags`, or an `eval` dumping `metadataCache` to JSON); treat bodies as fetch-on-demand.

2. **Locate → then read (two-tier retrieval).** Step 1: `search`/`backlinks` returns *paths + snippets* (cheap). Step 2: read full text of only the top few that matter. Use `total`/`counts` to size a result set before pulling bodies.

3. **Scope every query.** `path="Projects"`, tag filters, frontmatter queries (`query="status::active"`), `limit=`, `matches` (surrounding lines, not whole files). Never `read` where you can `search`.

4. **Prefer short, high-signal identifiers.** For unlinked mentions this is why aliases matter: `TASK-10` returns a precise, bounded set; the long title returns noise. Small query → small output → small context.

5. **Semantic layer for "related but not string-matching."** Exact search misses a note titled "core search" when you look for "the search feature." An embeddings index (Smart Connections plugin, or an external vector store built from the files) retrieves **top-k by meaning** — pull 5 notes, not 4000. This scales conceptual recall without dumping the vault.

**Mental model:** the agent shouldn't *hold* the vault — it should hold a **cheap index (metadata + a vector store)** and use the CLI/ripgrep as its query engine, pulling full note bodies only for the few notes a task actually touches. Strictly more scalable than the human UI, which shows one note's panel at a time anyway.

## Sources
- [Obsidian CLI (obsidian.md/cli)](https://obsidian.md/cli)
- [Obsidian CLI help docs](https://obsidian.md/help/cli)
- [kepano/obsidian-skills — CLI commands & syntax](https://github.com/kepano/obsidian-skills/blob/main/skills/obsidian-cli/SKILL.md)
- [Obsidian's Official CLI Is Here (DEV)](https://dev.to/shimo4228/obsidians-official-cli-is-here-no-more-hacking-your-vault-from-the-back-door-3123)
