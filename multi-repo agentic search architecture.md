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
- **Context dumping:** Packing full repositories into frontier model [[session context|context windows]] burns hundreds of thousands of [[AI tokens|tokens]] per query on boilerplate, dependencies, and build artifacts.

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
- **Repo routing:** The agent identifies the 2–5 candidate repositories relevant to the prompt, filtering out 90%+ of irrelevant codebases at zero token cost.

Instead of calling every team in a company to ask what they do, the agent checks the org address book and only visits the relevant departments.

### Tier 2: Repo Skeletons & Incremental AST Indexing
For the selected candidate repos, the agent inspects compact structural skeletons rather than full implementation files:
- **AST extraction:** Uses `tree-sitter` or `ctags` to extract module docstrings, class declarations, and function signatures.
  It pulls class names, function signatures (like `def process_payment(amount, user_id)`), and top docstrings while stripping out the internal function bodies.
- **Commit SHA caching:** Indexes and embeddings are cached against the latest commit SHA (`git rev-parse HEAD`), so only repos with new commits are re-processed.

### Tier 3: Hierarchical Map-Reduce Rollup
When answering complex multi-repo queries across multiple services:
1. **Map (Per-Repo Extraction):** A fast, low-cost model (e.g. Gemini Flash or Claude Haiku) inspects targeted code chunks within each candidate repo and outputs a concise structured summary (~2k–5k tokens per repo).
2. **Reduce (Org-Wide Synthesis):** A deep reasoning model (Gemini Pro or Claude Opus) receives those per-repo summaries and synthesizes the unified answer (~10k tokens).

The expensive reasoning model (the lead architect) delegates reading individual repos to cheap, fast models (the interns), then combines their findings into a single coherent answer.

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
- [[single-repo vs multi-repo agent search]] — Comparing out-of-the-box CLI capabilities (Claude Code, Gemini Flash) with cross-repo gaps.
- [[hierarchical map-reduce note rollup]] — The foundational map-reduce compression pattern applied to personal notes.
- [[agent-friendly documentation tools]] — Specifications like `llms.txt` and `repomix` for packing codebases into token-efficient agent formats.
- [[vault MCP server for agents]] — Structured MCP server design patterns for AI assistants.
