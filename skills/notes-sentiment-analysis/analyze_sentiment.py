"""
High-speed multithreaded batch sentiment analysis for Obsidian vault notes.
See: _scripts/notes sentiment analysis.md
"""

import argparse
import hashlib
import json
import os
import random
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import frontmatter
from tqdm import tqdm

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

def find_vault_root() -> Path:
    current = Path(__file__).resolve().parent
    for p in [Path.cwd(), current, current.parent, current.parent.parent, current.parent.parent.parent]:
        if (p / ".obsidian").exists():
            return p
    return current.parent.parent.parent

VAULT_ROOT = find_vault_root()

EXCLUDED_FOLDERS = {
    ".obsidian", ".git", ".github", ".smart-env", ".smart-connections",
    "image", "Excalidraw", "Strava", "Google Keep", "google-drive",
}

MIN_CONTENT_LENGTH = 30  # skip near-empty notes

BATCH_PROMPT = """\
Analyze the sentiment of each note provided below under --- NOTE N --- headers.

Return ONLY a JSON object mapping each note id string (e.g. "0", "1") to its analysis object.

Example JSON output structure:
{
  "0": {
    "sentiment": [3, 5],
    "sentiment_label": ["lonely", "hopeful"],
    "energy": 4,
    "tags": ["journal", "relationship"]
  }
}

Field definitions per note:
- sentiment: Array of 1-10 scores (1=deeply negative, 5=neutral, 10=very positive). First entry is the dominant mood. Add secondary scores if the note has clear emotional shifts.
- sentiment_label: Array of one-word mood labels corresponding 1-to-1 with sentiment scores.
- energy: Author's activation level from 1 (drained/numb) to 10 (wired/restless). Omit if the note has no emotional content.
- tags: List of relevant tags covering note type (journal, medical, technical, etc.), topics, and life areas.

Evaluate each NOTE block independently without leaking context between notes.
"""

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def content_hash(text: str) -> str:
    """MD5 hash of note body, truncated to 8 hex chars."""
    return hashlib.md5(text.encode("utf-8")).hexdigest()[:8]


def is_excluded(path: Path) -> bool:
    """Check if a path is in an excluded folder."""
    parts = path.relative_to(VAULT_ROOT).parts
    return any(part in EXCLUDED_FOLDERS for part in parts)


def collect_notes(folder: str | None = None) -> list[Path]:
    """Collect all .md files, respecting exclusions. Can be a folder or single file."""
    if folder:
        target = VAULT_ROOT / folder
        if target.is_file() and target.suffix == ".md":
            return [target] if not is_excluded(target) else []
        root = target
    else:
        root = VAULT_ROOT

    notes = []
    for path in root.rglob("*.md"):
        if not is_excluded(path):
            notes.append(path)
    return sorted(notes)


def load_note(path: Path) -> frontmatter.Post:
    """Load a note with frontmatter, handling encoding issues."""
    try:
        return frontmatter.load(path, encoding="utf-8")
    except Exception:
        return frontmatter.load(path, encoding="utf-8-sig")


def save_note(path: Path, post: frontmatter.Post) -> None:
    """Save a note, preserving line endings."""
    content = frontmatter.dumps(post)
    path.write_text(content + "\n", encoding="utf-8")


