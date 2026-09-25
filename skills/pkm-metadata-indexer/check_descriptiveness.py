"""DESCRIPTIVENESS CHECKER FOR MARKDOWN NOTES.

Checks markdown notes for generic filenames, label headings, and missing descriptions:
  1. NON-DESCRIPTIVE FILENAME - too short or generic label
  2. LABEL HEADINGS - generic or too short ## headings
  3. MISSING DESCRIPTION - body over threshold with no frontmatter description

Usage:
  python check_descriptiveness.py VAULT_ROOT [NOTE_PATH ...]
  python check_descriptiveness.py VAULT_ROOT --min-words 800 --skip-dir sessions
  python check_descriptiveness.py VAULT_ROOT --warn-only
  python check_descriptiveness.py VAULT_ROOT --json

Exits 0 when clean or --warn-only, 1 when there are findings.
"""
import argparse
import json
import os
import re
import sys
from pathlib import Path

# Try importing from index_pkm_meta, fall back to local implementation
try:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from index_pkm_meta import parse_frontmatter, DESCRIPTION_MIN_WORDS
    HAS_INDEXER = True
except ImportError:
    HAS_INDEXER = False
    DESCRIPTION_MIN_WORDS = 600
    print("Warning: could not import index_pkm_meta, using local fallback", file=sys.stderr)

# Generic filename labels that indicate a non-descriptive name
GENERIC_FILENAME_LABELS = {
    "notes", "misc", "untitled", "meeting", "scratch", "todo", "ideas", "log",
    "summary", "temp", "wip", "readme", "index", "draft", "day note"
}

# Generic heading labels (measured top offenders)
GENERIC_HEADING_LABELS = {
    "sources", "at a glance", "the pitch", "why it stopped", "key docs", "related",
    "what shipped", "what was discussed", "further reading", "the lens", "what happened",
    "outcome", "summary", "notes", "next steps", "background", "context", "details",
    "results", "conclusion", "todo", "links", "references", "appendix", "overview",
    "why", "how", "status"
}

# Structural exemptions - filenames that should never be checked
STRUCTURAL_EXEMPT_FILENAMES = {"AGENTS.md", "CLAUDE.md", "README.md", "SKILL.md"}

# Frontmatter regex for local fallback
FRONTMATTER_RE = re.compile(r"^---\s*\r?\n(.*?)\r?\n---\s*(?:\r?\n|$)", re.DOTALL)


def parse_frontmatter_local(content: str) -> dict:
    """Local fallback for parsing frontmatter description."""
    match = FRONTMATTER_RE.match(content)
    if not match:
        return {"description": None, "repo": None, "url": None}

    frontmatter = match.group(1)
    meta = {"description": None, "repo": None, "url": None}

    # Parse description
    desc_scalar = re.search(r"^description:\s*(.+)$", frontmatter, re.MULTILINE)
    if desc_scalar:
        value = desc_scalar.group(1).strip()
        if value in (">", ">-", "|", "|-"):
            desc_block = re.search(r"^description:\s*[>|][-]?\s*\n((?:[ \t]+[^\n]*\n?)+)", frontmatter, re.MULTILINE)
            if desc_block:
                meta["description"] = " ".join(desc_block.group(1).split())
        else:
            meta["description"] = value.strip('"\'')
    if meta["description"] is not None and not meta["description"].strip():
        meta["description"] = None

    # Parse repo and url for catalog card exemption
    repo_match = re.search(r"^repo:\s*(.+)$", frontmatter, re.MULTILINE)
    if repo_match:
        meta["repo"] = repo_match.group(1).strip()

    url_match = re.search(r"^url:\s*(.+)$", frontmatter, re.MULTILINE)
    if url_match:
        meta["url"] = url_match.group(1).strip()

    return meta


def is_exempt_filename(path: Path, stem_no_date: str, meta: dict) -> bool:
    """Check if a note is exempt from filename checks based on structural rules."""
    # Structural files
    if path.name in STRUCTURAL_EXEMPT_FILENAMES:
        return True  # Structural documentation, correctly named

    # Catalog cards: machine-written, correctly keyed by repo name
    if meta.get("repo") and meta.get("url"):
        return True

    # Day logs: correctly keyed by date
    if re.match(r"^\d{4}-\d{2}-\d{2}$", path.stem):
        return True

    # Concept/glossary notes: correctly named by bare term (no leading date)
    if not re.match(r"^\d{4}-\d{2}-\d{2}\s", path.stem):
        return True

    return False


