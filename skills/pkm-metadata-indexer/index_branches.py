"""Index the markdown a remote ref holds that the default branch cannot see.

A daemon that indexes a working copy answers for one checkout. A repository with
several worktrees has several of them, so a note written on one branch is
invisible to a daemon watching another, and the duplicate check run before
writing a note can answer "no such note" while that note already exists a branch
away. This scanner reads committed state instead, and prefixes every path with
the ref it came from, so a hit says where the note lives and the reader can tell
"already on the default branch" from "only on someone's branch".

The filter is the whole design, because the obvious rule is wrong. Keeping every
blob whose oid differs from the default branch also keeps the stale ones: a
branch that is merely *behind* differs on every file the default branch has since
moved on from, and contributes nothing new. Measured on a live repository that
rule gave 1,130 blobs over 187 paths, one old branch supplying 86 of them, all of
it content the main corpus already holds at a newer version. Indexing that buries
every ranking under near-identical copies, which is the failure this corpus
exists to avoid rather than to cause.

The rule used here is the merge-tree contribution set: the markdown a merge of
the ref would actually add to or change on the default branch.

    git merge-tree --write-tree <default> <ref>
    git diff --name-only <default>^{tree} <merged tree>

That is the same test that answers whether a branch is merged at all, applied per
file rather than per branch. On the same repository it gives 4 instead of 1,130.

A ref whose merge conflicts yields no usable tree, because the merged blobs would
carry conflict markers, so it falls back to the paths it holds that the default
branch does not have at all. A contribution that is a deletion is skipped: a note
a branch removes is not a note anyone can collide with.
"""

import argparse
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import index_pkm_meta as pkm  # noqa: E402


def git(root: Path, *arguments: str, check: bool = True) -> subprocess.CompletedProcess:
    """One `git` call in `root`, captured as text."""
    return subprocess.run(
        ["git", *arguments], cwd=root, capture_output=True, text=True, check=check
    )


def default_branch(root: Path) -> str | None:
    """`main` or `master`, whichever the origin remote has, else None."""
    for name in ("main", "master"):
        if git(root, "rev-parse", "--verify", f"origin/{name}", check=False).returncode == 0:
            return name
    return None


def remote_refs(root: Path, exclude: str) -> list[str]:
    """Every `origin/*` ref except HEAD and the default branch."""
    listed = git(root, "for-each-ref", "--format=%(refname:short)", "refs/remotes/origin")
    return [
        ref for ref in (line.strip() for line in listed.stdout.splitlines())
        if ref and ref != "origin/HEAD" and ref != f"origin/{exclude}"
    ]


def tree_blobs(root: Path, ref: str) -> dict[str, str]:
    """`{path: blob oid}` for the markdown in a ref's tree."""
    listed = git(root, "ls-tree", "-r", ref, "--format=%(path) %(objectname)")
    blobs = {}
    for line in listed.stdout.splitlines():
        path, separator, oid = line.rpartition(" ")
        if separator and path.endswith(".md"):
            blobs[path] = oid
    return blobs


def merged_tree(root: Path, default_ref: str, ref: str) -> tuple[str | None, bool]:
    """`(merged tree oid, conflicted)` for merging `ref` into `default_ref`.

    `git merge-tree` exits non-zero on a conflict and prints the tree followed by
    conflict stanzas, so the return code carries the verdict and only the first
    line is a tree.
    """
    result = git(root, "merge-tree", "--write-tree", default_ref, ref, check=False)
    first_line = result.stdout.split("\n", 1)[0].strip()
    conflicted = result.returncode != 0
    if not first_line or any(character.isspace() for character in first_line):
        return None, conflicted
    return first_line, conflicted


def contributed_paths(root: Path, default_ref: str, ref: str, default_blobs: dict[str, str]) -> list[str]:
    """The markdown a merge of `ref` would add to or change on the default branch."""
    tree, conflicted = merged_tree(root, default_ref, ref)
    if tree is None or conflicted:
        return sorted(path for path in tree_blobs(root, ref) if path not in default_blobs)
    changed = git(root, "diff", "--name-only", f"{default_ref}^{{tree}}", tree, check=False)
    if changed.returncode != 0:
        return []
    return sorted(path for path in changed.stdout.splitlines() if path.endswith(".md"))


