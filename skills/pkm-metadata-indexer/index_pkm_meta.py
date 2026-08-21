"""
PKM Metadata, Section Embeddings & Graph Indexer.
Extracts:
1. Note-level YAML frontmatter (energy, sentiment, tags) & snippets -> `notes` table
2. Heading-level sections (^## ) with bge-small-en-v1.5 embeddings & SHA256 cache -> `sections` table
3. Wikilink graph edges [[target]] -> `edges` table
"""

import os
import sys
import re
import json
import sqlite3
import hashlib
import argparse
import numpy as np
from pathlib import Path

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

try:
    from fastembed import TextEmbedding
    HAS_FASTEMBED = True
except ImportError:
    HAS_FASTEMBED = False

def find_vault_root():
    current = Path.cwd().resolve()
    for parent in [current, *current.parents]:
        if (parent / ".obsidian").exists() or (parent / ".git").exists():
            return parent
    return current

def get_sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()

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
    extracted = []
    for line in body.splitlines():
        line_clean = line.strip()
        if not line_clean:
            continue
        if line_clean.startswith("#") or line_clean.startswith("- [ ]") or line_clean.startswith("- [x]") or line_clean.startswith("- "):
            if len(line_clean) > 200:
                line_clean = line_clean[:200] + "..."
            extracted.append(line_clean)
            if len(extracted) >= max_lines:
                break
    return "\n".join(extracted)

def extract_wikilinks(content):
    """Extract clean target note titles from [[target|alias]] or [[target#heading]]."""
    matches = re.findall(r"\[\[([^\]]+)\]\]", content)
    targets = set()
    for m in matches:
        target = m.split("|")[0].split("#")[0].strip()
        if target:
            targets.add(target)
    return list(targets)

def parse_sections(file_stem, body):
    """
    Split note into sections.
    If note has '## ' headings, splits on them.
    If atomic without '## ' headings, returns 1 section using file_stem as heading.
    """
    lines = body.splitlines()
    sections = []
    current_heading = file_stem
    current_lines = []
    start_line = 1
    
    for idx, line in enumerate(lines, start=1):
        if line.startswith("## "):
            if current_lines:
                sec_text = "\n".join(current_lines).strip()
                if sec_text:
                    sections.append((current_heading, start_line, sec_text))
            current_heading = line[3:].strip()
            current_lines = [line]
            start_line = idx
        else:
            current_lines.append(line)
            
    if current_lines:
        sec_text = "\n".join(current_lines).strip()
        if sec_text:
            sections.append((current_heading, start_line, sec_text))
            
    return sections

