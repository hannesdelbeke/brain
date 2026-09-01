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

WIKILINK_RE = re.compile(r"\[\[(.*?)\]\]")
CODE_SPAN_RE = re.compile(r"`[^`\n]+`")
SCRIPT_CODE_SPAN_RE = re.compile(r"(?<!\[\[)`([a-zA-Z0-9_\-]+\.(?:py|sh|ps1|bat|ts|js))`(?!\s*\]\])")


def find_vault_root(start_path: Path = None) -> Path:
    """Find the enclosing Obsidian vault root or Git repository root."""
    if start_path is None:
        start_path = Path.cwd()
    start_path = start_path.resolve()
    if start_path.is_file():
        start_path = start_path.parent

    # 1. Search upwards for .obsidian directory
    curr = start_path
    for _ in range(10):
        if (curr / ".obsidian").exists():
            return curr
        if curr.parent == curr:
            break
        curr = curr.parent

    # 2. Search upwards for .git directory
    curr = start_path
    for _ in range(10):
        if (curr / ".git").exists():
            return curr
        if curr.parent == curr:
            break
        curr = curr.parent

    # 3. Fallback to parent of script directory
    return Path(__file__).resolve().parent.parent


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


def autolink_file_scripts(file_path: Path, valid_targets: set) -> bool:
    """Auto-convert backticked script filenames to [[filename.ext]] if they exist on disk."""
    if not file_path.exists() or file_path.suffix.lower() != ".md":
        return False

    in_fenced_code = False
    new_lines = []
    modified = False

    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            stripped = line.strip()
            if stripped.startswith("```"):
                in_fenced_code = not in_fenced_code
                new_lines.append(line)
                continue

            if in_fenced_code:
                new_lines.append(line)
                continue

            def _replace_script(match):
                fname = match.group(1)
                if fname.lower() in valid_targets or Path(fname).stem.lower() in valid_targets:
                    return f"[[{fname}]]"
                return match.group(0)

            new_line = SCRIPT_CODE_SPAN_RE.sub(_replace_script, line)
            if new_line != line:
                modified = True
            new_lines.append(new_line)

    if modified:
        with open(file_path, "w", encoding="utf-8") as f:
            f.writelines(new_lines)

    return modified


def main():
    args = sys.argv[1:]
    fix_mode = "--fix" in args
    if fix_mode:
        args = [a for a in args if a != "--fix"]

    vault_override = None
    if "--vault" in args:
        v_idx = args.index("--vault")
        if v_idx + 1 < len(args):
            vault_override = Path(args[v_idx + 1]).resolve()
            args = args[:v_idx] + args[v_idx + 2 :]

    files_to_check = []
    if args:
        files_to_check = [Path(arg).resolve() for arg in args]

    if vault_override:
        root = vault_override
    elif files_to_check:
        root = find_vault_root(files_to_check[0])
    else:
        root = find_vault_root()

    if not files_to_check:
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

    if fix_mode:
        for file_path in files_to_check:
            if autolink_file_scripts(file_path, valid_targets):
                rel = (
                    file_path.relative_to(root).as_posix()
                    if file_path.is_relative_to(root)
                    else file_path.name
                )
                print(f"[AUTO-FIX] Converted script code spans to wikilinks in {rel}")

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
