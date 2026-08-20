---
tags:
  - ai
  - github
  - architecture
  - ci-cd
  - automation
---
The simplest, lowest-friction way to implement agentic map-reduce across repositories without building custom orchestration servers.

## The Core Concept: Pre-Computed CI/CD Maps
Instead of forcing interactive coding agents to crawl and map repositories on demand while you wait, pre-compute the map asynchronously on every Git push using [[GitHub Actions]]:

```
  Git Push (Developer / PR)
             │
             ▼
  GitHub Action (Incremental AST / Flash Summary)
             │
             ▼
  Saves `llms.txt` or `.agent/repo_map.md` to repo / org catalog
             │
             ▼
  Agent reads map first via [[AGENTS]] / `CLAUDE.md`
```

## The 3-Step Implementation

**1. GitHub Action on Push**
A lightweight workflow triggers on `push` to `main`:
- Detects changed files using `git diff --name-only HEAD~1`.
- Extracts class and function signatures using AST tools (`tree-sitter`, `repomix`, or a fast Gemini Flash prompt).
- Updates a concise summary file: `llms.txt` or `.agent/repo_map.md`.

**2. Storage Strategy**
- **Single-repo:** Commit the updated map directly to repository root (e.g. `llms.txt`) or an `.agent/` folder.
- **Multi-repo org:** Push the per-repo map fragment into a central `org-index` repository or GitHub Pages catalog.

**3. Agent Steering via AGENTS.md**
Add a single steering rule to the repo's agent prompt file (`AGENTS.md`, `CLAUDE.md`, or `GEMINI.md`):
> *"Never crawl or grep raw source directories upfront. Always read `llms.txt` or `.agent/repo_map.md` first to locate relevant modules before opening files."*

## Ready-to-Use Workflow (`.github/workflows/repo-map.yml`)

```yaml
name: Update Agent Repo Map
on:
  push:
    branches: [main]
jobs:
  build-map:
    runs-on: ubuntu-latest
    permissions:
      contents: write
    steps:
      - uses: actions/checkout@v4
      - name: Generate skeleton map
        run: npx repomix --style xml --output .agent/repo_map.xml --parsable-style
      - name: Commit map
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add .agent/repo_map.xml
          git commit -m "chore: update agent repo map [skip ci]" || exit 0
          git push
```

## Why This is the Easiest Path
- **Zero infrastructure:** No background databases, vector servers, or custom daemon processes to host and maintain.
- **Zero query latency:** The map is already sitting on disk when the agent starts; no runtime scanning delay.
- **Cost efficiency:** Parsing runs once in CI via cheap models (Gemini Flash) or free local AST parsers.

### Related
- [[multi-repo agentic search architecture]] — 3-tier catalog and rollup strategy for multi-repo organizations.
- [[agent-friendly documentation tools]] — Standardized summary formats like `llms.txt` and `repomix`.
- [[hierarchical map-reduce note rollup]] — Theoretical map-reduce pattern applied to Markdown vaults.
- [[CICD]]