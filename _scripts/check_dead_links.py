#!/usr/bin/env python3
"""
Ultra-fast wikilink resolution validator for Obsidian PKM vaults.
Indexes all vault files and relative paths in ~30ms and validates wikilinks [[Target Note]].
Ignores wikilinks inside code spans `[[like_this]]` and fenced code blocks.
"""

import os
import re
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

VAULT_ROOT = Path(__file__).resolve().parent.parent
WIKILINK_RE = re.compile(r"\[\[(.*?)\]\]")
CODE_SPAN_RE = re.compile(r"`[^`\n]+`")


def build_vault_index(root: Path):
    """Index all filenames, stems, relative paths, and extensionless targets in sub-50ms."""
    valid_targets = set()

    for dirpath, dirnames, filenames in os.walk(root):
        # Prune hidden dirs, build/vendor directories
        dirnames[:] = [
            d
            for d in dirnames
            if not d.startswith(".")
            and d not in ("node_modules", "__pycache__", "venv", ".venv", ".obsidian", "dist", "build")
        ]

        rel_dir = Path(dirpath).relative_to(root)
        for fname in filenames:
            if fname.startswith("."):
                continue

            fname_lower = fname.lower()
            stem_lower = Path(fname).stem.lower()
            rel_path = (rel_dir / fname).as_posix().lower()

            valid_targets.add(fname_lower)
            valid_targets.add(stem_lower)
            valid_targets.add(rel_path)
            if fname_lower.endswith(".md"):
                valid_targets.add(rel_path[:-3])

    return valid_targets


def check_file_links(file_path: Path, valid_targets: set):
    """Check all wikilinks in a file and report unresolved targets."""
    broken = []
    if not file_path.exists() or not file_path.suffix.lower() == ".md":
        return broken

    in_fenced_code = False
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        for line_num, line in enumerate(f, 1):
            stripped = line.strip()
            if stripped.startswith("```"):
                in_fenced_code = not in_fenced_code
                continue

            if in_fenced_code:
                continue

            # Strip inline code spans so `[[example]]` isn't treated as a real vault link
            clean_line = CODE_SPAN_RE.sub("", line)

            for match in WIKILINK_RE.finditer(clean_line):
                raw = match.group(1).strip()
                if not raw:
                    continue
                # Strip alias pipe and heading anchor
                target = raw.split("|")[0].split("#")[0].strip()
                if not target:
                    continue

                target_clean = target.replace("\\", "/").lower()
                target_base = Path(target_clean).stem.lower()

                if target_clean not in valid_targets and target_base not in valid_targets:
                    broken.append((line_num, raw, target))

    return broken


def main():
    root = VAULT_ROOT
    files_to_check = []

    if len(sys.argv) > 1:
        files_to_check = [Path(arg).resolve() for arg in sys.argv[1:]]
    else:
        import subprocess

        try:
            res = subprocess.run(
                ["git", "status", "--porcelain"], capture_output=True, text=True, cwd=root
            )
            for line in res.stdout.splitlines():
                if len(line) > 3:
                    p = root / line[3:].strip().strip('"')
                    if p.suffix.lower() == ".md":
                        files_to_check.append(p)
        except Exception:
            pass

    if not files_to_check:
        print("No markdown files to check.")
        sys.exit(0)

    valid_targets = build_vault_index(root)
    total_broken = 0

    for file_path in files_to_check:
        broken = check_file_links(file_path, valid_targets)
        if broken:
            rel = (
                file_path.relative_to(root).as_posix()
                if file_path.is_relative_to(root)
                else file_path.name
            )
            print(f"\n[FAIL] Broken wikilinks in {rel}:")
            for line_num, raw, target in broken:
                print(f"  Line {line_num}: [[{raw}]] (Target '{target}' not found)")
                total_broken += 1

    if total_broken > 0:
        print(f"\nTotal broken wikilinks: {total_broken}")
        sys.exit(1)
    else:
        print(f"[PASS] All wikilinks in {len(files_to_check)} file(s) resolve successfully.")
        sys.exit(0)


if __name__ == "__main__":
    main()
