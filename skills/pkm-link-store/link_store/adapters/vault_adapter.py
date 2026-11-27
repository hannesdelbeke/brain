"""Vault note adapter: notes, aliases, wikilinks, linked files, session notes, URLs.

Note lists, wikilinks, and session rows come from the vault's pkm_index.db
(opened read-only) when present, otherwise from a markdown scan. Note bodies are
read from disk in both modes for cited URLs, markdown links, and session
frontmatter.
"""

from __future__ import annotations

import json
import os
import re
import sqlite3
from collections import defaultdict
from dataclasses import dataclass, replace
from pathlib import Path, PurePosixPath
from typing import Any, Callable, Iterable
from urllib.parse import unquote

import yaml

from ..canonical_ids import file_id, note_id, repo_id, session_id, url_id
from ..db import LinkStoreDB
from . import BoundaryPolicy
from .claude_jsonl import _detect_git_repo

ADAPTER = "vault_adapter"

# Mirrors pkm-metadata-indexer so both modes see the same corpus.
IGNORED_DIRS = frozenset({".obsidian", ".git", ".trash", "node_modules", ".venv", "__pycache__"})

_FRONTMATTER_RE = re.compile(r"^---\s*\r?\n(.*?)\r?\n---\s*(?:\r?\n|$)", re.DOTALL)
_WIKILINK_RE = re.compile(r"\[\[([^\]]+)\]\]")
_MD_LINK_RE = re.compile(r"(?<!\[)\[[^\[\]]*\]\(\s*<?([^()<>\n]+?)>?(?:\s+\"[^\"\n]*\")?\s*\)")
# Stops at brackets and pipes so "[url](url)" and table cells split correctly.
_URL_RE = re.compile(r"https?://[^\s<>\"'`\[\]|]+")
_URI_SCHEME_RE = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]+:")
_SESSION_TOKEN_RE = re.compile(r"^[A-Za-z0-9_.-]+(?::agent-[A-Za-z0-9_.-]+)?$")
_UUID_RE = re.compile(r"^[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}$")
_PLACEHOLDER_SESSIONS = frozenset({"null", "none", "unknown", "n/a", "~"})
_ID_PREFIXES = ("note:", "session:", "repo:", "branch:", "commit:", "file:", "url:")
_SESSION_KEYS = ("session_id", "recap_session")


@dataclass
class _Source:
    """What one vault offers before boundary filtering."""

    kind: str
    note_paths: list[str]
    # None means "parse from the note content".
    aliases: dict[str, list[str]] | None
    links: list[tuple[str, str, int]] | None  # (source_rel, target_rel, line)
    sessions: list[tuple[str, str]]  # (session_id, note_rel)


def _boundary_checker(policy: BoundaryPolicy) -> Callable[[Path], bool]:
    """Apply the policy to a path and to its symlink target."""
    real = BoundaryPolicy(
        allow_roots=tuple(Path(os.path.realpath(p)) for p in policy.allow_roots),
        deny_roots=tuple(Path(os.path.realpath(p)) for p in policy.deny_roots),
    )

    def allowed(path: Path) -> bool:
        return policy.is_allowed(path) and real.is_allowed(os.path.realpath(path))

    return allowed


def _safe_rel(rel: Any) -> str | None:
    """Accept only normalized vault-relative posix paths from the index."""
    if not isinstance(rel, str) or not rel:
        return None
    pure = PurePosixPath(rel)
    if pure.is_absolute() or ".." in pure.parts:
        return None
    return pure.as_posix()


def _note_key(value: str) -> str:
    clean = value.strip().replace("\\", "/")
    if clean.lower().endswith(".md"):
        clean = clean[:-3]
    return clean.lstrip("/").casefold()


def _clean_link_target(raw: str) -> str:
    target = raw.split("|", 1)[0].rstrip("\\")  # "\|" escapes the pipe in tables
    return target.split("#", 1)[0].strip().replace("\\", "/")


