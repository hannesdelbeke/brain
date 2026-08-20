---
tags:
  - ai
  - tools
  - technical
  - mcp
  - pkm
origin-sha: f0156f1
---
Tools that expose documentation, codebases, and web content as plain [[Markdown]] or MCP endpoints for [[AI agent|AI agents]] without requiring a full browser.

### Llms.txt & Markdown Indices
Publishing machine-readable indexes at `/llms.txt` or full corpus dumps at `/llms-full.txt`:
- 🟢 [AnswerDotAI/llms-txt](https://github.com/AnswerDotAI/llms-txt) ⭐2574 — the standard specification for AI-first documentation indexes.
- 🟢 [thedaviddias/llms-txt-hub](https://github.com/thedaviddias/llms-txt-hub) ⭐896 — directory of 200+ implementing sites plus a CLI installer.
- 🟢 [langchain-ai/mcpdoc](https://github.com/langchain-ai/mcpdoc) ⭐1030 — serves llms.txt files directly to code editors over MCP.
- 🟡 [firecrawl/llmstxt-generator](https://github.com/firecrawl/llmstxt-generator) ⭐537 — auto-generates llms.txt files for sites lacking one.

### MCP Endpoints
Live query endpoints returning structured documentation on demand:
- 🟢 [upstash/context7](https://github.com/upstash/context7) ⭐61004 — serves version-correct library documentation.
- 🟡 [idosal/git-mcp](https://github.com/idosal/git-mcp) ⭐8336 — exposes any GitHub repository as a remote MCP server with no setup.
- 🟢 [invertase/docs.page](https://github.com/invertase/docs.page) ⭐668 — serves markdown documentation from GitHub branches with MCP and llms.txt.

### Repo Packing & Single-file Aggregators
Bundles an entire codebase or markdown vault into a single prompt-sized file:
- 🟢 [coderamp-labs/gitingest](https://github.com/coderamp-labs/gitingest) ⭐15324 — replace `hub` with `ingest` in any GitHub URL to get prompt-ready markdown.
- 🟢 [yamadashy/repomix](https://github.com/yamadashy/repomix) ⭐27967 — packs local repositories into one structured markdown/XML file.
- 🟢 [AsyncFuncAI/deepwiki-open](https://github.com/AsyncFuncAI/deepwiki-open) ⭐17703 — auto-generates a structured wiki from a codebase.

### Web & API Scrapers
Markdown fallbacks when no direct endpoint exists:
- 🟡 [jina-ai/reader](https://github.com/jina-ai/reader) ⭐11886 — converts any web page to clean markdown by prefixing `https://r.jina.ai/`.
- 🟢 [freeCodeCamp/devdocs](https://github.com/freeCodeCamp/devdocs) ⭐39313 — offline searchable copies of hundreds of API documentation sets.

### References
- [[2026-08-19 AI tool research]] — review of Herdr, Roo Code, Devstral, and agent harnesses.
- [[offline GPU embeddings with incremental cache]] — local vector search over markdown files.
- [[how can we get value out of public notes]] — discovery and retrieval across external vaults.
