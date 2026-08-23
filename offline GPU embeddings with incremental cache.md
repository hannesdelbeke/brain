---
tags:
  - ai
  - embeddings
  - python
  - technical
  - pkm
  - gpu
origin-sha: 4e7e95b2a
---
> [!summary] Status
> **Phase 1 Implementation.** Lightweight GPU embeddings (`all-MiniLM-L6-v2`) with persistent SQLite SHA256 caching provide instant fuzzy/thematic search for agents without ongoing API cost. See [[agentic tooling upgrades over grep]].

How to run local vector embeddings across thousands of [[Markdown]] notes in your [[Obsidian]] vault on an RTX [[graphics processing unit|GPU]] with persistent [[cache|caching]], ensuring subsequent runs only process modified or newly added notes.

> [!ai]+ Verified Benchmark: [[razor blade 15 rz09-02705w76 2018|Razer Blade 15 (2018, GTX 1060 Max-Q 6GB)]]
> Tested on 2026-08-21 using `fastembed` with `onnxruntime-directml` and `BAAI/bge-small-en-v1.5` (384-dim):
> - **Throughput:** **764.0 chunks/sec** on GPU (1,000 chunks embedded in **1.31 seconds** vs ~45.0s on CPU).
> - **Full vault build (17,356 sections):** **~22 seconds** on GPU vs ~14 minutes on CPU.
> - **VRAM footprint:** < 300 MB out of 6 GB VRAM (< 5% usage).
> - **Incremental updates:** **< 0.05 seconds** per modified note via SQLite SHA256 caching.
> - **Active tooling:** [[pkm metadata indexer|index_pkm_meta.py]] and [[pkm metadata indexer|search_vault.py]].

---

## How Incremental Caching Works

```
                  ┌─────────────────────────────────────┐
                  │          Scan Vault Note            │
                  └──────────────────┬──────────────────┘
                                     ▼
                  ┌─────────────────────────────────────┐
                  │ Has file hash or mtime changed vs   │
                  │        the SQLite Cache?            │
                  └─────────┬─────────────────┬─────────┘
                            │                 │
                      NO    │                 │   YES (New / Edited Note)
                            ▼                 ▼
             ┌────────────────────────┐   ┌───────────────────────────┐
             │ Skip (0s, 0 GPU work)  │   │  Run Fast GPU Embedding   │
             │ Keep existing vectors  │   │  Update SQLite Cache DB   │
             └────────────────────────┘   └───────────────────────────┘
```

1. **Initial Indexing (One-Time):** Processes ~3,000+ notes on GPU in ~30–60 seconds.
2. **Incremental Runs:** Checks content SHA256 / modification timestamps in < 0.2 seconds. Only newly edited files trigger GPU embedding.
3. **Storage footprint:** 3,000 document vectors (768 dimensions) take **~5–10 MB** of disk space in SQLite or ChromaDB.

---

## Implementation Options

### Option A: Obsidian Plugin (smart Connections)
- **Plugin:** Smart Connections
- **Backend:** Local Ollama (`nomic-embed-text` or `bge-m3`) or local transformers
- **Caching:** Built-in. Automatically caches vectors in `.obsidian/plugins/smart-connections/` and updates on note save.

### Option B: Standalone Python Script (sqlite Vector Cache)
A lightweight script using `sentence-transformers` or `fastembed-gpu`:

```python
import os
import hashlib
import sqlite3
from pathlib import Path
from sentence_transformers import SentenceTransformer

PKM_PATH = Path(r"C:\repos\pkm")
DB_PATH = Path(r"C:\repos\pkm\.obsidian\pkm_vectors.db")

def get_file_hash(path):
    with open(path, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()

def update_embeddings():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS embeddings (
            path TEXT PRIMARY KEY,
            content_hash TEXT,
            embedding BLOB
        )
    """)
    
    # Load fast local embedding model on GPU
    model = SentenceTransformer("all-MiniLM-L6-v2", device="cuda")
    
    for root, _, files in os.walk(PKM_PATH):
        if ".obsidian" in root or ".git" in root:
            continue
        for file in files:
            if not file.endswith(".md"):
                continue
            full_path = Path(root) / file
            rel_path = full_path.relative_to(PKM_PATH).as_posix()
            file_hash = get_file_hash(full_path)
            
            # Check cache
            cur.execute("SELECT content_hash FROM embeddings WHERE path = ?", (rel_path,))
            row = cur.fetchone()
            if row and row[0] == file_hash:
                continue # Unchanged, skip!
                
            with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()
                
            vector = model.encode(text)
            cur.execute("""
                INSERT OR REPLACE INTO embeddings (path, content_hash, embedding)
                VALUES (?, ?, ?)
            """, (rel_path, file_hash, vector.tobytes()))
            print(f"Embedded: {rel_path}")
            
    conn.commit()
    conn.close()

if __name__ == "__main__":
    update_embeddings()
```

benefits of custom script vs plugin

| Feature                         | Standalone Python Script (SQLite)                                 | Obsidian Plugin (Smart Connections)                    |
| :------------------------------ | :---------------------------------------------------------------- | :----------------------------------------------------- |
| **Obsidian Startup Speed**      | **Zero impact** (runs outside Obsidian process)                   | Adds indexing overhead / plugin load lag on startup    |
| **Agent / CLI Accessibility**   | **Directly queryable** by CLI agents (`agy`, Claude Code, Python) | Trapped inside Obsidian plugin internals               |
| **Custom Chunking & Filtering** | Total control over frontmatter stripping, chunk size, tags        | Fixed plugin-level chunking heuristics                 |
| **VRAM & Process Isolation**    | Runs only when triggered, frees VRAM immediately                  | ==Keeps local embedding server running in background== |
| **Portability**                 | Single lightweight `.db` file queryable from anywhere             | Tied to Obsidian plugin config & updates               |

---

## Quickstart on Razer Blade 15
Tested on [[razor blade 15 rz09-02705w76 2018|Razer Blade 15]]:

1. **Install requirements:**
   ```bash
   pip install fastembed onnxruntime-directml numpy
   ```
2. **Run full-vault GPU indexing:**
   ```bash
   python public/skills/pkm-metadata-indexer/index_pkm_meta.py
   ```
3. **Run sub-second semantic search:**
   ```bash
   python public/skills/pkm-metadata-indexer/search_vault.py "query or vibe"
   ```

## References
- [[token efficient PKM analysis architecture]]
- [[PKM indexer performance log]]
- [[2026-08-17 PKM review]]
- [[what AI models can razor blade run]]
