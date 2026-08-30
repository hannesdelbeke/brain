"""Index a code repository with the vault indexer, for the link graph.

A repository has no wikilinks and is full of references anyway: a readme
pointing at a source file, a page embedding a diagram, a doc naming a module.
This scanner turns those into `edges` rows so they can be queried:

    python index_repo.py --root /path/to/repo
    python searchd.py --corpus /path/to/index_repo.py:scan_repo=myrepo=/path/to/repo

Every file that is not ignored becomes a note, so a png is a node even though
nothing about it is searchable; only markdown gets sections. That is what makes
"every image nothing references" a single query, since the unreferenced side of
it is a row that no edge points at rather than a file nobody listed.

Three reference kinds become edges, all of them from markdown only: links
`[text](path)`, image embeds `![alt](path)`, and bare relative paths in prose
such as `see src/auth/token.py`. A target resolves against the source file's
directory then the repository root, and `resolved_target_path` stays null when
neither exists on disk, which is what makes a broken reference queryable. A
target that resolves nowhere falls back to its filename alone, when exactly one
file in the repository carries that name.

No import parsing and no cross-repo resolution: measured over three repositories
in `2026-08-27 agent search progress`, cross-repo resolution has 26 candidate
edges across 54,000 files and does not earn itself, and import parsing does but
only after a guid parser, since a unity asset is referenced from a `.meta` file
rather than from prose.
"""

from __future__ import annotations

import argparse
import collections
import json
import os
import re
import subprocess
import sys
import urllib.parse
from pathlib import Path, PurePosixPath

import index_pkm_meta as pkm

# `[text](target)` and `![alt](target)` are the same shape, so one pattern reads
# both. An optional title and optional angle brackets are stripped here rather
# than in the resolver.
MD_LINK_RE = re.compile(r"!?\[[^\]]*\]\(\s*<?([^)<>\s]+)>?(?:\s+[\"'][^\"']*[\"'])?\s*\)")
# A bare path needs a slash and an extension, which is what separates
# `src/auth/token.py` from a sentence with a full stop in it. The extension has
# to start with a letter or every ratio in the prose, `1.2/1.4`, reads as a
# broken reference. The lookbehind keeps the tail of a url from matching.
BARE_PATH_RE = re.compile(
    r"(?<![\w./\\-])((?:\.{1,2}/)?[\w.-]+(?:/[\w.-]+)+\.[A-Za-z][A-Za-z0-9]{0,5})(?![\w/])")
EXTERNAL_RE = re.compile(r"^(?:[a-zA-Z][\w+.-]*:|//|#)")

# Generated trees are most of a repository by file count and none of it by
# meaning. `.gitignore` covers them where there is a git checkout; this covers
# the rest.
SKIP_DIRS = pkm.IGNORED_DIRS | {"dist", "build", "out", "target", "vendor",
                                ".next", ".nuxt", "coverage", ".cache", ".idea", ".vs"}
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".avif", ".ico", ".bmp"}


def category_for(relative_path: str) -> str:
    """`doc` is searchable, `asset` is the orphan-image query, `code` is the rest."""
    suffix = PurePosixPath(relative_path).suffix.lower()
    if suffix == ".md":
        return "doc"
    return "asset" if suffix in IMAGE_EXTENSIONS else "code"


def skipped(relative_path: str) -> bool:
    return any(part in SKIP_DIRS for part in PurePosixPath(relative_path).parts[:-1])


def repo_files(root: Path) -> list[str]:
    """Every indexable file, relative and posix, respecting `.gitignore`.

    `git ls-files` already applies every ignore file in the checkout, so the
    ignore rules are git's rather than a second half-implementation of them. A
    directory that is not a checkout falls back to a walk over `SKIP_DIRS`.
    """
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
            capture_output=True, timeout=120,
        )
        if result.returncode == 0:
            listed = result.stdout.decode("utf-8", errors="ignore").split("\0")
            return sorted(path for path in listed
                          if path and not skipped(path) and (root / path).is_file())
    except (OSError, subprocess.SubprocessError):
        pass

    paths = []
    for current, directories, files in os.walk(root):
        directories[:] = [name for name in directories if name not in SKIP_DIRS]
        for name in files:
            paths.append((Path(current) / name).relative_to(root).as_posix())
    return sorted(paths)


