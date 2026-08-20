---
tags:
  - pkm
  - ai
  - obsidian
  - review
---
Review of [eugeniughelbur/obsidian-second-brain](https://github.com/eugeniughelbur/obsidian-second-brain), a suite of 45+ CLI slash commands that connects [[AI agent|AI agents]] to an [[Obsidian vault]] as autonomous long-term memory.

### concept
Extends Karpathy's LLM Wiki idea into an autonomous, self-rewriting vault. Rather than append-only logs, agents ingest media (YouTube, X, audio via [[Whisper]], whiteboard photos) and autonomously update existing entity notes, reconcile contradictions, and rebuild indexes via background cron jobs.

### pros
- Solves cross-session amnesia by grounding CLI agents in persistent [[Markdown]] files.
- Reconciles new info into existing concept notes instead of creating duplicate notes.
- Portable plain text format across multiple CLI harnesses (Claude Code, Antigravity, OpenCode, Codex).

### concerns & pitfalls
- **Vault pollution:** Unsupervised self-rewriting and nightly auto-merges risk hallucinated edits or homogenized writing.
- **Loss of spatial familiarity:** You lose track of what you wrote vs what an automated agent generated overnight.
- **Token & API cost:** Continuous ingestion and full-vault reconciliation eat heavy context tokens and API spend.
- **Command bloat:** 45 separate commands is overwhelming when most workflows only need quick recall, capture, and Git backups.
- **Fragile scraper stack:** Depends on volatile third-party scrapers (YouTube transcript API, Grok/X, Perplexity, ffmpeg) that break on API changes.
- **Privacy risk:** Multi-agent search pipelines across private notes can expose sensitive personal data to external APIs.

### verdict
Good source of architectural ideas, but don't install the full automated suite. Cherry-pick specific capture prompts or standalone scripts (e.g. [[public/offline GPU embeddings with incremental cache|local GPU vector cache]]) while keeping note edits under human review.

### References
- [[public/offline GPU embeddings with incremental cache]] — lightweight local embedding alternative without API dependencies.
- [[agentic note taking]] — patterns for agent-assisted note generation.
- [[differentiate between AI and human notes]] — preserving authorship attribution in hybrid vaults.

[[agentic note taking]]