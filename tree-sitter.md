---
tags:
  - tools
  - programming
  - ast
  - parsing
---
A fast, incremental parser generator tool that builds concrete syntax trees for source code across dozens of programming languages.

## Key Capabilities
- **Incremental parsing:** Re-parses modified code in milliseconds upon editing rather than reprocessing the entire file from scratch.
- **Robust error recovery:** Produces a valid syntax tree even when source code contains syntax errors or incomplete statements.
- **Structural extraction:** Allows tools to instantly query class names, function signatures (e.g. `def process_payment(amount, user_id)`), and top-level docstrings while discarding hundreds of lines of internal function bodies.

## Role in AI & Agent Tooling
Tree-sitter is the primary engine for generating compact code skeletons and repository maps (`llms.txt`, `repomix`), letting LLMs navigate module structures without loading full implementation files into context.

### Related
- [[repo maps via GitHub Actions]] — Using AST extractors to build lightweight pre-computed repo maps.
- [[multi-repo agentic search architecture]] — Skeletons and AST indexing across multiple repositories.