# A scan is keyed by the oids that produced it, because the daemon asks far more
# often than the answer can change. `--watch` watches the working copy, and a
# write there cannot move a ref: refs move on fetch, which touches no file the
# watcher sees. So the common call is a redundant one, and the merge-tree pass
# over every ref is seconds where `git for-each-ref` is one process and settles
# it in milliseconds. Keyed by root, since one daemon can hold several corpora.
_CACHE: dict[str, tuple] = {}


def ref_state(root: Path) -> tuple[tuple[str, str], ...]:
    """`((ref, oid), ...)` for every origin ref, enough to tell a scan is stale."""
    listed = git(root, "for-each-ref", "--format=%(refname:short) %(objectname)",
                 "refs/remotes/origin", check=False)
    if listed.returncode != 0:
        return ()
    state = []
    for line in listed.stdout.splitlines():
        ref, separator, oid = line.rpartition(" ")
        if separator:
            state.append((ref, oid))
    return tuple(state)


def read_blobs(root: Path, oids: list[str]) -> dict[str, str]:
    """`{oid: text}` from one `git cat-file --batch`.

    Read as bytes and sliced on the size git states, because a payload is not
    line-structured and counting reassembled lines gets the boundary wrong on any
    blob whose trailing newlines matter.
    """
    unique = list(dict.fromkeys(oids))
    if not unique:
        return {}
    process = subprocess.Popen(
        ["git", "cat-file", "--batch"], cwd=root,
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    payload, errors = process.communicate(input=("\n".join(unique) + "\n").encode())
    if process.returncode != 0:
        raise RuntimeError(f"git cat-file failed: {errors.decode(errors='replace')}")

    contents, position = {}, 0
    while position < len(payload):
        end_of_header = payload.find(b"\n", position)
        if end_of_header == -1:
            break
        header = payload[position:end_of_header].split()
        position = end_of_header + 1
        if len(header) < 3 or header[1] != b"blob":  # `<oid> missing` has two fields
            continue
        size = int(header[2])
        contents[header[0].decode()] = payload[position:position + size].decode("utf-8", errors="replace")
        position += size + 1  # the newline git writes after each payload
    return contents


def scan_branches(root: Path, db_path: Path | None = None, resume: bool = True):
    """Scanner with the same contract as `collect_index_data`.

    `db_path` and `resume` are part of that contract and unused here. The saving
    an incremental pass would give comes from `_CACHE` instead, which is keyed on
    the ref oids rather than on file mtimes, because refs are what this corpus is
    made of.
    """
    root = Path(root).resolve()
    notes, sections, links, errors = [], [], [], []

    if not (root / ".git").exists():
        return notes, sections, links, errors

    state = ref_state(root)
    cached = _CACHE.get(str(root))
    if state and cached is not None and cached[0] == state:
        # Copied out, so a caller that sorts or trims its result does not edit
        # what the next call will be handed.
        return tuple(list(rows) for rows in cached[1])

    branch = default_branch(root)
    if branch is None:
        return notes, sections, links, errors
    default_ref = f"origin/{branch}"
    default_blobs = tree_blobs(root, default_ref)

    for ref in remote_refs(root, branch):
        short_ref = ref[len("origin/"):]
        try:
            paths = contributed_paths(root, default_ref, ref, default_blobs)
            if not paths:
                continue
            blobs = tree_blobs(root, ref)
            # A path in the contribution that the ref does not hold is a deletion.
            wanted = {path: blobs[path] for path in paths if path in blobs}
            if not wanted:
                continue
            contents = read_blobs(root, list(wanted.values()))

            prefixed = {path: f"{short_ref}/{path}" for path in wanted}
            by_path, by_stem = pkm.make_note_lookup(list(prefixed.values()))

            for path, oid in wanted.items():
                prefixed_path = prefixed[path]
                content = contents.get(oid)
                if content is None:
                    errors.append((prefixed_path, "read", f"blob {oid} not returned"))
                    continue
                try:
                    meta, body, body_start_line = pkm.parse_frontmatter(content)
                    notes.append((
                        prefixed_path,
                        Path(path).name,
                        pkm.category_for(path),
                        meta["energy"],
                        meta["sentiment"],
                        pkm.json.dumps(meta["sentiment_label"]),
                        pkm.json.dumps(meta["tags"]),
                        pkm.extract_key_lines(body),
                        len(body.split()),
                    ))
                    for raw_target, start_line in pkm.iter_wikilinks(content):
                        links.append(pkm.Link(
                            source_path=prefixed_path,
                            raw_target=raw_target,
                            resolved_target_path=pkm.resolve_wikilink(
                                raw_target, prefixed_path, by_path, by_stem
                            ),
                            start_line=start_line,
                        ))
                    for section_ordinal, (heading, start_line, section_text) in enumerate(
                        pkm.parse_sections(Path(path).stem, body, body_start_line)
                    ):
                        for chunk_index, chunk_text in enumerate(pkm.chunk_section(heading, section_text)):
                            sections.append(pkm.Section(
                                section_id=f"{prefixed_path}::{section_ordinal}:{chunk_index}",
                                path=prefixed_path,
                                heading=heading,
                                start_line=start_line,
                                chunk_index=chunk_index,
                                sha256=pkm.get_sha256(chunk_text),
                                text=chunk_text,
                            ))
                except Exception as error:  # one unreadable note must not fail the run
                    errors.append((prefixed_path, "parse", str(error)))
        except Exception as error:  # one unreadable ref must not fail the run
            errors.append((short_ref, "ref", str(error)))

    if state:  # copies, so the caller's lists and the cache's cannot alias
        _CACHE[str(root)] = (state, ([*notes], [*sections], [*links], [*errors]))
    return notes, sections, links, errors


def self_check() -> int:
    """Build a throwaway repository and assert the contribution rule on it.

    The rule is only worth anything if a branch that is behind stays out, and
    that is the case a fixture written from the code's own assumptions tends to
    miss, so the check uses real refs rather than a stub.
    """
    with tempfile.TemporaryDirectory() as directory:
        base = Path(directory)
        origin, work = base / "origin.git", base / "work"
        subprocess.run(["git", "init", "--bare", "-q", str(origin)], check=True)
        subprocess.run(["git", "init", "-q", "-b", "main", str(work)], check=True)
        for key, value in (("user.name", "self-check"), ("user.email", "self-check@localhost")):
            git(work, "config", key, value)

        (work / "shared.md").write_text("# shared\noriginal\n", encoding="utf-8")
        git(work, "add", "shared.md")
        git(work, "commit", "-qm", "first")
        git(work, "remote", "add", "origin", str(origin))
        git(work, "push", "-q", "-u", "origin", "main")

        git(work, "checkout", "-qb", "behind")
        git(work, "push", "-q", "-u", "origin", "behind")

        git(work, "checkout", "-q", "main")
        (work / "shared.md").write_text("# shared\nmoved on\n", encoding="utf-8")
        git(work, "commit", "-qam", "advance the default branch")
        git(work, "push", "-q", "origin", "main")

        git(work, "checkout", "-qb", "ahead")
        (work / "only here.md").write_text("# only here\na note no one else has\n", encoding="utf-8")
        git(work, "add", "only here.md")
        git(work, "commit", "-qm", "a branch-only note")
        git(work, "push", "-q", "-u", "origin", "ahead")
        git(work, "checkout", "-q", "main")
        git(work, "fetch", "-q", "origin")

        notes, _, _, errors = scan_branches(work)
        paths = {row[0] for row in notes}

        failures = []
        if errors:
            failures.append(f"errors on a clean repository: {errors}")
        if any(path.startswith("behind/") for path in paths):
            failures.append(f"a branch that is only behind contributed {sorted(paths)}")
        if "ahead/only here.md" not in paths:
            failures.append(f"the branch-only note is missing, got {sorted(paths)}")
        if not all("/" in path for path in paths):
            failures.append(f"a path is not prefixed with its ref: {sorted(paths)}")

    for failure in failures:
        print(f"index_branches.py self-check: FAILED, {failure}")
    if failures:
        return 1
    print("index_branches.py self-check: passed")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("root", nargs="?", help="a git repository to read refs from")
    parser.add_argument("--self-check", action="store_true", help="run the internal gate and exit")
    arguments = parser.parse_args()

    if arguments.self_check:
        return self_check()
    if not arguments.root:
        parser.error("root path required")

    notes, sections, links, errors = scan_branches(Path(arguments.root).resolve())
    print(f"{len(notes)} notes, {len(sections)} sections, {len(links)} links, {len(errors)} errors")
    for row in notes:
        print(f"  {row[0]}")
    for error_path, kind, message in errors:
        print(f"  error {error_path} ({kind}): {message}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
