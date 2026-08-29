---
tags:
- technical
- search
- pkm
- ai
---

Hosting the public PKM SQLite database and embedding vectors in the cloud allows agents on any machine (home PC, work PC, mobile) to run hybrid semantic search without local embedding models or synced index files.

## Vault Footprint & Sizing
The public vault currently holds ~3,230 markdown notes (~3.3 MB raw text). 
Chunking into ~6,500 passages with 384-dimensional dense vectors produces an index footprint of ~15–25 MB (including FTS5 tables, vector indexes, and link graphs).

## Hosting Options

- **Cloudflare D1 + Vectorize / Workers:** Best serverless edge setup. Free tier provides 5GB storage, 5M D1 reads/day, and 30M Vectorize dimensions queried/month. A simple Worker acts as an authenticated REST / MCP endpoint.
- **[[Turso]] (libSQL):** Native SQLite with `libsql_vector`. Free tier offers 9GB storage and 1B row reads/month. Agents can query directly via HTTP or embed a local read-replica.
- **[[Supabase]] (Postgres + pgvector):** 500MB free database tier with built-in REST API and vector indexing. Heavier than SQLite, but mature ecosystem for RPC search functions.
- **Cloudflare R2 + SQLite HTTP Range Requests:** Static hosting of the `.sqlite` file. Agents issue HTTP byte-range requests to read chunks directly without a running database server.

## Traffic Capacity
For personal single-user multi-agent workloads (10–50 agent queries daily, ~500 vector lookups), any free tier consumes less than 1% of monthly limits. Turso or Cloudflare D1 can scale to tens of thousands of requests per day at $0 before needing paid resources.

## Tracking Agent Energy & Note Utility

To identify which notes actively help agents solve tasks versus dead weight, the endpoint logs usage and correlates searches with completed outcomes (see [[note utility and synapse strength from session recaps]]).

**Usage telemetry schema**
- `query_id`: unique search query identifier
- `timestamp`: execution time
- `agent_id`: model/caller tag (e.g. `claude-cli`, `gemini-flash-local`)
- `query_text`: input search query
- `retrieved_note_ids`: ranked notes returned to the agent context
- `score`: similarity and BM25 rank scores

**Utility scoring model**
Notes accumulate a dynamic utility score based on agent task resolution:
- **Positive reinforcement (+3):** Retrieved note was explicitly cited, read in detail, or included in a successful git commit/task completion.
- **Neutral retrieval (+0.1):** Note returned in top 5 results but unused.
- **Negative signal (-1):** Note retrieved during sessions that failed, timed out, or required repeated re-prompting.

Analyzing this access history reveals high-leverage concept notes, uncovers knowledge gaps where searches return low similarity, and flags outdated notes that lead agents astray.

## Related Notes
- [[note utility and synapse strength from session recaps]]
- [[pkm metadata indexer]]
- [[agentic tooling upgrades over grep]]
- [[cross-agent session indexing architecture]]
