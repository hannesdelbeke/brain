"""
Fast, local metadata & summary extractor for PKM notes.
Extracts YAML frontmatter (energy, sentiment, tags) and top-level headings/bullets.
Outputs a lightweight SQLite database for token-efficient LLM analysis.
"""

import os
import re
import json
import sqlite3
import argparse
from pathlib import Path

def find_vault_root():
    """Locate the vault root directory containing .obsidian or .git, climbing up if necessary."""
    current = Path.cwd().resolve()
    for parent in [current, *current.parents]:
        if (parent / ".obsidian").exists() or (parent / ".git").exists():
            return parent
    return current

def parse_frontmatter(content):
    meta = {"energy": None, "sentiment": None, "sentiment_label": [], "tags": []}
    fm_match = re.match(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)
    if not fm_match:
        return meta, content
    
    fm_text = fm_match.group(1)
    body = content[fm_match.end():]
    
    # Extract energy
    energy_m = re.search(r"^energy:\s*(\d+)", fm_text, re.MULTILINE)
    if energy_m:
        meta["energy"] = int(energy_m.group(1))
        
    # Extract sentiment
    sent_m = re.search(r"^sentiment:\s*\n((?:\s*-\s*\d+\s*\n?)+)", fm_text, re.MULTILINE)
    if sent_m:
        scores = re.findall(r"\d+", sent_m.group(1))
        if scores:
            meta["sentiment"] = sum(int(s) for s in scores) / len(scores)

    # Extract sentiment labels
    label_m = re.search(r"^sentiment-label:\s*\n((?:\s*-\s*[^\n]+\s*\n?)+)", fm_text, re.MULTILINE)
    if label_m:
        meta["sentiment_label"] = [l.strip("- ").strip() for l in label_m.group(1).strip().splitlines()]

    # Extract tags
    tag_m = re.search(r"^tags:\s*\n((?:\s*-\s*[^\n]+\s*\n?)+)", fm_text, re.MULTILINE)
    if tag_m:
        meta["tags"] = [t.strip("- ").strip() for t in tag_m.group(1).strip().splitlines()]
        
    return meta, body

def extract_key_lines(body, max_lines=15):
    """Extracts high-signal lines (headings, bullets, tasks) while skipping long prose and boilerplate."""
    extracted = []
    for line in body.splitlines():
        line_clean = line.strip()
        if not line_clean:
            continue
        # Capture headers, markdown tasks, and first-level bullets
        if line_clean.startswith("#") or line_clean.startswith("- [ ]") or line_clean.startswith("- [x]") or line_clean.startswith("- "):
            if len(line_clean) > 200:
                line_clean = line_clean[:200] + "..."
            extracted.append(line_clean)
            if len(extracted) >= max_lines:
                break
    return "\n".join(extracted)

def build_index(vault_path=None, db_path=None):
    vault_dir = Path(vault_path).resolve() if vault_path else find_vault_root()
    database_file = Path(db_path).resolve() if db_path else vault_dir / ".obsidian" / "pkm_index.db"
    database_file.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"Indexing PKM vault at: {vault_dir}")
    print(f"Output database: {database_file}")
    
    conn = sqlite3.connect(database_file)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS notes (
            path TEXT PRIMARY KEY,
            filename TEXT,
            category TEXT,
            energy INTEGER,
            sentiment REAL,
            sentiment_labels TEXT,
            tags TEXT,
            summary_snippet TEXT,
            word_count INTEGER
        )
    """)
    
    ignored_dirs = {".obsidian", ".git", ".trash", "node_modules", ".venv", "__pycache__"}
    count = 0
    
    for root, dirs, files in os.walk(vault_dir):
        dirs[:] = [d for d in dirs if d not in ignored_dirs]
        for file in files:
            if not file.endswith(".md"):
                continue
            
            full_path = Path(root) / file
            rel_path = full_path.relative_to(vault_dir).as_posix()
            
            category = "general"
            if file.startswith("day "):
                category = "daily"
            elif file.startswith("review "):
                category = "review"
            elif rel_path.startswith("work/"):
                parts = rel_path.split("/")
                category = f"work/{parts[1]}" if len(parts) > 2 else "work"
                
            try:
                with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                    
                meta, body = parse_frontmatter(content)
                snippet = extract_key_lines(body)
                word_count = len(body.split())
                
                cur.execute("""
                    INSERT OR REPLACE INTO notes 
                    (path, filename, category, energy, sentiment, sentiment_labels, tags, summary_snippet, word_count)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    rel_path,
                    file,
                    category,
                    meta["energy"],
                    meta["sentiment"],
                    json.dumps(meta["sentiment_label"]),
                    json.dumps(meta["tags"]),
                    snippet,
                    word_count
                ))
                count += 1
            except Exception:
                pass

    conn.commit()
    conn.close()
    print(f"Successfully indexed {count} notes into {database_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract PKM metadata into SQLite index.")
    parser.add_argument("--vault", type=str, default=None, help="Path to vault root")
    parser.add_argument("--db", type=str, default=None, help="Path to output SQLite database")
    args = parser.parse_args()
    build_index(vault_path=args.vault, db_path=args.db)