def call_llm_batch(batch_items: list[tuple[int, str]], client, provider: str = "gemini", model_name: str = "gemini-3.6-flash", max_retries: int = 4) -> dict | None:
    """
    Call Gemini Flash / Groq API for a batch of notes using XML note boundaries.
    batch_items: list of (idx, note_body_text)
    Returns dict mapping idx (int) -> result dict
    """
    formatted_notes = []
    for idx, body in batch_items:
        formatted_notes.append(f"--- NOTE {idx} ---\n{body}\n")

    full_prompt = BATCH_PROMPT + "\n" + "\n".join(formatted_notes)

    for attempt in range(max_retries):
        try:
            if provider == "groq":
                response = client.chat.completions.create(
                    model=model_name,
                    messages=[{"role": "user", "content": full_prompt}],
                    response_format={"type": "json_object"}
                )
                text = response.choices[0].message.content.strip()
            else:
                response = client.models.generate_content(
                    model=model_name,
                    contents=full_prompt,
                )
                text = response.text.strip()

            if text.startswith("```"):
                text = text.split("\n", 1)[1]
                if text.endswith("```"):
                    text = text[:-3]
                text = text.strip()

            data = json.loads(text)
            normalized = {}
            for k, v in data.items():
                clean_k = str(k).replace("NOTE_", "").replace("note_", "").strip()
                if clean_k.isdigit():
                    normalized[int(clean_k)] = v
            return normalized

        except json.JSONDecodeError:
            time.sleep(1)
        except Exception as e:
            err_str = str(e)
            if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str or "rate_limit" in err_str:
                time.sleep(3 * (attempt + 1))
            else:
                time.sleep(1)

    return None


def merge_tags(existing_tags: list, new_tags: list) -> list:
    """Merge new tags into existing, preserving order, no duplicates."""
    seen = set()
    merged = []
    for tag in existing_tags + new_tags:
        tag_lower = str(tag).lower().strip()
        if tag_lower not in seen:
            seen.add(tag_lower)
            merged.append(tag_lower)
    return merged


def apply_result(path: Path, result: dict, current_hash: str) -> None:
    """Apply analysis result to note frontmatter."""
    post = load_note(path)

    sentiment = result.get("sentiment", [5])
    sentiment_label = result.get("sentiment_label", ["unclear"])
    energy = result.get("energy")
    new_tags = result.get("tags", [])

    if isinstance(sentiment, int):
        sentiment = [sentiment]
    if isinstance(sentiment_label, str):
        sentiment_label = [str(sentiment_label)]

    sentiment = [max(1, min(10, s)) for s in sentiment]

    post["sentiment"] = sentiment
    post["sentiment-label"] = sentiment_label
    
    if energy is not None and isinstance(energy, (int, float)):
        post["energy"] = max(1, min(10, int(energy)))
    elif "energy" in post.metadata:
        del post.metadata["energy"]

    post["sentiment-hash"] = current_hash

    existing_tags = post.metadata.get("tags", [])
    if existing_tags is None:
        existing_tags = []
    if isinstance(existing_tags, str):
        existing_tags = [existing_tags]
    merged = merge_tags(existing_tags, new_tags)
    if merged:
        post["tags"] = merged
    elif "tags" in post.metadata:
        del post.metadata["tags"]

    save_note(path, post)


