---
tags:
  - ai
  - github
  - architecture
  - tools
  - optimization
---
An agentic search and rollup architecture to query across 50–500 repositories in a [[GitHub]] organization without cloning entire codebases or burning millions of API tokens.

## The Multi-Repo Problem
When an [[AI agent|AI agent]] answers questions spanning an entire organization (e.g. *"Which services use deprecated auth endpoint X?"* or *"Where is billing logic implemented across our microservices?"*), naive approaches fail:
- **Raw cloning and grepping:** Clones gigabytes of code and runs slow, brute-force file searches across dozens of repositories.
- **Context dumping:** Packing full repositories into frontier model context windows burns hundreds of thousands of tokens per query on boilerplate, dependencies, and build artifacts.

## The 3-Tier Multi-Repo Search Pipeline

```
┌─────────────────────────────────────────────────────────────┐
│              Tier 1: Org Repository Catalog                 │
│      Lightweight index of repo descriptions & symbols       │
└──────────────────────────────┬──────────────────────────────┘
                               ▼
┌─────────────────────────────────────────────────────────────┐
│           Tier 2: Repo Skeletons & Incremental AST          │
│   Tree-sitter signatures + cached embeddings on commit SHA  │
└──────────────────────────────┬──────────────────────────────┘
                               ▼
┌─────────────────────────────────────────────────────────────┐
│          Tier 3: Hierarchical Map-Reduce Rollup             │
│    Repo Maps (Flash/Haiku) ──► Org Synthesis (Pro/Opus)     │
└─────────────────────────────────────────────────────────────┘
```

### Tier 1: Org Repository Catalog (Repo Routing)
Before touching any code files, the agent queries a lightweight organization catalog:
- **Index:** A cached table of repository names, README summaries, tech stacks, and top-level exported packages or services.
- **Repo routing:** The agent identifies the 2–5 candidate repositories relevant to the prompt, immediately filtering out 90%+ of irrelevant codebases at zero token cost.

### Tier 2: Repo Skeletons & Incremental AST Indexing
For the selected candidate repos, the agent pulls compact structural skeletons rather than raw implementation files:
- **AST extraction:** Uses `tree-sitter` or `ctags` to extract module docstrings, class declarations, and function signatures.
- **Commit SHA caching:** Indexes and GPU embeddings are cached against the latest commit SHA (`git rev-parse HEAD`), so only repos with new commits are re-indexed.

### Tier 3: Hierarchical Map-Reduce Rollup
When answering complex multi-repo queries:
1. **Map (Per-Repo Extraction):** A fast, low-cost model (e.g. Gemini Flash or Claude Haiku) inspects only the targeted code chunks within each candidate repo and outputs a concise structured summary answering the query for that specific codebase (~2k–5k tokens per repo).
2. **Reduce (Org-Wide Synthesis):** A deep reasoning model (Gemini Pro or Claude Opus) receives the per-repo summary fragments and synthesizes the unified cross-repo answer (~10k tokens).

## Agent MCP Tool Interface
Exposes structured multi-repo query primitives via Model Context Protocol:

```bash
# Route prompt to candidate repositories in org
mcp-org-search route "where is user subscription billing processed"

# Search AST symbols across targeted repositories
mcp-org-search symbols --repos "billing-service,api-gateway" --query "process_payment"

# Map-reduce rollup across all services
mcp-org-search rollup --query "audit all OAuth2 callback implementations"
```

### Related
- [[hierarchical map-reduce note rollup]] — The foundational map-reduce compression pattern applied to personal notes.
- [[agent-friendly documentation tools]] — Specifications like `llms.txt` and `repomix` for packing codebases into token-efficient agent formats.
- [[vault MCP server for agents]] — Structured MCP server design patterns for AI assistants.
