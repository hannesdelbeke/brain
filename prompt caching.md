---
tags:
  - ai
  - optimization
  - economics
---
An LLM inference optimization that saves prompt prefixes in memory between API calls, dramatically lowering latency and cost for repetitive context.

## Pricing & Persistence Dynamics
In models supporting prompt caching (e.g. Anthropic Claude, OpenAI, Gemini):
- **Cache write:** Incurred on the first call or when new prefix content is added (typically $1.25\times$ base input cost).
- **Cache read:** Subsequent calls reusing that exact prefix receive up to a 90% discount ($0.1\times$ base input cost).
- **Time-to-live (TTL):** Caches typically persist for 5 minutes of inactivity before expiring (with 1-hour extended TTL options).

## The Turn Multiplier
In conversational coding sessions, a tool result or file read of $N$ tokens stays in context across all subsequent turns:

$$\text{Total Cost} = N \times (1.25 + 0.1 \times \text{remaining\_turns})$$

Because early exploratory search outputs stay in context longest, early tool results pay a heavy $2\times$ to $11\times$ lifetime cost multiplier.

### Related
- [[multi-repo agent search cost and ROI]] — Quantifying prompt caching economics in engineering organizations.
- [[vault MCP server for agents]] — Structuring tool outputs to prevent context bloating in cached sessions.
