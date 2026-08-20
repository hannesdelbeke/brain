---
tags:
  - ai
  - architecture
  - economics
  - github
  - optimization
---
Quantifying the direct API token savings and engineering time recovered by replacing naive context dumping with pre-computed CI/CD maps and catalog routing.

## Baseline Organization Model

- Organization: 500 employees, 100 software engineers, 200 repositories.
- Activity: 15 agent prompts per engineer daily (1,500 total queries/day org-wide: 225 multi-repo, 1,275 single-repo).
- Engineering rate: $60/hour ($120k/year).

## Claude Sonnet Tier ($3.00 / 1M input)

Standard default model in tools like [[Claude Code]]:
- Naive context dumping: ~54.4M input tokens/day $\approx$ $43,000 / year.
- Pre-computed maps & catalog routing: ~9.1M input tokens/day $\approx$ $7,200 / year.
- Direct API savings: ~$35,800 / year (83% reduction).

## Claude Opus / Flagship Tier ($15.00 / 1M input)

Flagship frontier models used for complex refactors and reasoning:
- Naive dumping into Opus: 54.4M input tokens/day $\approx$ $215,000 / year.
- Hierarchical map-reduce (Haiku map $\rightarrow$ Opus reduce): Cheap models scan repos, Opus only reads structured summaries $\approx$ $35,000 / year.
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

