---
tags:
  - ai
  - github
  - architecture
  - automation
  - cli
---
Low-infrastructure, pragmatic options to solve the 3 major multi-repo search gaps without hosting complex vector servers or custom daemons.

## The 3 Gaps & Simple Options

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Sandboxing (CWD)   ──► Meta-Repo or Org GitHub Action    │
│ 2. Org Catalog        ──► Static `org-map.md` in `.github`  │
│ 3. Multi-Repo Rollup  ──► GitHub Actions Matrix / CLI Loop  │
└─────────────────────────────────────────────────────────────┘
```

---

## Gap 1: Single-Directory Sandboxing

Agents sit in one local repository (`CWD`) and cannot see other repositories across the organization.

- **Option A (Meta-Repo / Multi-Submodule Vault):** Create a local `workspaces/` parent folder containing all active repos as git submodules or sibling folders with a top-level `AGENTS.md`. Agents running at the root can grep and navigate across repos natively.
- **Option B (GitHub CLI Tooling):** Give the agent access to the `gh` CLI (`gh search code`, `gh repo list`). When asked about other services, the agent queries GitHub's remote code search without cloning.
- **Option C (Launcher Script):** A lightweight wrapper script (`agy-org "prompt"`) that reads a central catalog, identifies the target repository, and launches the agent directly in that repository directory.

---

## Gap 2: No Org-Level Repository Catalog

No central address book mapping repository names to their architectural responsibilities.

- **Option A (Central `.github` Repo Map):** A single cron GitHub Action runs weekly in the special `.github` repository. It calls `gh repo list <org> --json name,description,topics` and generates a static `org-map.md` or `llms-org.txt`.
- **Option B (GitHub Pages Aggregator):** Combine the pre-computed `llms.txt` from each repo (per [[repo maps via GitHub Actions]]) into a single hosted GitHub Pages site (`https://my-org.github.io/llms-full.txt`).
- **Option C (Standardized Repo Topics):** Enforce consistent GitHub topics (`#auth`, `#billing`, `#python`) so agents can find candidate repos instantly via `gh repo list my-org --topic auth`.

---

## Gap 3: No Multi-Repo Map-Reduce

Running organization-wide audits or refactoring questions across 50 repositories simultaneously.

- **Option A (GitHub Actions Matrix Workflow):** Trigger a workflow with `strategy: matrix: repo: [repo-1, repo-2, ...]`. Each runner clones one repo, runs a fast model (Gemini Flash) to output a 200-word summary artifact, and a final `reduce` job combines all artifacts into a PR or issue summary.
- **Option B (Local Subagent Script):** A 25-line Python script that iterates through candidate repos, invokes local CLI agents (`agy` / `claude`) in parallel with subagent prompts, and pipes the output into a final reasoning pass.
- **Option C (Issue-Triggered Audit Bot):** Opening a GitHub issue with label `agent-audit` triggers a workflow that queries relevant repos and posts per-repo findings as comments, followed by a final synthesized summary.

---

## Recommended Minimum Viable Setup

For the fastest setup with **zero ongoing server maintenance**:
1. **Catalog:** A weekly GitHub Action generating `org-map.md` in the `.github` repo.
2. **Repo Maps:** The drop-in `.github/workflows/repo-map.yml` in each repo from [[repo maps via GitHub Actions]].
3. **Execution:** Local CLI script querying the catalog first, then launching the agent in the target repo.

### Related
- [[single-repo vs multi-repo agent search]] — The architectural limitations of single-workspace CLI tools.
- [[multi-repo agentic search architecture]] — High-level 3-tier catalog and map-reduce theory.
- [[repo maps via GitHub Actions]] — Plug-and-play workflow for generating per-repo maps in CI/CD.
- [[proposal - agent git workflow tooling]] — folds this MVP into the wider workflow-tooling proposal, with a 2026 tool scan (Zoekt, WarpGrep, CodeGraph).
