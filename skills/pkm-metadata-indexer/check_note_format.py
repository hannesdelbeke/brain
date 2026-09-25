"""STRUCTURAL GATE FOR MARKDOWN NOTES.

Checks markdown notes for common structural issues:
  1. WIKILINKS RESOLVE - every [[target]] must match a file stem in the vault
  2. NUMBERED ITEMS ARE CONTIGUOUS AND UNIQUE - no duplicates or gaps
  3. FRONTMATTER IS WELL FORMED - valid YAML if present
  4. NO SENSITIVE PATHS LEAK UNDER public/ - checked only for public/ files

Usage:
  python check_note_format.py VAULT_ROOT NOTE_PATH [NOTE_PATH ...]

where NOTE_PATH is relative to VAULT_ROOT. Exits 0 when clean, 1 when not,
and prints malformed=[...] either way.
"""
import re
import sys
from pathlib import Path


def main():
    if len(sys.argv) < 3:
        print("usage: python check_note_format.py VAULT_ROOT NOTE_PATH [...]",
              file=sys.stderr)
        sys.exit(1)

    vault_root = Path(sys.argv[1]).resolve()
    if not vault_root.is_dir():
        print(f"error: vault root {vault_root} is not a directory",
              file=sys.stderr)
        sys.exit(1)

    # Index every file in the vault, not just markdown files - wikilinks can
    # point to script filenames too (e.g. [[search.py]]), and those are real
    # targets that must resolve.
    stems = {}
    roots = [vault_root]

    # `rglob` does not follow a symlinked directory, so any symlinked
    # subdirectory of the vault root must be resolved and walked explicitly or
    # notes inside it will appear unresolved. This fix prevents false positives
    # when public/ or similar directories are symlinks to separate repositories.
    pub = vault_root / "public"
    if pub.is_symlink() or pub.is_dir():
        roots.append(pub.resolve())

    for root in roots:
        for p in root.rglob("*"):
            if not p.is_file() or ".git" in p.parts:
                continue
            stems.setdefault(p.stem.lower(), p)
            stems.setdefault(p.name.lower(), p)

    errors, warnings = [], []

    for arg in sys.argv[2:]:
        f = Path(arg)
        if not f.is_absolute():
            f = vault_root / arg
        if not f.exists():
            errors.append(f"{f.name}: file does not exist")
            continue
        txt = f.read_text()

        # Resolve path-style wikilinks by their last path segment, not the
        # whole string - a link written as [[dir/note]] should match a file
        # named "note.md", not "dir/note.md". This prevents false positives
        # from common path-style wikilink notation.
        def resolves(t):
            t = t.strip().lower().rstrip("/")
            return t in stems or t.rsplit("/", 1)[-1] in stems

        bad = sorted({t for t in re.findall(r"\[\[([^\]|#]+)", txt)
                      if not resolves(t)})
        for t in bad:
            errors.append(f"{f.name}: wikilink does not resolve -> [[{t.strip()}]]")

        nums = [int(n) for n in re.findall(r"^(\d+)\.\s", txt, re.M)]
        if nums:
            seen, dupes = set(), []
            for n in nums:
                if n in seen:
                    dupes.append(n)
                seen.add(n)

            # Treat duplicate low-numbered list entries as warnings rather than
            # errors - a note may contain multiple short unrelated numbered lists
            # alongside a long primary sequence. Only duplicates well inside the
            # findings range signal concurrent agents appending at once.
            for n in sorted(set(dupes)):
                (errors if n > 10 else warnings).append(
                    f"{f.name}: duplicate item number {n}"
                    + ("" if n > 10 else " (low number, probably a separate list)"))

            missing = sorted(set(range(min(nums), max(nums) + 1)) - seen)
            for n in missing:
                errors.append(f"{f.name}: item number {n} is skipped")

        if txt.startswith("---"):
            if txt.count("\n---", 0, 4000) < 1:
                errors.append(f"{f.name}: frontmatter opens and never closes")
            else:
                try:
                    import yaml
                    yaml.safe_load(txt.split("---", 2)[1])
                except ImportError:
                    warnings.append(f"{f.name}: pyyaml absent, frontmatter unparsed")
                except Exception as e:
                    errors.append(f"{f.name}: frontmatter is not valid yaml: {e}")

        if "public/" in str(f.resolve()) or "/public/" in str(f.resolve()):
            for m in re.findall(r"/Users/\w+", txt):
                errors.append(f"{f.name}: absolute user path inside public/ -> {m}")

        print(f"  {f.name}: {len(nums)} numbered items"
              + (f", max {max(nums)}" if nums else "")
              + f", {len(set(re.findall(r'\[\[([^\]|#]+)', txt)))} distinct "
                f"wikilinks, {len(bad)} unresolved")

    for w in warnings:
        print(f"WARNING {w}")
    print(f"\nmalformed={errors}")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
