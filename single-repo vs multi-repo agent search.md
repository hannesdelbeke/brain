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

## The Multi-Repo Org Gaps & Simple Solutions

**1. Single-Directory Sandboxing**
CLI agents are bounded by their current working directory (`CWD`). If a user asks where a feature lives across 50 microservices, the agent doesn't know the other 49 repositories exist.

*Simple solution:* allow the agent to run `gh search code` via GitHub CLI.

**2. No Org-Level Repository Catalog**
Standard tools lack an automated directory listing what each repo does, so agents cannot route prompts to the top 2–3 candidate repos without manual human intervention.

*Simple solution:* A weekly cron GitHub Action in the org's `.github` repository that outputs a static `org-map.md` catalog listing all repo descriptions and topics.

**3. No Automated Multi-Repo Map-Reduce**
Agents cannot spin up parallel search runners across 50 remote repos to extract summaries and reduce them into a single report on demand.

*Simple solution:* [[repo maps via GitHub Actions]] — Pre-compute skeleton maps on push in CI/CD, so the agent only reads lightweight static maps rather than scanning raw code.

### Related
- [[multi-repo agentic search architecture]] — 3-tier catalog, AST outline, and map-reduce pipeline for GitHub orgs.
- [[vault MCP server for agents]] — Designing structured tool interfaces over raw file dumps.
- [[multi-repo agent search cost and ROI]]