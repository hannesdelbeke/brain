---
tags:
  - ai
  - tools
  - cli
  - github
  - architecture
---
Comparing what modern coding assistants ([[Claude Code]], Gemini Flash in [[antigravity]]) handle out-of-the-box versus the missing gaps in cross-repository search.

## What Agents Do Today (Single-Repo)

Within a single workspace directory, modern CLI agents already implement several token-saving retrieval patterns:
- **Subagent delegation:** [[antigravity]] and [[Claude Code]] can invoke lightweight background subagents (using `flash` or `haiku`) to run targeted search passes while the main reasoning model plans.
- **Tool-based slicing:** Agents use ripgrep and targeted slice readers (`view_file` with line ranges) rather than loading entire repositories into the prompt.
- **Massive context windows:** Models like Gemini Flash offer 1M+ token context windows, allowing them to ingest an entire medium-sized repository in a single prompt when necessary.

## The Multi-Repo Org Gaps

When answering questions spanning an organization with 50–500 microservices, standard CLI tools hit three architectural limitations:

**1. Single-Directory Sandboxing**
CLI agents are bounded by their current working directory (`CWD`). If a user asks *"Where is Stripe webhook signature verification implemented across our services?"*, the agent has no built-in awareness of the other 79 repositories in the GitHub organization.

**2. No Org-Level Repository Catalog**
Standard tools lack an automated directory listing repository descriptions, tech stacks, and top-level package exports. Agents cannot route prompts to the top 2–3 candidate repos without manual human intervention or external GitHub API queries.

**3. No Automated Multi-Repo Map-Reduce**
Agents do not automatically spin up parallel search runners across 50 remote repositories to extract per-repo summaries and reduce them into a unified audit report.

### Related
- [[multi-repo agentic search architecture]] — 3-tier catalog, AST outline, and map-reduce pipeline for GitHub orgs.
- [[vault MCP server for agents]] — Designing structured tool interfaces over raw file dumps.
- [[easiest way to support agentic map reduce]]