def _resolve_note_link(
    raw: str, source_rel: str, by_path: dict[str, str], by_stem: dict[str, list[str]]
) -> str | None:
    """Resolve a wikilink the way pkm-metadata-indexer does."""
    target = _clean_link_target(raw)
    if not target:
        return None
    direct = by_path.get(_note_key(target))
    if direct:
        return direct
    if "/" in target:
        relative = str(PurePosixPath(source_rel).parent / target)
        hit = by_path.get(_note_key(relative))
        if hit:
            return hit
    candidates = by_stem.get(PurePosixPath(target).name.casefold(), [])
    return candidates[0] if len(candidates) == 1 else None


def _line_of(content: str, pos: int) -> int:
    return content.count("\n", 0, pos) + 1


def _parse_frontmatter(content: str) -> dict[str, Any]:
    """Return frontmatter as strings and lists, tolerating invalid YAML."""
    match = _FRONTMATTER_RE.match(content)
    if not match:
        return {}
    block = match.group(1)
    try:
        # BaseLoader keeps every scalar a string, so numeric-looking ids survive.
        doc = yaml.load(block, Loader=yaml.BaseLoader)
        return doc if isinstance(doc, dict) else {}
    except yaml.YAMLError:
        pass

    out: dict[str, Any] = {}
    for key in ("aliases", *_SESSION_KEYS):
        found = re.search(
            rf"^{key}:[ \t]*([^\n]*)\n((?:[ \t]*-[ \t]+[^\n]+\n?)*)", block + "\n", re.MULTILINE
        )
        if not found:
            continue
        inline = found.group(1).strip()
        if inline.startswith("["):
            values = inline.strip("[]").split(",")
        elif inline:
            values = [inline]
        else:
            values = [line.strip()[1:] for line in found.group(2).splitlines()]
        out[key] = [v.strip().strip("'\"") for v in values if v.strip()]
    return out


def _string_list(value: Any) -> list[str]:
    items = value if isinstance(value, list) else [value]
    return [v.strip() for v in items if isinstance(v, str) and v.strip()]


def _walk_files(root: Path, include_nested_repos: bool) -> Iterable[str]:
    for current, directories, files in os.walk(root):
        directories[:] = sorted(
            d
            for d in directories
            if d not in IGNORED_DIRS
            and (include_nested_repos or not (Path(current) / d / ".git").exists())
        )
        for name in sorted(files):
            yield (Path(current) / name).relative_to(root).as_posix()


def _load_from_index(db_path: Path) -> _Source | None:
    """Read notes, edges, and sessions_idx; None if the index is unusable."""
    try:
        conn = sqlite3.connect(
            f"{db_path.resolve().as_uri()}?mode=ro", uri=True, timeout=60.0, isolation_level=None
        )
    except sqlite3.Error:
        return None
    try:
        conn.execute("BEGIN")  # one consistent snapshot across the three tables
        columns = {row[1] for row in conn.execute("PRAGMA table_info(notes)")}
        alias_expr = "aliases" if "aliases" in columns else "NULL"
        note_paths: list[str] = []
        aliases: dict[str, list[str]] = {}
        for path, raw_aliases in conn.execute(f"SELECT path, {alias_expr} FROM notes ORDER BY path"):
            rel = _safe_rel(path)
            if rel is None:
                continue
            note_paths.append(rel)
            try:
                aliases[rel] = _string_list(json.loads(raw_aliases or "[]"))
            except (json.JSONDecodeError, TypeError):
                aliases[rel] = []

        links = [
            (source, target, int(line))
            for source, target, line in conn.execute(
                """
                SELECT source_path, resolved_target_path, start_line FROM edges
                WHERE resolved_target_path IS NOT NULL
                ORDER BY source_path, start_line, resolved_target_path
                """
            )
        ]

        sessions: list[tuple[str, str]] = []
        if conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'sessions_idx'"
        ).fetchone():
            for sid, note_path in conn.execute(
                "SELECT session_id, note_path FROM sessions_idx ORDER BY note_path"
            ):
                if not isinstance(sid, str) or not isinstance(note_path, str):
                    continue
                # The indexer substitutes the filename stem when a note declares
                # no session_id; that is not a session.
                if sid == PurePosixPath(note_path).stem and not _UUID_RE.match(sid):
                    continue
                sessions.append((sid, note_path))
        return _Source(
            "pkm_index",
            note_paths,
            aliases if "aliases" in columns else None,
            links,
            sessions,
        )
    except sqlite3.Error:
        return None
    finally:
        conn.close()


