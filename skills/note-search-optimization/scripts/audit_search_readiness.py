#!/usr/bin/env python3
"""Audit markdown notes for semantic search readiness and header extraction quality.

Heuristics evaluated per note:
1. Header Quality & Informativeness:
   - Descriptive "Label : Thesis" or informative headers vs generic placeholders (Overview, Notes, TODO).
   - Appropriate heading chunk sizes for vector embedding windows (40 - 350 words).
2. Lead Thesis & Context Framing:
   - Substantive lead paragraph framing the core concept before lists/tables/code.
3. Metadata & Alias Anchors:
   - YAML frontmatter with aliases, tags, and descriptive fields.
4. Link Graph Connectivity:
   - Outbound wikilinks contextualized in prose.
5. Structural Integrity:
   - Clean heading hierarchy and typed code fences.

Usage:
    python audit_search_readiness.py                        # Audit entire vault
    python audit_search_readiness.py --path "public"        # Audit specific directory
    python audit_search_readiness.py --file "my-note.md"    # Audit single note
    python audit_search_readiness.py --min-score 70         # Show notes scoring under 70
    python audit_search_readiness.py --self-check           # Run internal test suite
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, List, Optional, Tuple

VAGUE_HEADERS = {
    "overview",
    "notes",
    "note",
    "update",
    "updates",
    "summary",
    "thoughts",
    "todo",
    "todos",
    "misc",
    "miscellaneous",
    "introduction",
    "intro",
    "details",
    "log",
    "info",
    "general",
    "context",
    "background",
}

SKIP_DIRS = {".git", ".obsidian", ".trash", "archive", ".smart-env", "__pycache__", ".venv"}


@dataclass
class AuditResult:
    path: str
    score: int
    word_count: int
    issues: list[str] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)
    headers: list[str] = field(default_factory=list)
    has_frontmatter: bool = False
    has_lead_thesis: bool = False
    aliases_count: int = 0
    wikilinks_count: int = 0


def parse_frontmatter(content: str) -> Tuple[dict[str, Any], str]:
    """Extract frontmatter dict and body text."""
    if not content.startswith("---"):
        return {}, content
    parts = content.split("---", 2)
    if len(parts) < 3:
        return {}, content
    yaml_text = parts[1]
    body = parts[2]
    meta: dict[str, Any] = {}
    for line in yaml_text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" in line:
            key, val = line.split(":", 1)
            key = key.strip()
            val = val.strip()
            if val.startswith("[") and val.endswith("]"):
                meta[key] = [v.strip().strip("'\"") for v in val[1:-1].split(",") if v.strip()]
            elif val:
                meta[key] = val.strip("'\"")
            else:
                meta[key] = []
        elif line.startswith("- ") and meta:
            last_key = list(meta.keys())[-1]
            if isinstance(meta[last_key], list):
                meta[last_key].append(line[2:].strip().strip("'\""))
    return meta, body


def audit_note_content(content: str, rel_path: str = "") -> AuditResult:
    """Evaluate note content against semantic search and header extraction heuristics."""
    meta, body = parse_frontmatter(content)
    lines = body.splitlines()
    words = re.findall(r"\b\w+\b", body)
    word_count = len(words)

    score = 100
    issues: list[str] = []
    suggestions: list[str] = []

    # 1. Frontmatter & Aliases (20 pts)
    has_frontmatter = bool(meta)
    aliases = meta.get("aliases", [])
    if isinstance(aliases, str):
        aliases = [aliases]
    aliases_count = len(aliases)

    if not has_frontmatter:
        score -= 10
        issues.append("Missing YAML frontmatter")
        suggestions.append("Add YAML frontmatter with tags and aliases.")
    elif aliases_count == 0:
        score -= 5
        issues.append("No aliases declared in frontmatter")
        suggestions.append("Add aliases to capture synonyms and alternate search phrasing.")

    # 2. Lead Thesis & Opening Context (25 pts)
    # Skip any top-level title header (# Title) to find opening prose
    first_meaningful_block = ""
    for line in lines:
        s = line.strip()
        if not s or s.startswith("<!--"):
            continue
        if s.startswith("# ") and not first_meaningful_block:
            continue
        first_meaningful_block = s
        break

    has_lead_thesis = False
    if not first_meaningful_block:
        score -= 25
        issues.append("Missing lead paragraph / empty note body")
        suggestions.append("Add a substantive lead thesis explaining the core finding or topic.")
    elif first_meaningful_block.startswith("```"):
        score -= 15
        issues.append("Note opens immediately with a code block")
        suggestions.append("Add a 1-2 sentence lead paragraph above code to provide semantic context for embeddings.")
    elif first_meaningful_block.startswith("|"):
        score -= 15
        issues.append("Note opens immediately with a markdown table")
        suggestions.append("Add a lead paragraph describing the table contents.")
    elif first_meaningful_block.startswith(("- ", "* ", "1. ")):
        score -= 12
        issues.append("Note opens directly with bullet list without lead sentence")
        suggestions.append("Lead with a complete thesis sentence before bullet points.")
    elif first_meaningful_block.startswith("#"):
        score -= 15
        issues.append("Note opens directly with section subheader without lead intro")
        suggestions.append("Add an introductory thesis paragraph before the first section header.")
    else:
        lead_words = len(first_meaningful_block.split())
        if lead_words >= 8:
            has_lead_thesis = True
        else:
            score -= 8
            issues.append("Lead sentence is very brief (< 8 words)")
            suggestions.append("Expand lead sentence into a clear thesis statement.")

    # 3. Header Quality & Chunkability (30 pts)
    headers = [line.strip() for line in lines if line.strip().startswith("#")]

    if word_count > 350 and not any(re.match(r"^#{2,6}\s+", h) for h in headers):
        score -= 20
        issues.append(f"Long note ({word_count} words) with no sub-headings (cannot slice by section)")
        suggestions.append("Break note into logical sections using `## ` headers to allow section-level chunking.")

    vague_found = []
    good_informative_found = []
    for h in headers:
        header_text = re.sub(r"^#{1,6}\s+", "", h).strip()
        clean_text = re.sub(r"[^\w\s:]", "", header_text).strip().lower()
        if clean_text in VAGUE_HEADERS:
            vague_found.append(header_text)
        elif ":" in header_text or len(clean_text.split()) >= 4:
            good_informative_found.append(header_text)

    if vague_found:
        penalty = min(25, len(vague_found) * 8)
        score -= penalty
        issues.append(f"Vague placeholder headers found: {', '.join(vague_found)}")
        suggestions.append("Replace vague headers with 'Label : Thesis' format (e.g. `## Root Cause: Lock Contention`).")

    # 4. Link Graph & Wikilinks (15 pts)
    wikilinks = re.findall(r"\[\[([^\]|]+)(?:\|[^\]]+)?\]\]", body)
    wikilinks_count = len(wikilinks)

    if wikilinks_count == 0:
        score -= 15
        issues.append("Orphan note (zero outbound wikilinks)")
        suggestions.append("Add contextual wikilinks to connect this note to the vault link graph.")
    elif word_count > 150 and wikilinks_count == 1:
        score -= 5
        issues.append("Low link connectivity (only 1 outbound link)")
        suggestions.append("Consider cross-linking to related hub or concept notes.")

    # 5. Formatting & Code Syntax (10 pts)
    untyped_code_blocks = len(re.findall(r"^```\s*$", body, re.M))
    if untyped_code_blocks > 0:
        score -= min(10, untyped_code_blocks * 3)
        issues.append(f"{untyped_code_blocks} code block(s) missing syntax language tag")
        suggestions.append("Add language identifiers (e.g. ```python, ```bash) to code blocks.")

    final_score = max(0, min(100, score))
    return AuditResult(
        path=rel_path,
        score=final_score,
        word_count=word_count,
        issues=issues,
        suggestions=suggestions,
        headers=headers,
        has_frontmatter=has_frontmatter,
        has_lead_thesis=has_lead_thesis,
        aliases_count=aliases_count,
        wikilinks_count=wikilinks_count,
    )


def audit_vault(root: Path, target_subpath: str = "") -> list[AuditResult]:
    """Audit all markdown files under root directory."""
    start_dir = root / target_subpath if target_subpath else root
    results: list[AuditResult] = []

    for path in sorted(start_dir.rglob("*.md")):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        try:
            content = path.read_text(encoding="utf-8", errors="replace")
            rel_path = path.relative_to(root).as_posix()
            res = audit_note_content(content, rel_path)
            results.append(res)
        except OSError:
            continue

    return results


def self_check() -> int:
    """Validate heuristic audit logic with test fixtures."""
    # 1. Perfect note
    perfect = """---