def build_index(vault_path=None, db_path=None, skip_embeddings=False):
    vault_dir = Path(vault_path).resolve() if vault_path else find_vault_root()
    database_file = Path(db_path).resolve() if db_path else vault_dir / ".obsidian" / "pkm_index.db"
    database_file.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"Indexing PKM vault at: {vault_dir}")
    print(f"Database location: {database_file}")
    
    conn = sqlite3.connect(database_file)
    cur = conn.cursor()
    
    # 1. Notes table
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
    
    # 2. Sections table (with vector blob)
    cur.execute("DROP TABLE IF EXISTS sections")
    cur.execute("""
        CREATE TABLE IF NOT EXISTS sections (
            id TEXT PRIMARY KEY,
            path TEXT,
            heading TEXT,
            start_line INTEGER,
            sha256 TEXT,
            vector BLOB
        )
    """)
    cur.execute("CREATE INDEX IF NOT EXISTS idx_sections_path ON sections(path)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_sections_sha ON sections(sha256)")
    
    # 3. Edges table (link graph)
    cur.execute("DROP TABLE IF EXISTS edges")
    cur.execute("""
        CREATE TABLE IF NOT EXISTS edges (
            source TEXT,
            target TEXT,
            PRIMARY KEY (source, target)
        )
    """)
    cur.execute("CREATE INDEX IF NOT EXISTS idx_edges_source ON edges(source)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_edges_target ON edges(target)")
    
    # Load existing section hashes for incremental caching
    cur.execute("SELECT id, sha256 FROM sections WHERE vector IS NOT NULL")
    existing_hashes = dict(cur.fetchall())
    
    ignored_dirs = {".obsidian", ".git", ".trash", "node_modules", ".venv", "__pycache__"}
    seen_paths = set()
    seen_section_ids = set()
    
    notes_batch = []
    edges_batch = []
    sections_to_embed = [] # list of (sec_id, rel_path, heading, start_line, sec_hash, sec_text)
    unchanged_sections_count = 0
    
    for root, dirs, files in os.walk(vault_dir):
        dirs[:] = [d for d in dirs if d not in ignored_dirs]
        for file in files:
            if not file.endswith(".md"):
                continue
            
            full_path = Path(root) / file
            rel_path = full_path.relative_to(vault_dir).as_posix()
            file_stem = full_path.stem
            seen_paths.add(rel_path)
            
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
                
                notes_batch.append((
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
                
                # Wikilinks
                targets = extract_wikilinks(content)
                for t in targets:
                    edges_batch.append((file_stem, t))
                    
                # Sections
                parsed_sec = parse_sections(file_stem, body)
                for heading, start_line, sec_text in parsed_sec:
                    sec_id = f"{rel_path}#{heading}"
                    seen_section_ids.add(sec_id)
                    sec_hash = get_sha256(sec_text)
                    
                    if skip_embeddings:
                        if sec_id not in existing_hashes:
                            sections_to_embed.append((sec_id, rel_path, heading, start_line, sec_hash, sec_text))
                    else:
                        if sec_id in existing_hashes and existing_hashes[sec_id] == sec_hash:
                            unchanged_sections_count += 1
                        else:
                            # Needs embedding
                            sections_to_embed.append((sec_id, rel_path, heading, start_line, sec_hash, sec_text))
                            
            except Exception:
                pass

    # Save notes
    cur.executemany("""
        INSERT OR REPLACE INTO notes 
        (path, filename, category, energy, sentiment, sentiment_labels, tags, summary_snippet, word_count)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, notes_batch)
    
    # Save edges
    cur.execute("DELETE FROM edges")
    cur.executemany("INSERT OR IGNORE INTO edges (source, target) VALUES (?, ?)", edges_batch)
    
    # Cleanup deleted sections
    if seen_section_ids:
        cur.execute("SELECT id FROM sections")
        all_db_sec = [r[0] for r in cur.fetchall()]
        stale_sec = [sid for sid in all_db_sec if sid not in seen_section_ids]
        if stale_sec:
            cur.executemany("DELETE FROM sections WHERE id = ?", [(sid,) for sid in stale_sec])
            print(f"Pruned {len(stale_sec)} deleted sections from index.")
            
    conn.commit()
    print(f"Indexed {len(notes_batch)} notes and {len(edges_batch)} graph edges.")
    print(f"Sections: {unchanged_sections_count} cached/unchanged, {len(sections_to_embed)} new or modified.")

    # Embed new/modified sections or save placeholders
    if sections_to_embed:
        if skip_embeddings or not HAS_FASTEMBED:
            save_sec_batch = [(s[0], s[1], s[2], s[3], s[4], None) for s in sections_to_embed]
            cur.executemany("""
                INSERT OR REPLACE INTO sections (id, path, heading, start_line, sha256, vector)
                VALUES (?, ?, ?, ?, ?, ?)
            """, save_sec_batch)
            conn.commit()
            print(f"Recorded {len(save_sec_batch)} section metadata records.")
        else:
            print(f"Computing embeddings for {len(sections_to_embed)} sections with BAAI/bge-small-en-v1.5...")
            model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
            texts = [s[5] for s in sections_to_embed]
            
            # Embed in batches
            embeddings = list(model.embed(texts, batch_size=128))
            
            save_sec_batch = []
            for (sec_id, rel_path, heading, start_line, sec_hash, _), vec in zip(sections_to_embed, embeddings):
                vec_np = np.array(vec, dtype=np.float32)
                # Normalize vector to unit length for fast dot product cosine similarity
                norm = np.linalg.norm(vec_np)
                if norm > 0:
                    vec_np = vec_np / norm
                save_sec_batch.append((sec_id, rel_path, heading, start_line, sec_hash, vec_np.tobytes()))
                
            cur.executemany("""
                INSERT OR REPLACE INTO sections (id, path, heading, start_line, sha256, vector)
                VALUES (?, ?, ?, ?, ?, ?)
            """, save_sec_batch)
            conn.commit()
            print(f"Successfully saved {len(save_sec_batch)} section embeddings.")

    conn.close()
    print("Indexing complete.")

def search_index(query, vault_path=None, db_path=None, limit=10):
    vault_dir = Path(vault_path).resolve() if vault_path else find_vault_root()
    database_file = Path(db_path).resolve() if db_path else vault_dir / ".obsidian" / "pkm_index.db"
    
    if not database_file.exists():
        print(f"Index database not found at {database_file}. Run indexing first.")
        return []

    conn = sqlite3.connect(database_file)
    cur = conn.cursor()

    # 1. Lexical search across notes and sections
    clean_q = re.sub(r"[^\w\s]", "", query).strip()
    lex_results = {}
    if clean_q:
        words = clean_q.split()
        like_clauses = " AND ".join(["(path LIKE ? OR heading LIKE ?)" for _ in words])
        like_params = []
        for w in words:
            like_params.extend([f"%{w}%", f"%{w}%"])
            
        cur.execute(f"""
            SELECT path, heading, start_line, sha256
            FROM sections
            WHERE {like_clauses}
            LIMIT 50
        """, like_params)
        for rank, row in enumerate(cur.fetchall(), 1):
            key = f"{row[0]}#{row[1]}"
            lex_results[key] = {
                "path": row[0],
                "heading": row[1],
                "start_line": row[2],
                "lex_rank": rank
            }

    # 2. Vector Cosine Search (In-Memory CPU Matmul)
    vec_results = {}
    if HAS_FASTEMBED:
        cur.execute("SELECT path, heading, start_line, vector FROM sections WHERE vector IS NOT NULL")
        rows = cur.fetchall()
        if rows:
            matrix = np.array([np.frombuffer(row[3], dtype=np.float32) for row in rows])
            model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
            q_emb = np.array(list(model.embed([query]))[0], dtype=np.float32)
            norm = np.linalg.norm(q_emb)
            if norm > 0:
                q_emb = q_emb / norm
                
            scores = matrix @ q_emb
            top_indices = np.argsort(-scores)[:50]
            
            for rank, idx in enumerate(top_indices, 1):
                row = rows[idx]
                key = f"{row[0]}#{row[1]}"
                vec_results[key] = {
                    "path": row[0],
                    "heading": row[1],
                    "start_line": row[2],
                    "score": float(scores[idx]),
                    "vec_rank": rank
                }

    # 3. Reciprocal Rank Fusion (RRF)
    all_keys = set(lex_results.keys()).union(vec_results.keys())
    fused = []
    
    for key in all_keys:
        lex_item = lex_results.get(key)
        vec_item = vec_results.get(key)
        
        path = (vec_item or lex_item)["path"]
        heading = (vec_item or lex_item)["heading"]
        start_line = (vec_item or lex_item)["start_line"]
        
        # RRF formula: 1 / (60 + rank)
        score = 0.0
        if lex_item:
            score += 1.0 / (60.0 + lex_item["lex_rank"])
        if vec_item:
            score += 1.0 / (60.0 + vec_item["vec_rank"])
            
        fused.append({
            "path": path,
            "heading": heading,
            "start_line": start_line,
            "score": score,
            "raw_sim": vec_item["score"] if vec_item else None
        })

    fused.sort(key=lambda x: -x["score"])
    results = fused[:limit]
    conn.close()
    return results

def check_duplicate(title, vault_path=None, db_path=None):
    """Check nearest neighbors before creating a new note to prevent duplicates."""
    results = search_index(title, vault_path=vault_path, db_path=db_path, limit=5)
    print(f"\nDuplicate Check for proposed note: '{title}'")
    if not results:
        print("No similar notes found. Clear to create new note.")
        return
    
    print("Found potential existing matches in vault:")
    for idx, r in enumerate(results, 1):
        sim_str = f" (cosine: {r['raw_sim']:.3f})" if r['raw_sim'] else ""
        print(f"  {idx}. [{r['path']}:{r['start_line']}] #{r['heading']}{sim_str}")
    
    top = results[0]
    if top["raw_sim"] and top["raw_sim"] > 0.82:
        print(f"\nRecommendation: High semantic overlap (>0.82) with '{top['path']}'. Consider updating/appending instead of creating a duplicate.")
    else:
        print("\nRecommendation: Moderate/low overlap. Safe to create note or link to top matches.")

def query_links(note_title, vault_path=None, db_path=None):
    """Query inbound backlinks and outbound links for a note."""
    vault_dir = Path(vault_path).resolve() if vault_path else find_vault_root()
    database_file = Path(db_path).resolve() if db_path else vault_dir / ".obsidian" / "pkm_index.db"
    
    if not database_file.exists():
        print("Index database not found. Run indexing first.")
        return

    conn = sqlite3.connect(database_file)
    cur = conn.cursor()
    
    # Strip potential .md or brackets
    clean_title = note_title.replace(".md", "").strip("[]")
    
    cur.execute("SELECT target FROM edges WHERE source = ? ORDER BY target", (clean_title,))
    outbound = [row[0] for row in cur.fetchall()]
    
    cur.execute("SELECT source FROM edges WHERE target = ? ORDER BY source", (clean_title,))
    inbound = [row[0] for row in cur.fetchall()]
    
    print(f"\nLink Graph for: [[{clean_title}]]")
    print(f"Outbound links ({len(outbound)}):")
    for link in outbound[:20]:
        print(f"  -> [[{link}]]")
    if len(outbound) > 20:
        print(f"  ... (+{len(outbound) - 20} more)")
        
    print(f"\nInbound backlinks ({len(inbound)}):")
    for link in inbound[:20]:
        print(f"  <- [[{link}]]")
    if len(inbound) > 20:
        print(f"  ... (+{len(inbound) - 20} more)")
        
    conn.close()

def print_stats(vault_path=None, db_path=None):
    vault_dir = Path(vault_path).resolve() if vault_path else find_vault_root()
    database_file = Path(db_path).resolve() if db_path else vault_dir / ".obsidian" / "pkm_index.db"
    
    if not database_file.exists():
        print("Database not found.")
        return
        
    conn = sqlite3.connect(database_file)
    cur = conn.cursor()
    
    cur.execute("SELECT COUNT(*) FROM notes")
    notes_count = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*), COUNT(vector) FROM sections")
    sec_row = cur.fetchone()
    sec_count, vec_count = sec_row[0], sec_row[1]
    
    cur.execute("SELECT COUNT(*) FROM edges")
    edges_count = cur.fetchone()[0]
    
    db_size_mb = database_file.stat().st_size / (1024 * 1024)
    
    print("\n--- PKM Index Stats ---")
    print(f"Database location: {database_file}")
    print(f"Database size:     {db_size_mb:.2f} MB")
    print(f"Indexed Notes:     {notes_count:,}")
    print(f"Sections (chunks): {sec_count:,}")
    print(f"Vector Embeddings: {vec_count:,} (BGE-small 384-dim)")
    print(f"Link Graph Edges:  {edges_count:,}")
    print("-----------------------\n")
    conn.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract PKM metadata, graph edges, and section embeddings.")
    parser.add_argument("--vault", type=str, default=None, help="Path to vault root")
    parser.add_argument("--db", type=str, default=None, help="Path to output SQLite database")
    parser.add_argument("--skip-embeddings", action="store_true", help="Skip generating neural embeddings")
    parser.add_argument("--search", type=str, default=None, help="Run hybrid semantic search across vault sections")
    parser.add_argument("--check-duplicate", type=str, default=None, help="Check if candidate note title has existing near-duplicates")
    parser.add_argument("--links", type=str, default=None, help="Query inbound and outbound links for a note")
    parser.add_argument("--stats", action="store_true", help="Display indexer database statistics")
    parser.add_argument("--limit", type=int, default=10, help="Max search results to return")
    
    args = parser.parse_args()
    
    if args.stats:
        print_stats(vault_path=args.vault, db_path=args.db)
    elif args.search:
        results = search_index(args.search, vault_path=args.vault, db_path=args.db, limit=args.limit)
        print(f"\nHybrid Search Results for: '{args.search}'")
        for idx, r in enumerate(results, 1):
            sim_str = f" [cos: {r['raw_sim']:.3f}]" if r['raw_sim'] else ""
            print(f"{idx}. {r['path']}:{r['start_line']} #{r['heading']}{sim_str} (score: {r['score']:.4f})")
    elif args.check_duplicate:
        check_duplicate(args.check_duplicate, vault_path=args.vault, db_path=args.db)
    elif args.links:
        query_links(args.links, vault_path=args.vault, db_path=args.db)
    else:
        build_index(vault_path=args.vault, db_path=args.db, skip_embeddings=args.skip_embeddings)
