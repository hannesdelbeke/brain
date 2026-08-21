---
tags:
  - ai
  - architecture
  - economics
  - github
  - optimization
---
Quantifying the direct API token savings and engineering time recovered by replacing exploratory directory crawling with pre-computed CI/CD catalogs and targeted file routing.

## The Real Token Cost Driver: Cache Persistence

In modern coding agents with [[prompt caching]] (e.g. [[Claude Code]]), a tool result or file read of $N$ tokens is written into cache once ($1.25\times$) and re-read at ($0.1\times$) on every remaining turn of the session:

$$\text{Effective Cost} = N \times (1.25 + 0.1 \times \text{remaining\_turns})$$

- At 10 remaining turns: $2.25\times$ face value.
- At 50 remaining turns: $6.25\times$ face value.
- At 100 remaining turns: $11.25\times$ face value.

Early exploratory search calls (blind grepping across multiple repositories or reading large configuration files to find where logic lives) stay in context for the rest of the session, paying the cache read multiplier on every subsequent turn.

## Re-Read Redundancy vs. Context Dumping

Agents rarely dump entire 500k-line codebases at once. Instead, they suffer from **re-read redundancy**: subagents repeatedly re-read the same architectural and routing files (often 6x–10x across a task) because the initial brief lacked explicit file targets.

Providing an org-wide [[repository catalog]] and pre-computed router eliminates exploratory search turns and cuts redundant file reads upfront.

## Baseline Organization Model

- Organization: 500 employees, 100 software engineers, 200 repositories.
- Activity: 15 agent prompts per engineer daily (1,500 total queries/day org-wide: 225 multi-repo, 1,275 single-repo).
- Engineering rate: $60/hour ($120k/year).

## Claude Sonnet Tier ($3.00 / 1M input)

Standard default model in tools like [[Claude Code]]:
- Exploratory grep & re-read loops: *~54.4M input tokens/day $\approx$ $43,000 / year.*
- Pre-computed maps & [[repository catalog|catalog routing]]: *~9.1M input tokens/day $\approx$ $7,200 / year.*
- Direct API savings: *~$35,800 / year (83% reduction).*

## Claude Opus / Flagship Tier ($15.00 / 1M input)

Flagship frontier models used for complex refactors and reasoning:
- Exploratory crawl in Opus: 54.4M input tokens/day $\approx$ $215,000 / year.
- Hierarchical [[map-reduce]] (cheap map $\rightarrow$ Opus reduce): Cheap models scan candidate repos, Opus only reads structured summaries $\approx$ $35,000 / year.
- Direct API savings: ~$180,000 / year (84% reduction).

## Engineering Wait Latency Recovered

Beyond API token spend, developer wait time represents the largest economic saving:
- Naive crawl delay: Developers wait 30–60 seconds per prompt while the agent crawls directories or processes massive 100k+ token prompts.
- Pre-computed map speed: Maps sit locally on disk; agent opens the target file in under 3 seconds.
- Recovered capacity: Saves ~2,800 developer hours/year across 100 engineers $\approx$ ~$168,000 / year in recovered productivity.

## Summary: Annual Expected Benefit

```
┌─────────────────────────────────────────────────────────────┐
│  Claude Sonnet Total Value (API + Dev Time): ~$203,800/year │
│  Claude Opus Total Value   (API + Dev Time): ~$348,000/year │
└─────────────────────────────────────────────────────────────┘
```

### Related
- [[multi-repo agentic search architecture]] — 3-tier catalog, AST outline, and map-reduce pipeline for GitHub orgs.
- [[repo maps via GitHub Actions]] — Plug-and-play workflow for generating per-repo maps in CI/CD.
- [[hierarchical map-reduce note rollup]] — Theoretical map-reduce pattern applied to Markdown vaults.