def check_note(path: Path, min_words: int) -> dict:
    """Check a single note and return findings."""
    findings = {
        "path": str(path),
        "non_descriptive_filename": [],
        "label_headings": [],
        "missing_description": False,
        "word_count": 0,
    }

    try:
        content = path.read_text(encoding="utf-8", errors="ignore")
    except Exception as e:
        findings["error"] = str(e)
        return findings

    # Parse frontmatter
    if HAS_INDEXER:
        meta, body, _ = parse_frontmatter(content)
    else:
        meta = parse_frontmatter_local(content)
        fm_match = FRONTMATTER_RE.match(content)
        body = content[fm_match.end():] if fm_match else content

    word_count = len(body.split())
    findings["word_count"] = word_count

    # Strip leading date from stem for filename checks
    stem = path.stem
    stem_no_date = re.sub(r"^\d{4}-\d{2}-\d{2}\s+", "", stem)

    exempt = is_exempt_filename(path, stem_no_date, meta)

    # Check 1: Non-descriptive filename (skip if exempt)
    if not exempt:
        word_parts = stem_no_date.split()
        if len(word_parts) < 4:
            findings["non_descriptive_filename"].append(f"too short ({len(word_parts)} words)")
        if stem_no_date.lower() in GENERIC_FILENAME_LABELS:
            findings["non_descriptive_filename"].append(f"generic label: {stem_no_date}")

    # Check 2: Label headings (skip if exempt)
    if not exempt:
        for match in re.finditer(r"^## (.+)$", body, re.MULTILINE):
            heading_text = match.group(1).strip()
            word_parts = heading_text.split()
            if len(word_parts) <= 3:
                # Check if it's a bare date
                if re.match(r"^\d{4}-\d{2}-\d{2}$", heading_text):
                    findings["label_headings"].append(f"bare date: {heading_text}")
                elif heading_text.lower() in GENERIC_HEADING_LABELS:
                    findings["label_headings"].append(f"generic: {heading_text}")
                elif len(word_parts) <= 3:
                    findings["label_headings"].append(f"too short ({len(word_parts)} words): {heading_text}")
            elif heading_text.lower() in GENERIC_HEADING_LABELS:
                findings["label_headings"].append(f"generic: {heading_text}")

    # Check 3: Missing description (skip catalog cards only)
    is_catalog_card = meta.get("repo") and meta.get("url")
    if not is_catalog_card and word_count > min_words and not meta.get("description"):
        findings["missing_description"] = True

    return findings


def main():
    parser = argparse.ArgumentParser(description="Check notes for descriptive filenames and headings")
    parser.add_argument("vault_root", help="Path to the vault root directory")
    parser.add_argument("note_paths", nargs="*", help="Specific note paths to check (relative to vault root)")
    parser.add_argument("--min-words", type=int, default=DESCRIPTION_MIN_WORDS,
                       help=f"Minimum word count for description requirement (default {DESCRIPTION_MIN_WORDS})")
    parser.add_argument("--skip-dir", action="append", dest="skip_dirs", default=[],
                       help="Skip a top-level directory (repeatable)")
    parser.add_argument("--warn-only", action="store_true",
                       help="Always exit 0 (warnings only)")
    parser.add_argument("--json", action="store_true",
                       help="Output machine-readable JSON")

    args = parser.parse_args()

    vault_root = Path(args.vault_root).resolve()
    if not vault_root.is_dir():
        print(f"error: vault root {vault_root} is not a directory", file=sys.stderr)
        sys.exit(1)

    # Collect notes to check
    notes_to_check = []
    if args.note_paths:
        for note_path in args.note_paths:
            path = Path(note_path)
            if not path.is_absolute():
                path = vault_root / note_path
            if path.exists() and path.suffix == ".md":
                notes_to_check.append(path)
    else:
        # Walk the vault
        for root, dirs, files in os.walk(vault_root):
            # Filter out ignored and skipped directories
            dirs[:] = [d for d in dirs if d not in {".obsidian", ".git", ".trash"}
                      and d not in args.skip_dirs]

            for filename in files:
                if filename.endswith(".md"):
                    notes_to_check.append(Path(root) / filename)

    # Check all notes and collect findings
    all_findings = []
    for path in notes_to_check:
        findings = check_note(path, args.min_words)
        if (findings.get("non_descriptive_filename") or
            findings.get("label_headings") or
            findings.get("missing_description")):
            all_findings.append(findings)

    # Sort by word count, descending (biggest notes first)
    all_findings.sort(key=lambda x: x["word_count"], reverse=True)

    # Output results
    if args.json:
        print(json.dumps(all_findings, indent=2))
    else:
        for finding in all_findings:
            print(f"\n{finding['path']} ({finding['word_count']} words)")
            for issue in finding.get("non_descriptive_filename", []):
                print(f"  NON-DESCRIPTIVE FILENAME: {issue}")
            for heading in finding.get("label_headings", []):
                print(f"  LABEL HEADING: {heading}")
            if finding.get("missing_description"):
                print(f"  MISSING DESCRIPTION: note over {args.min_words} words")

        # Summary counts
        print("\n--- Summary ---")
        filename_issues = sum(1 for f in all_findings if f.get("non_descriptive_filename"))
        heading_issues = sum(1 for f in all_findings if f.get("label_headings"))
        missing_desc = sum(1 for f in all_findings if f.get("missing_description"))
        print(f"Non-descriptive filenames: {filename_issues}")
        print(f"Notes with label headings: {heading_issues}")
        print(f"Missing descriptions:      {missing_desc}")
        print(f"Total notes with issues:   {len(all_findings)}")

    # Exit code
    has_errors = len(all_findings) > 0
    sys.exit(0 if args.warn_only or not has_errors else 1)


if __name__ == "__main__":
    main()
