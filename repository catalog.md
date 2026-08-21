---
tags:
  - architecture
  - github
  - ai
  - tools
---
A lightweight, centralized directory listing an organization's active repositories, their architectural domains, ownership, and primary entry points.

## Why Agents Need a Catalog
When coding agents answer questions across multi-repo organizations (50–500 services), they are sandboxed to their current directory. Without a catalog, agents cannot know which repository owns a given feature.

An org catalog acts as an architectural address book:
- **Zero-token routing:** The agent scans the 1–2 page catalog to identify the 2–3 relevant repositories before opening any code.
- **Automated hygiene:** Generated via scheduled CI/CD jobs querying repository metadata, topics, and README summaries.

### Related
- [[multi-repo agentic search architecture]] — 3-tier catalog and map-reduce pipeline for multi-repo orgs.
- [[simple options for multi-repo agent search]] — Low-infrastructure implementations for org-level catalogs.
- [[repo maps via GitHub Actions]] — Per-repo map pre-computation in CI/CD.