def iter_references(content: str):
    """Yield `(raw_target, line)` for every markdown link, embed and bare path.

    A bare path inside a link matches twice, so the pair is deduplicated; the
    edges primary key would collapse it anyway, this just keeps the rows honest.
    """
    seen = set()
    for pattern in (MD_LINK_RE, BARE_PATH_RE):
        for match in pattern.finditer(content):
            raw_target = match.group(1).strip()
            if not raw_target or EXTERNAL_RE.match(raw_target):
                continue
            line = content.count("\n", 0, match.start()) + 1
            if (raw_target, line) not in seen:
                seen.add((raw_target, line))
                yield raw_target, line


def resolve_reference(raw_target: str, source_path: str, root: Path,
                      by_path: dict[str, str], by_name: dict[str, str] | None = None) -> str | None:
    """The path this reference points at, or None when nothing is there.

    Relative to the source file first, since that is what a markdown link means,
    then to the repository root. A target that climbs out of the root is not a
    node here, so it stays unresolved rather than pointing outside the corpus.

    Last, the filename alone, and only when exactly one file in the repository
    carries it. Prose names a file from wherever it was written, so a partial
    path is the common shape of a broken edge rather than a rare one: the
    fallback resolves 34% of HyperLight's unresolved edges and 72% of
    proj-project-d-client's, against 5% and 3% whose basename is ambiguous, which
    is the measurement in `2026-08-27 agent search progress`. Ambiguous names
    stay unresolved, since a wrong edge is worse here than a missing one.
    """
    target = urllib.parse.unquote(raw_target.split("#", 1)[0].strip()).replace("\\", "/")
    if not target:
        return None
    if target.startswith("/"):
        candidates = [target.lstrip("/")]
    else:
        candidates = [str(PurePosixPath(source_path).parent / target), target]

    for candidate in candidates:
        normalised = os.path.normpath(candidate).replace("\\", "/")
        if normalised.startswith("..") or normalised in (".", ""):
            continue
        known = by_path.get(normalised.casefold())
        if known:
            return known
        # An ignored file is still a file, so "the readme points at a build
        # artifact" reads as resolved rather than broken.
        if (root / normalised).is_file():
            return normalised
    return (by_name or {}).get(PurePosixPath(target).name.casefold())


def scan_repo(root: Path):
    """Scanner with the same contract as `collect_index_data`."""
    root = Path(root)
    relative_paths = repo_files(root)
    by_path = {path.casefold(): path for path in relative_paths}
    counted = collections.Counter(PurePosixPath(path).name.casefold() for path in relative_paths)
    by_name = {PurePosixPath(path).name.casefold(): path for path in relative_paths
               if counted[PurePosixPath(path).name.casefold()] == 1}

    notes, sections, links, errors = [], [], [], []
    for relative_path in relative_paths:
        category = category_for(relative_path)
        name = PurePosixPath(relative_path).name
        if category != "doc":
            # A source file or an image is a node with nothing to search: it is
            # here so an edge can land on it and so an orphan query can miss it.
            notes.append((relative_path, name, category, None, None,
                          json.dumps([]), json.dumps([category]), "", 0))
            continue
        try:
            content = (root / relative_path).read_text(encoding="utf-8", errors="ignore")
            meta, body, body_start_line = pkm.parse_frontmatter(content)
            notes.append((relative_path, name, category, meta["energy"], meta["sentiment"],
                          json.dumps(meta["sentiment_label"]),
                          json.dumps(["doc"] + meta["tags"]),
                          pkm.extract_key_lines(body), len(body.split())))

            for raw_target, start_line in iter_references(content):
                links.append(pkm.Link(
                    source_path=relative_path,
                    raw_target=raw_target,
                    resolved_target_path=resolve_reference(raw_target, relative_path, root, by_path, by_name),
                    start_line=start_line,
                ))

            stem = PurePosixPath(relative_path).stem
            for section_ordinal, (heading, start_line, text) in enumerate(
                pkm.parse_sections(stem, body, body_start_line)
            ):
                for chunk_index, chunk_text in enumerate(pkm.chunk_section(heading, text)):
                    sections.append(pkm.Section(
                        section_id=f"{relative_path}::{section_ordinal}:{chunk_index}",
                        path=relative_path,
                        heading=heading,
                        start_line=start_line,
                        chunk_index=chunk_index,
                        sha256=pkm.get_sha256(chunk_text),
                        text=chunk_text,
                    ))
        except Exception as error:  # one unreadable file must not fail the run
            errors.append((relative_path, "parse", str(error)))

    return notes, sections, links, errors