def _load_from_markdown(root: Path) -> _Source:
    notes = [rel for rel in _walk_files(root, include_nested_repos=False) if rel.endswith(".md")]
    return _Source("markdown", notes, None, None, [])


class _FileResolver:
    """Resolve link targets to existing non-markdown files inside the vault."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self._by_name: dict[str, list[str]] | None = None

    def _existing(self, rel: str) -> str | None:
        norm = os.path.normpath(rel).replace(os.sep, "/")
        if norm == ".." or norm.startswith(("../", "/")):
            return None
        if IGNORED_DIRS.intersection(PurePosixPath(norm).parts):
            return None
        return norm if (self.root / norm).is_file() else None

    def resolve(self, target: str, source_rel: str, by_name: bool) -> str | None:
        suffix = PurePosixPath(target).suffix.lower()
        if not suffix or suffix == ".md":
            return None
        source_dir = PurePosixPath(source_rel).parent
        candidates = [str(source_dir / target), target.lstrip("/")]
        if by_name:  # wikilinks are vault-rooted first, markdown links relative first
            candidates.reverse()
        for candidate in candidates:
            hit = self._existing(candidate)
            if hit:
                return hit
        if not by_name or "/" in target:
            return None
        if self._by_name is None:
            self._by_name = defaultdict(list)
            for rel in _walk_files(self.root, include_nested_repos=True):
                if not rel.lower().endswith(".md"):
                    self._by_name[PurePosixPath(rel).name.casefold()].append(rel)
        matches = self._by_name.get(target.casefold(), [])
        return matches[0] if len(matches) == 1 else None


def _parse_session_ref(raw: str) -> str | None:
    token = raw.strip()
    if token.startswith("session:"):
        token = token[len("session:"):]
    if token.lower() in _PLACEHOLDER_SESSIONS or not _SESSION_TOKEN_RE.match(token):
        return None
    uuid, _, agent = token.partition(":")
    return session_id(uuid, agent or None)


def _ensure_session(db: LinkStoreDB, raw: str) -> str | None:
    """Return the Session node for a raw reference, creating it if unknown."""
    canonical = _parse_session_ref(raw)
    if canonical is None:
        return None
    aliased = db.resolve_alias(canonical[len("session:"):])
    if aliased:
        node = db.get_node(aliased)
        if node and node["node_type"] == "Session":
            canonical = aliased
    node = db.get_node(canonical)
    if node is None:
        db.upsert_node(canonical, "Session", title=canonical[len("session:"):])
    elif node["expired_at"] is not None:
        db.upsert_node(canonical, "Session")
    return canonical


def _sync_aliases(
    db: LinkStoreDB,
    wanted: dict[str, set[str]],
    previous: list[list[str]],
) -> tuple[list[list[str]], int]:
    """Apply this vault's aliases without taking over another node's alias."""
    desired = {
        alias: next(iter(owners))
        for alias, owners in wanted.items()
        if len(owners) == 1  # shared by several notes: ambiguous
        and not alias.startswith(_ID_PREFIXES)
        and not _UUID_RE.match(alias)  # would shadow session lookups
    }
    for alias, nid in previous:
        if desired.get(alias) != nid:
            db.delete_alias(alias, nid)
    emitted: list[list[str]] = []
    for alias, nid in sorted(desired.items()):
        if db.resolve_alias(alias) in (None, nid):
            db.upsert_alias(alias, nid)
            emitted.append([alias, nid])
    return emitted, len(wanted) - len(emitted)


def sync_vault(
    db: LinkStoreDB,
    vault_name: str,
    vault_path: Path | str,
    policy: BoundaryPolicy | None = None,
) -> dict[str, Any]:
    """Ingest one vault and expire what an earlier sync emitted that is now gone."""
    root = Path(os.path.abspath(os.path.expanduser(str(vault_path))))
    pol = policy or BoundaryPolicy()
    pol = replace(pol, vault_roots={**pol.vault_roots, vault_name: root})
    totals: dict[str, Any] = {
        "source": None,
        "notes": 0,
        "aliases": 0,
        "skipped_aliases": 0,
        "wikilinks_to": 0,
        "backed_by": 0,
        "documented_in": 0,
        "cited_url": 0,
        "skipped_denied": 0,
        "unreadable": 0,
        "expired_nodes": 0,
        "expired_edges": 0,
    }
    # A missing root (unmounted, mistyped) must not expire the whole vault.
    if not root.is_dir():
        return totals
    allowed = _boundary_checker(pol)

    index_path = root / ".obsidian" / "pkm_index.db"
    index_policy = replace(pol, allow_roots=())  # rows are allow-filtered below
    source = None
    if index_path.is_file() and _boundary_checker(index_policy)(index_path):
        source = _load_from_index(index_path)
    if source is None:
        source = _load_from_markdown(root)
    totals["source"] = source.kind

    # Pass 1: nodes for every note this vault owns and the policy allows.
    note_nodes: dict[str, str] = {}
    contents: dict[str, str] = {}
    for rel in source.note_paths:
        full = root / rel
        owner = pol.resolve_vault_note(full)
        # A different owner means the note belongs to a nested vault.
        if owner is None or owner[0] != note_id(vault_name, rel) or not full.is_file():
            continue
        if not allowed(full):
            totals["skipped_denied"] += 1
            continue
        try:
            contents[rel] = full.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            totals["unreadable"] += 1
            continue
        note_nodes[rel] = owner[0]
        db.upsert_node(owner[0], "Note", title=full.name, metadata={"vault": vault_name, "path": rel})
    totals["notes"] = len(note_nodes)

    # (src, dst, rel) -> source_ref
    edges: dict[tuple[str, str, str], str] = {}

    def add_edge(src: str, dst: str, rel: str, ref: str) -> None:
        edges.setdefault((src, dst, rel), ref)

    by_path: dict[str, str] = {}
    by_stem: dict[str, list[str]] = defaultdict(list)
    for rel in source.note_paths:
        by_path[_note_key(rel)] = rel
        by_stem[PurePosixPath(rel).stem.casefold()].append(rel)

    if source.links is not None:
        for src_rel, dst_rel, line in source.links:
            src, dst = note_nodes.get(src_rel), note_nodes.get(dst_rel)
            if src and dst and src != dst:
                add_edge(src, dst, "wikilinks_to", f"{src_rel}:{line}")

    files = _FileResolver(root)
    repo_cache: dict[Path, tuple[Path, str] | None] = {}
    wanted_aliases: dict[str, set[str]] = defaultdict(set)
    session_refs: list[tuple[str, str, str]] = [
        (sid, note_rel, "sessions_idx") for sid, note_rel in source.sessions
    ]

    def add_file_link(src_rel: str, target_rel: str, line: int) -> None:
        full = root / target_rel
        if not allowed(full):
            totals["skipped_denied"] += 1
            return
        parent = full.parent.resolve()
        info = _detect_git_repo(parent, repo_cache)
        if info is not None:
            repo_root, rid = info
            repo_rel = (parent / full.name).relative_to(repo_root).as_posix()
        else:
            rid, repo_rel = repo_id(fallback_name=vault_name), target_rel
        fid = file_id(rid, repo_rel)
        db.upsert_node(fid, "File", title=full.name)
        add_edge(note_nodes[src_rel], fid, "backed_by", f"{src_rel}:{line}")

    # Pass 2: everything derived from note content.
    for rel, content in contents.items():
        nid = note_nodes[rel]
        frontmatter = _parse_frontmatter(content)

        if source.aliases is not None:
            aliases = source.aliases.get(rel, [])
        else:
            aliases = _string_list(frontmatter.get("aliases"))
        for alias in aliases:
            wanted_aliases[alias].add(nid)

        for match in _WIKILINK_RE.finditer(content):
            raw = match.group(1).strip()
            line = _line_of(content, match.start())
            note_target = _resolve_note_link(raw, rel, by_path, by_stem)
            if note_target is not None:
                dst = note_nodes.get(note_target)
                if source.links is None and dst and dst != nid:
                    add_edge(nid, dst, "wikilinks_to", f"{rel}:{line}")
                continue
            file_target = files.resolve(_clean_link_target(raw), rel, by_name=True)
            if file_target:
                add_file_link(rel, file_target, line)

        for match in _MD_LINK_RE.finditer(content):
            href = match.group(1).strip()
            if _URI_SCHEME_RE.match(href) or href.startswith("#"):
                continue
            target = unquote(href.split("#", 1)[0].split("?", 1)[0])
            file_target = files.resolve(target, rel, by_name=False) if target else None
            if file_target:
                add_file_link(rel, file_target, _line_of(content, match.start()))

        for match in _URL_RE.finditer(content):
            try:
                uid = url_id(match.group(0).rstrip("*~"))
            except ValueError:  # malformed port or host
                continue
            if uid:
                db.upsert_node(uid, "Url", title=uid[4:])
                add_edge(nid, uid, "cited_url", f"{rel}:{_line_of(content, match.start())}")

        if PurePosixPath(rel).parts[0] == "sessions":
            for key in _SESSION_KEYS:
                for sid in _string_list(frontmatter.get(key)):
                    session_refs.append((sid, rel, key))

    for raw_sid, note_rel, via in session_refs:
        dst = note_nodes.get(note_rel)
        if dst is None:
            continue
        sess = _ensure_session(db, raw_sid)
        if sess:
            add_edge(sess, dst, "documented_in", f"{note_rel}#{via}")

    for (src, dst, rel_name), ref in edges.items():
        db.upsert_edge(
            src, dst, rel_name, ADAPTER, source_ref=ref, metadata={"vault": vault_name}
        )
        totals[rel_name] += 1

    # Reconcile against the previous sync of this vault.
    for row in db.conn.execute(
        "SELECT src_id, dst_id, rel, metadata_json FROM edges "
        "WHERE source_adapter = ? AND expired_at IS NULL",
        (ADAPTER,),
    ).fetchall():
        key = (row["src_id"], row["dst_id"], row["rel"])
        if key in edges or json.loads(row["metadata_json"] or "{}").get("vault") != vault_name:
            continue
        db.expire_edge(*key)
        totals["expired_edges"] += 1

    state_key = f"vault:{vault_name}"
    state = db.get_sync_state(ADAPTER, state_key)
    previous = json.loads(state["extra_json"]) if state and state.get("extra_json") else {}
    current = set(note_nodes.values())
    for nid, rel in previous.get("notes", {}).items():
        if nid in current:
            continue
        full = root / rel
        if not full.is_file() or not allowed(full):
            db.expire_node(nid)
            totals["expired_nodes"] += 1

    emitted_aliases, skipped = _sync_aliases(db, wanted_aliases, previous.get("aliases", []))
    totals["aliases"] = len(emitted_aliases)
    totals["skipped_aliases"] = skipped

    # Keep notes that still exist but dropped out (stale index) so a later
    # deletion is still noticed.
    tracked = {
        nid: rel
        for nid, rel in previous.get("notes", {}).items()
        if (root / rel).is_file() and allowed(root / rel)
    }
    tracked.update({nid: rel for rel, nid in note_nodes.items()})
    db.set_sync_state(
        ADAPTER, state_key, extra={"notes": tracked, "aliases": emitted_aliases}
    )
    return totals