def process_chunk(chunk: list[tuple[Path, str, str]], client, provider: str, model_name: str) -> int:
    """Process a single batch chunk of notes."""
    batch_items = [(idx, item[1]) for idx, item in enumerate(chunk)]
    results = call_llm_batch(batch_items, client, provider=provider, model_name=model_name)
    
    if not results:
        return 0

    success_count = 0
    for idx, (path, body, h) in enumerate(chunk):
        note_res = results.get(idx)
        if note_res and isinstance(note_res, dict):
            try:
                apply_result(path, note_res, h)
                success_count += 1
            except Exception:
                pass
    return success_count


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(
        description="High-speed multithreaded batch sentiment analysis for Obsidian"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Preview what would change without writing"
    )
    parser.add_argument(
        "--sample", type=int, default=None,
        help="Only process N random notes (for testing)"
    )
    parser.add_argument(
        "--force", action="store_true",
        help="Re-analyze all notes, ignoring content hash"
    )
    parser.add_argument(
        "--folder", type=str, default=None,
        help="Only analyze notes in a specific subfolder or file"
    )
    parser.add_argument(
        "--redo-factual", action="store_true",
        help="Re-analyze all notes currently labeled as factual"
    )
    parser.add_argument(
        "--batch-size", type=int, default=5,
        help="Number of notes to combine into a single API request (default: 5)"
    )
    parser.add_argument(
        "--workers", type=int, default=5,
        help="Number of parallel worker threads (default: 5)"
    )
    parser.add_argument(
        "--model", type=str, default="gemini-3.6-flash",
        help="Model to use (default: gemini-3.6-flash)"
    )
    args = parser.parse_args()

    provider = "gemini"
    api_key = os.environ.get("GEMINI_API_KEY")
    groq_key = os.environ.get("GROQ_API") or os.environ.get("GROQ_API_KEY")

    if groq_key:
        provider = "groq"
        api_key = groq_key
        if args.model == "gemini-3.6-flash":
            args.model = "llama-3.3-70b-versatile"
        from groq import Groq
        client = Groq(api_key=api_key)
    elif api_key:
        from google import genai
        client = genai.Client(api_key=api_key)
    else:
        print("Error: Neither GEMINI_API_KEY nor GROQ_API / GROQ_API_KEY environment variable set.")
        sys.exit(1)

    print(f"Vault: {VAULT_ROOT}")
    notes = collect_notes(args.folder)
    print(f"Found {len(notes)} candidate notes")

    if args.sample:
        notes = random.sample(notes, min(args.sample, len(notes)))
        print(f"Sampled {len(notes)} notes")

    if args.dry_run:
        print("DRY RUN — no files will be modified\n")

    # Pre-filter notes needing update
    to_process = []
    skipped_short = 0
    skipped_hash = 0
    skipped_factual = 0

    for p in notes:
        try:
            post = load_note(p)
            body = post.content.strip()
            if len(body) < MIN_CONTENT_LENGTH:
                skipped_short += 1
                continue

            # Check if factual
            labels = post.metadata.get("sentiment-label", [])
            if isinstance(labels, str):
                labels = [labels]
            tags = post.metadata.get("tags", [])
            if isinstance(tags, str):
                tags = [tags]
            
            is_factual = (
                (labels and str(labels[0]).lower() == "factual") or
                ("factual" in [str(t).lower() for t in tags]) or
                ("factual" in [str(l).lower() for l in labels])
            )

            if args.redo_factual:
                if not is_factual:
                    continue
            else:
                # Skip primary factual notes unless --force is specified
                if not args.force and is_factual:
                    skipped_factual += 1
                    continue

                h = content_hash(body)
                if not args.force and post.metadata.get("sentiment-hash") == h:
                    skipped_hash += 1
                    continue

            h = content_hash(body)
            to_process.append((p, body, h))
        except Exception:
            to_process.append((p, "", ""))

    print(f"To analyze: {len(to_process)} notes | Skipped (hash): {skipped_hash} | Skipped (short): {skipped_short} | Skipped (factual): {skipped_factual}")

    if not to_process:
        print("All notes are up to date!")
        return

    # Create chunks
    batch_size = args.batch_size
    chunks = [to_process[i : i + batch_size] for i in range(0, len(to_process), batch_size)]
    
    analyzed = 0
    errors = 0

    if args.dry_run:
        print(f"[DRY RUN] Would process {len(to_process)} notes across {len(chunks)} batches.")
        return

    print(f"Starting multithreaded analysis with {args.workers} workers using {provider} ({args.model})...")

    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {executor.submit(process_chunk, chunk, client, provider, args.model): chunk for chunk in chunks}
        
        with tqdm(total=len(to_process), desc="Multithreaded Analyzing", unit="note") as pbar:
            for future in as_completed(futures):
                chunk = futures[future]
                try:
                    count = future.result()
                    analyzed += count
                    errors += (len(chunk) - count)
                except Exception as e:
                    errors += len(chunk)
                pbar.update(len(chunk))

    print(f"\n{'='*50}")
    print("Done!")
    print(f"  Analyzed:       {analyzed}")
    print(f"  Skipped (hash):  {skipped_hash}")
    print(f"  Skipped (short): {skipped_short}")
    print(f"  Errors:         {errors}")


if __name__ == "__main__":
    main()
