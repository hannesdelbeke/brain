---
tags:
  - technical
  - obsidian
  - git
  - python
  - pkm
---
Proposal and script to extract added and removed [[wikilink|wikilinks]] from Git history into SQLite, generating data for [[2026-07-31 historic obsidian links|temporal graph analysis]] and [[wikilink temporal integrity]].

### Implementation Plan
1. **Reuse native diffs:** Use `git log -p --follow -M -- '*.md'` to handle file renames and deletions without custom diff tracking.
2. **Standard library:** Pure Python with `subprocess`, `re`, and `sqlite3`.
3. **Parse diff chunks:** Match lines starting with `+` or `-` for wikilink regex `\[\[([^\]|#]+)`.

### Extraction Script
```python
import subprocess, re, sqlite3, sys

WIKILINK = re.compile(r'\[\[([^\]|#]+)')

def events(repo_path):
    out = subprocess.run(
        ["git", "-C", repo_path, "log", "-p", "--follow", "-M",
         "--date=iso", "--", "*.md"],
        capture_output=True, text=True, check=True
    ).stdout

    commit, date, source = None, None, None
    for line in out.splitlines():
        if line.startswith("commit "):
            commit = line.split()[1]
        elif line.startswith("Date:"):
            date = line[5:].strip()
        elif line.startswith("+++ b/") or line.startswith("--- a/"):
            source = line[6:]
        elif line[:1] in "+-" and not line[:3] in ("+++", "---"):
            for target in WIKILINK.findall(line):
                yield commit, date, source, target, "add" if line[0] == "+" else "remove"

def build_db(repo_path, db_path):
    con = sqlite3.connect(db_path)
    con.execute("CREATE TABLE IF NOT EXISTS link_events (commit_sha TEXT, date TEXT, source TEXT, target TEXT, event TEXT)")
    con.executemany("INSERT INTO link_events VALUES (?,?,?,?,?)", events(repo_path))
    con.commit()

if __name__ == "__main__":
    build_db(sys.argv[1], sys.argv[2])
```

### Querying Capabilities
- **Edge birth and death:** `MIN(date)` and `MAX(date)` grouped by `(source, target)` where last event is `remove`.
- **Edge weights & decay:** Count `add` events or total survival duration for RAG ranking.
- **Reorganization detection:** Identify commits with high add/remove churn across multiple source notes.

### References
- [[2026-07-31 historic obsidian links]] — research on why historical graph edges improve retrieval and detect conceptual drift.
- [[wikilink temporal integrity]] — resolves links to their historical snapshot states based on commit timestamps.
- [[linking to git commits and diffs in obsidian via uri]] — URI protocol schemes to inspect the commit diffs where links were edited.
- [[human vs ai text context]] — preserving Git commit history when moving notes to `public/`.