def selfcheck():
    import tempfile

    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp) / "repo"
        for directory in ("docs", "src", "assets", "node_modules/pkg"):
            (root / directory).mkdir(parents=True)
        (root / "README.md").write_text(
            "# Title\n"
            "\n"
            "The [guide](docs/guide.md) explains it, see src/app.ts for the entry point.\n"
            "\n"
            "![logo](assets/logo.png)\n"
            "\n"
            "Broken on purpose: see src/missing.ts and [gone](docs/gone.md).\n"
            "\n"
            "A partial path still resolves: see lib/parser.ts for the parser.\n"
            "\n"
            "An ambiguous one does not: see other/util.ts.\n"
            "\n"
            "External links are not edges: [site](https://example.com/a/b.html).\n",
            encoding="utf-8")
        (root / "docs" / "guide.md").write_text(
            "## Setup\n\nBack to the [readme](../README.md).\n", encoding="utf-8")
        (root / "src" / "app.ts").write_text("export const app = 1;\n", encoding="utf-8")
        (root / "src" / "lib").mkdir()
        (root / "src" / "lib" / "parser.ts").write_text("export const parse = 1;\n", encoding="utf-8")
        (root / "src" / "util.ts").write_text("export const a = 1;\n", encoding="utf-8")
        (root / "src" / "lib" / "util.ts").write_text("export const b = 1;\n", encoding="utf-8")
        (root / "assets" / "logo.png").write_bytes(b"\x89PNG")
        (root / "assets" / "unused.png").write_bytes(b"\x89PNG")
        (root / "node_modules" / "pkg" / "readme.md").write_text("# ignored\n", encoding="utf-8")

        notes, sections, links, errors = scan_repo(root)
        assert not errors, errors
        paths = {note[0] for note in notes}
        assert paths == {"README.md", "docs/guide.md", "src/app.ts", "src/lib/parser.ts",
                         "src/util.ts", "src/lib/util.ts",
                         "assets/logo.png", "assets/unused.png"}, paths
        assert {note[0]: note[2] for note in notes}["assets/logo.png"] == "asset"
        assert {note[0]: note[2] for note in notes}["src/app.ts"] == "code"
        assert {section.path for section in sections} == {"README.md", "docs/guide.md"}, \
            "only markdown is searchable"

        edges = {(link.source_path, link.raw_target): link.resolved_target_path for link in links}
        assert edges[("README.md", "docs/guide.md")] == "docs/guide.md", "markdown link"
        assert edges[("README.md", "assets/logo.png")] == "assets/logo.png", "image embed"
        assert edges[("README.md", "src/app.ts")] == "src/app.ts", "bare path in prose"
        assert edges[("README.md", "src/missing.ts")] is None, "a broken bare path is queryable"
        assert edges[("README.md", "docs/gone.md")] is None, "a broken link is queryable"
        assert edges[("docs/guide.md", "../README.md")] == "README.md", "resolved from the source dir"
        assert edges[("README.md", "lib/parser.ts")] == "src/lib/parser.ts", \
            "a partial path falls back to the one file with that name"
        assert edges[("README.md", "other/util.ts")] is None, \
            "two files named util.ts leave the reference unresolved"
        assert not [target for _, target in edges if "example.com" in target], "urls are not edges"
        assert len(links) == len(edges), "no duplicate edge from one line matching twice"

        referenced = {link.resolved_target_path for link in links}
        orphan_assets = [note[0] for note in notes if note[2] == "asset" and note[0] not in referenced]
        assert orphan_assets == ["assets/unused.png"], orphan_assets

    print("selfcheck ok")


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", default=".", help="Repository root")
    parser.add_argument("--db", default=None, help="Database, otherwise <root>/.pkm_index.db")
    parser.add_argument("--with-embeddings", action="store_true", help="Embed as well as index")
    parser.add_argument("--selfcheck", action="store_true", help="Run the assertions and exit")
    args = parser.parse_args()

    if args.selfcheck:
        selfcheck()
        return

    root = Path(args.root).expanduser().resolve()
    pkm.build_index(
        vault_path=str(root),
        db_path=args.db or str(pkm.default_db_path(root)),
        skip_embeddings=not args.with_embeddings,
        collect=scan_repo,
    )


if __name__ == "__main__":
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