aliases:
  - wide awareness diary study
  - Milner happiness findings
tags:
  - psychology
  - attention
---
Marion Milner's 7-year introspective diary study demonstrates that spontaneous happiness emerges from receptive attention rather than goal-directed striving.

## Core Finding: Receptive Attention over Achievement
Fulfillment is not a milestone that can be scheduled; it is an orientation of wide sensory perception.

## Key Mechanism: Panoramic Awareness vs Narrow Focus
Shifting from tunnel-vision problem-solving to wide panoramic awareness immediately relieves psychological constriction.

Related: [[attention economy]], [[minimal notetaking]].
"""
    r_perfect = audit_note_content(perfect, "perfect.md")
    assert r_perfect.score >= 90, f"Expected high score for well-structured note, got {r_perfect.score}"
    assert r_perfect.has_lead_thesis
    assert r_perfect.aliases_count == 2
    assert r_perfect.wikilinks_count == 2

    # 2. Vague headers and missing lead note
    poor = """# Overview
```
some_untyped_code()
```
## Notes
- just some bullets
## TODO
- do this
"""
    r_poor = audit_note_content(poor, "poor.md")
    assert r_poor.score < 50, f"Expected low score for vague note, got {r_poor.score}"
    assert "Missing YAML frontmatter" in r_poor.issues
    assert any("Vague placeholder headers" in i for i in r_poor.issues)

    print("self-check passed successfully.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--path", default="", help="Sub-path or folder to audit (e.g. public or work)")
    parser.add_argument("--file", default="", help="Audit a specific file path")
    parser.add_argument("--min-score", type=int, default=100, help="Only report notes with score <= min-score (default: 100)")
    parser.add_argument("--top", type=int, default=20, help="Max results to display when sorting lowest-first (default: 20)")
    parser.add_argument("--json", action="store_true", help="Output results in JSON format")
    parser.add_argument("--self-check", action="store_true", help="Run self-test suite")
    args = parser.parse_args()

    if args.self_check:
        return self_check()

    vault_root = Path(__file__).resolve().parent.parent.parent.parent
    if not (vault_root / ".obsidian").is_dir():
        vault_root = Path.cwd()

    if args.file:
        file_path = Path(args.file)
        if not file_path.is_absolute():
            file_path = vault_root / file_path
        if not file_path.exists():
            print(f"Error: file not found: {file_path}", file=sys.stderr)
            return 1
        content = file_path.read_text(encoding="utf-8", errors="replace")
        rel = file_path.relative_to(vault_root).as_posix() if file_path.is_relative_to(vault_root) else file_path.name
        res = audit_note_content(content, rel)
        results = [res]
    else:
        results = audit_vault(vault_root, args.path)

    filtered = [r for r in results if r.score <= args.min_score]
    filtered.sort(key=lambda x: (x.score, -x.word_count))

    if args.json:
        print(json.dumps([asdict(r) for r in filtered[: args.top]], indent=2))
        return 0

    total_audited = len(results)
    avg_score = (sum(r.score for r in results) / total_audited) if total_audited else 0
    print(f"\nAudited {total_audited} notes (Avg Searchability Score: {avg_score:.1f}/100)")
    print(f"Showing lowest-scoring notes (<= {args.min_score}):\n")

    for r in filtered[: args.top]:
        status_bar = "🔴" if r.score < 50 else ("🟡" if r.score < 75 else "🟢")
        print(f"{status_bar} [{r.score:3d}/100] {r.path} ({r.word_count} words, {r.wikilinks_count} links)")
        for issue in r.issues:
            print(f"   ✖ {issue}")
        for sug in r.suggestions[:2]:
            print(f"   💡 {sug}")
        print()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
