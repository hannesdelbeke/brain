---
tags:
  - technical
  - git
  - pkm
  - ai
  - embeddings
  - gpu
---
> i remembered something mentioned in a note, but not which note!
> but AI had reformatted it, together with hundreds of other notes.
> 
> if i AI could do semantic meaning on git history, it could probably find it in the history.
> how can i get this working for my vault?
> also see [[agentic tooling upgrades over grep]]
> how can we run this on gpu?

When AI agents mass-reformat hundreds of notes, valuable ideas and raw human phrasing get pruned across the vault. Because you don't know which file contained the text or exact wording, keyword tools like `git log -S` fail.

Vault-wide semantic Git search extracts all historical deleted text blocks and indexes them using local GPU vector embeddings.

## How it works

```
Git History (all .md) ──> Extract Deleted Chunks (-) ──> GPU Embeddings (DirectML/CUDA) ──> SQLite (pkm_index.db) ──> Semantic Query
```

### 1. Extract deleted diff chunks
Instead of snapshotting every historical revision (which duplicates thousands of unchanged files), parse only what was *removed* or *replaced*:
- Stream commit diffs: `git log -p -U1 -M -C --date=iso -- "*.md"`
- Group contiguous deleted lines (`-`) into paragraph-sized chunks.
- Filter out trivial changes: frontmatter hash updates, pure whitespace, or single-character edits under 20 characters.
- Capture metadata per chunk: `commit_sha`, `commit_date`, `author`, and original `file_path`.

### 2. GPU acceleration (DirectML / CUDA)
As measured in [[agentic tooling upgrades over grep]], embedding on CPU processes ~20 chunks/sec, while local GPU acceleration runs at **~760+ chunks/sec** on a basic GTX 1060 (dropping indexing time from 15 minutes to ~20 seconds).

To run embeddings on GPU on Windows:
- Install `onnxruntime-directml` (works on NVIDIA, AMD, and Intel GPUs via DirectX 12) or `onnxruntime-gpu` (CUDA).
- Initialize `fastembed` with execution providers in order: `["DmlExecutionProvider", "CUDAExecutionProvider", "CPUExecutionProvider"]`.
- Batch embeds in chunks of 128 to saturate GPU tensor cores without overflowing VRAM.

### 3. Store in SQLite index
Store chunks and dense vectors (`BAAI/bge-small-en-v1.5`, 384-dim) in `.obsidian/pkm_index.db` alongside [[pkm metadata indexer]]:
- Table `git_history_chunks (id, commit_sha, commit_date, author, file_path, deleted_text, vector)`
- FTS5 table `git_history_fts (chunk_id, content)` for hybrid keyword + semantic search.

### 4. Query and resurrect
When you search for a forgotten concept (e.g. `"ideas about solar diverter automation"`):
- The indexer computes cosine similarity across all deleted chunks vault-wide in <0.5ms.
- It returns the matching snippet, the historical `file_path`, and the commit where it was pruned.
- Run `git show <commit_sha>^:<file_path>` to view the whole note in its exact pre-reformatted state.

## Scoping mass-reformatting sessions

Filter the diff stream before embedding to index specific AI refactoring waves:
- **By AI author:** `git log --author="Claude" --author="Gemini"` (leveraging AI commit author conventions from [[AGENTS]]).
- **By date window:** `git log --since="2026-01-01" --until="2026-08-01"`.

## Implementation script

A GPU-accelerated historical diff indexer for `skills/pkm-metadata-indexer`:

```python
import subprocess, sqlite3, numpy as np
from fastembed import TextEmbedding

def get_gpu_providers():
    try:
        import onnxruntime as ort
        avail = set(ort.get_available_providers())
        return [p for p in ["DmlExecutionProvider", "CUDAExecutionProvider", "CPUExecutionProvider"] if p in avail]
    except Exception:
        return ["CPUExecutionProvider"]

def extract_deleted_chunks(repo_path):
    cmd = ["git", "-C", repo_path, "log", "-p", "-U0", "--date=iso", "--", "*.md"]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, text=True, errors="ignore")
    sha, date, author, path = None, None, None, None
    curr_lines = []
    
    for line in proc.stdout:
        if line.startswith("commit "):
            sha = line.split()[1]
        elif line.startswith("Author:"):
            author = line[7:].strip()
        elif line.startswith("Date:"):
            date = line[5:].strip()
        elif line.startswith("--- a/"):
            path = line[6:].strip()
        elif line.startswith("-") and not line.startswith("---"):
            text = line[1:].strip()
            if len(text) > 20 and not text.startswith("sentiment-hash:"):
                curr_lines.append(text)
        elif curr_lines:
            yield sha, date, author, path, "\n".join(curr_lines)
            curr_lines = []

def index_git_history(repo_path, db_path):
    chunks = list(extract_deleted_chunks(repo_path))
    model = TextEmbedding("BAAI/bge-small-en-v1.5", providers=get_gpu_providers())
    
    con = sqlite3.connect(db_path)
    con.execute("CREATE TABLE IF NOT EXISTS git_history_chunks (sha TEXT, date TEXT, author TEXT, path TEXT, text TEXT, vector BLOB)")
    
    batch_size = 128
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i+batch_size]
        texts = [item[4] for item in batch]
        vectors = [np.asarray(v, dtype=np.float32).tobytes() for v in model.embed(texts, batch_size=batch_size)]
        rows = [(c[0], c[1], c[2], c[3], c[4], vec) for c, vec in zip(batch, vectors)]
        con.executemany("INSERT INTO git_history_chunks VALUES (?,?,?,?,?,?)", rows)
        con.commit()
```

## See also
- [[agentic tooling upgrades over grep]] — benchmarks comparing CPU vs GPU embedding speeds and hybrid search
- [[pkm metadata indexer]] — local SQLite indexer for vault hybrid search and embeddings
- [[URI link to obsidian git diff - RnD]] — opening historical commit diffs directly in Obsidian via URI
- [[extract historic wikilinks from git]] — tracking link births and deaths in Git history
- [[semantic index as a git extension]] — the same idea generalised into a repo-level capability, keyed by blob SHA instead of by commit
[[semantic search]]
[[Semantic Versioning]]
[[semantic search online notes]]