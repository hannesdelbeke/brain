"""Incremental Claude Code JSONL transcript adapter for pkm-link-store."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Any

from ..canonical_ids import branch_id, repo_id, session_id, strip_branch_ref, url_id
from ..db import LinkStoreDB
from . import BoundaryPolicy

PREFIX_BYTES = 4096
# Bump when new record types or rules should apply to already-ingested transcripts.
PARSER_VERSION = 2

_URL_RE = re.compile(r"https?://[^\s<>\"'`]+")
_READ_TOOLS = frozenset({"Read", "View", "NotebookRead", "read_file"})
_WRITE_TOOLS = frozenset({"Edit", "Write", "MultiEdit", "NotebookEdit", "edit_file", "write_file"})
_FETCH_TOOLS = frozenset({"WebFetch", "fetch_url", "browser"})
_FILE_ARG_KEYS = ("file_path", "notebook_path", "path", "TargetFile")
_URL_ARG_KEYS = ("prompt", "query", "description", "command")
_UUID_RE = re.compile(r"[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}")
_LABEL_KEYS = {"ai-title": ("aiTitle", "ai_title"), "agent-name": ("agentName", "agent_name")}
LABEL_ALIAS_KINDS = frozenset(kind for _, kind in _LABEL_KEYS.values())
# Labels are free text, so they must not look like ids or note/transcript paths.
_RESERVED_ALIAS_RE = re.compile(
    r"^(?:note|session|repo|branch|commit|file|url):|[/\\]|\.(?:md|jsonl)$|^[0-9a-fA-F]{8}(?:-|$)"
)
_MAX_LABEL_ALIAS = 200


def _prefix_sha256(path: Path, nbytes: int = PREFIX_BYTES) -> str:
    with path.open("rb") as fh:
        return hashlib.sha256(fh.read(nbytes)).hexdigest()


def _detect_git_repo(cwd: Path, cache: dict[Path, tuple[Path, str] | None]) -> tuple[Path, str] | None:
    if cwd in cache:
        return cache[cwd]
    if not cwd.exists():
        cache[cwd] = None
        return None
    try:
        top = subprocess.run(
            ["git", "-C", str(cwd), "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        if top.returncode != 0:
            cache[cwd] = None
            return None
        repo_root = Path(top.stdout.strip()).resolve()
        rem = subprocess.run(
            ["git", "-C", str(repo_root), "remote", "get-url", "origin"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        remote_url = rem.stdout.strip() if rem.returncode == 0 else None
        rid = repo_id(remote_url=remote_url, fallback_name=repo_root.name)
        res = (repo_root, rid)
        cache[cwd] = res
        return res
    except OSError:
        cache[cwd] = None
        return None


def _safe_url_id(raw: str) -> str | None:
    try:
        return url_id(raw)
    except ValueError:  # shell placeholders such as http://$HOST:$PORT
        return None


def _extract_urls(text: str) -> list[str]:
    out: list[str] = []
    for match in _URL_RE.findall(text):
        cid = _safe_url_id(match)
        if cid:
            out.append(cid)
    return out


def _first_cwd(path: Path) -> str | None:
    """First cwd in a transcript, so cwd-less preamble records obey the boundary."""
    with path.open("rb") as fh:
        for raw in fh:
            if b'"cwd"' not in raw:
                continue
            try:
                rec = json.loads(raw.decode("utf-8", errors="replace"))
            except json.JSONDecodeError:
                continue
            if isinstance(rec, dict) and rec.get("cwd"):
                return str(rec["cwd"])
    return None


def _fallback_session_uuid(path: Path, is_agent_file: bool) -> str:
    if not is_agent_file:
        return path.stem
    # <uuid>/subagents/[...]/agent-<id>.jsonl
    parts = path.parts
    for index in range(len(parts) - 2, 0, -1):
        if parts[index] == "subagents":
            return parts[index - 1]
    return path.parent.parent.name


def _ensure_session_node(
    db: LinkStoreDB, node_id: str, default_title: str, metadata: dict[str, Any] | None = None
) -> None:
    """Upsert a Session without overwriting a label or dropping earlier metadata."""
    node = db.get_node(node_id)
    merged: dict[str, Any] | None = None
    if metadata is not None:
        old = json.loads(node["metadata_json"]) if node and node["metadata_json"] else {}
        merged = {**old, **metadata}
    title = None if node and node["title"] else default_title
    db.upsert_node(node_id, "Session", title=title, metadata=merged)
    uuid = node_id[len("session:"):]
    if _UUID_RE.fullmatch(uuid):
        db.refresh_short_id_alias(uuid[:8])


def _refresh_label_alias(db: LinkStoreDB, label: str) -> None:
    """Point a label alias at its only holder; drop it when none or several have it."""
    if len(label) > _MAX_LABEL_ALIAS or _RESERVED_ALIAS_RE.search(label):
        return
    owners = db.conn.execute(
        """
        SELECT id, json_extract(metadata_json, '$.agent_name') = ? AS by_name FROM nodes
        WHERE node_type = 'Session' AND expired_at IS NULL
          AND (json_extract(metadata_json, '$.agent_name') = ?
               OR json_extract(metadata_json, '$.ai_title') = ?)
        LIMIT 2
        """,
        (label, label, label),
    ).fetchall()
    current = db.get_alias(label)
    ours = current is not None and current["alias_kind"] in LABEL_ALIAS_KINDS
    if len(owners) != 1:  # ambiguous or unused: resolve to nobody
        if ours:
            db.delete_alias(label, current["node_id"])
    elif current is None or ours:  # never take over a note or path alias
        kind = "agent_name" if owners[0]["by_name"] else "ai_title"
        db.upsert_alias(label, owners[0]["id"], alias_kind=kind)


def _set_session_label(db: LinkStoreDB, node_id: str, kind: str, value: str) -> None:
    """Record an ai-title or agent-name; agent-name wins as the node title."""
    node = db.get_node(node_id)
    if node is None:
        return
    meta = json.loads(node["metadata_json"]) if node["metadata_json"] else {}
    previous = meta.get(kind)
    if previous == value:
        return
    meta[kind] = value
    title = meta.get("agent_name") or meta.get("ai_title")
    db.upsert_node(node_id, "Session", title=title, metadata=meta)
    if previous:
        _refresh_label_alias(db, previous)
    _refresh_label_alias(db, value)


def _sync_single_jsonl(
    db: LinkStoreDB,
    path: Path,
    claude_root: Path,
    policy: BoundaryPolicy,
    repo_cache: dict[Path, tuple[Path, str] | None],
) -> dict[str, int]:
    stats = {"records": 0, "edges": 0, "skipped_denied": 0}
    source_key = str(path.resolve())
    file_size = path.stat().st_size
    state = db.get_sync_state("claude_jsonl", source_key)

    stale_parser = bool(state) and (
        json.loads(state.get("extra_json") or "{}").get("parser_version") != PARSER_VERSION
    )
    if state and not stale_parser and int(state["byte_offset"]) <= file_size:
        prev_offset = int(state["byte_offset"])
        check_len = min(prev_offset, PREFIX_BYTES)
        if state["prefix_sha256"] == _prefix_sha256(path, check_len):
            offset = prev_offset
            line_count = int(state["line_count"])
            extra = json.loads(state["extra_json"]) if state.get("extra_json") else {}
        else:
            offset = 0
            line_count = 0
            extra = {}
    else:
        offset = 0
        line_count = 0
        extra = {}

    if offset == file_size:
        return stats

    active_session: str | None = extra.get("session_node_id")
    active_branch: str | None = extra.get("active_branch")
    branch_start: str | None = extra.get("branch_start")
    branch_last: str | None = extra.get("branch_last")
    last_cwd: str | None = extra.get("last_cwd")

    if last_cwd is None:
        last_cwd = _first_cwd(path)

    rel_source = path.relative_to(claude_root).as_posix()
    file_agent_hint = path.stem[len("agent-"):] if path.name.startswith("agent-") else None

    def add_edge(src: str, dst: str, rel: str, ts: Any = None, **kwargs: Any) -> None:
        db.upsert_edge(
            src,
            dst,
            rel,
            "claude_jsonl",
            valid_from=str(ts) if ts else None,
            source_ref=f"{rel_source}:{line_count}",
            **kwargs,
        )
        stats["edges"] += 1

    def add_url(uid: str, rel: str, ts: Any) -> None:
        db.upsert_node(uid, "Url", title=uid[4:])
        add_edge(active_session, uid, rel, ts)

    def add_file(raw_fp: Any, rel: str, ts: Any) -> None:
        if not isinstance(raw_fp, str) or not raw_fp.strip():
            return
        fp = Path(raw_fp)
        if not fp.is_absolute() and last_cwd:
            fp = Path(last_cwd) / fp
        repo_info = _detect_git_repo(Path(last_cwd), repo_cache) if last_cwd else None
        target = policy.resolve_target(
            fp,
            repo_root=repo_info[0] if repo_info else None,
            repo_id_str=repo_info[1] if repo_info else None,
        )
        if target is None:
            stats["skipped_denied"] += 1
            return
        dst_id, dst_type, dst_title = target
        db.upsert_node(dst_id, dst_type, title=dst_title)
        add_edge(active_session, dst_id, rel, ts)

    def add_lineage(other: Any, rel: str, ts: Any = None, via: set[str] | None = None) -> None:
        if not isinstance(other, str) or not other.strip():
            return
        other_node = session_id(other.strip())
        if other_node == active_session:
            return
        _ensure_session_node(db, other_node, other.strip())
        metadata = None
        if via:
            for row in db.conn.execute(
                "SELECT metadata_json FROM edges WHERE src_id = ? AND dst_id = ? "
                "AND rel = ? AND expired_at IS NULL",
                (active_session, other_node, rel),
            ):
                via = via | set(json.loads(row["metadata_json"] or "{}").get("via", []))
            metadata = {"via": sorted(via)}
        add_edge(active_session, other_node, rel, ts, metadata=metadata)

    with path.open("rb") as fh:
        fh.seek(offset)
        for raw in fh:
            if not raw.endswith(b"\n"):
                break
            offset += len(raw)
            line_count += 1
            try:
                rec = json.loads(raw.decode("utf-8", errors="replace"))
            except json.JSONDecodeError:
                continue
            if not isinstance(rec, dict):
                continue

            stats["records"] += 1
            rec_cwd = rec.get("cwd") or last_cwd
            if rec_cwd:
                last_cwd = str(rec_cwd)
                if not policy.is_allowed(last_cwd):
                    stats["skipped_denied"] += 1
                    continue

            sess_uuid = rec.get("sessionId") or _fallback_session_uuid(
                path, bool(file_agent_hint)
            )
            agent_id = rec.get("agentId") or file_agent_hint
            if not sess_uuid:
                continue

            sess_node = session_id(str(sess_uuid), str(agent_id) if agent_id else None)
            if active_session != sess_node:
                active_session = sess_node
                _ensure_session_node(
                    db,
                    sess_node,
                    str(sess_uuid) if not agent_id else f"{sess_uuid} (agent-{agent_id})",
                    metadata={"source_file": rel_source},
                )
                db.upsert_alias(rel_source, sess_node)
                if not agent_id:
                    db.upsert_alias(str(sess_uuid), sess_node)
                else:
                    parent_node = session_id(str(sess_uuid))
                    _ensure_session_node(db, parent_node, str(sess_uuid))
                    db.upsert_alias(str(sess_uuid), parent_node)
                    add_edge(sess_node, parent_node, "child_of")

            ts = rec.get("timestamp")
            rtype = rec.get("type")

            # Session lineage fields if present
            for field_name, rel_name in (
                ("continuedIn", "continued_in"),
                ("derivedFrom", "derived_from"),
                ("forkedFrom", "derived_from"),
            ):
                add_lineage(rec.get(field_name), rel_name)

            if rtype == "continued-in":
                add_lineage(rec.get("continuedInSessionId"), "continued_in", ts)
            elif rtype == "derived-from":
                # One source session can be listed once per mechanism (compact, fork, ...).
                sources: dict[str, set[str]] = {}
                entries = rec.get("sessions")
                for entry in entries if isinstance(entries, list) else []:
                    if isinstance(entry, dict) and isinstance(entry.get("id"), str):
                        vias = sources.setdefault(entry["id"], set())
                        if isinstance(entry.get("via"), str):
                            vias.add(entry["via"])
                for other, vias in sources.items():
                    add_lineage(other, "derived_from", ts, via=vias)
            elif rtype == "fork-context-ref":
                add_lineage(rec.get("parentSessionId"), "child_of")
            elif rtype in _LABEL_KEYS:
                field_name, kind = _LABEL_KEYS[rtype]
                label = rec.get(field_name)
                if isinstance(label, str) and label.strip():
                    _set_session_label(db, sess_node, kind, label.strip())
            elif rtype == "attachment":
                attachment = rec.get("attachment")
                if isinstance(attachment, dict):
                    atype = attachment.get("type")
                    # Only names and URLs are read, never attached file contents.
                    # edited_text_file reports a change made outside the session's
                    # own tools (user or linter), so it counts as a read.
                    if atype in ("compact_file_reference", "edited_text_file"):
                        add_file(
                            attachment.get("filename") or attachment.get("displayPath"),
                            "read_file",
                            ts,
                        )
                    elif atype == "remote_session_change":
                        raw_url = attachment.get("url")
                        uid = _safe_url_id(raw_url) if isinstance(raw_url, str) else None
                        if uid:
                            add_url(uid, "cited_url", ts)

            git_branch = rec.get("gitBranch")
            # "HEAD" is the placeholder for a detached checkout, not a branch.
            if git_branch and last_cwd and isinstance(git_branch, str):
                repo_info = _detect_git_repo(Path(last_cwd), repo_cache)
                if repo_info is not None:
                    repo_root, rid = repo_info
                    short_br = strip_branch_ref(git_branch)
                    if short_br and short_br != "HEAD":
                        br_node = branch_id(rid, short_br)
                        if active_branch != br_node:
                            if active_branch and branch_start:
                                db.upsert_edge(
                                    sess_node,
                                    active_branch,
                                    "worked_in_branch",
                                    "claude_jsonl",
                                    valid_from=branch_start,
                                    valid_to=branch_last or branch_start,
                                    source_ref=rel_source,
                                )
                                stats["edges"] += 1
                            db.upsert_node(rid, "Repo", title=repo_root.name)
                            db.upsert_node(
                                br_node,
                                "Branch",
                                title=short_br,
                                metadata={"branch": short_br},
                            )
                            db.upsert_edge(br_node, rid, "in_repo", "claude_jsonl", source_ref=rel_source)
                            active_branch = br_node
                            branch_start = str(ts) if ts else None
                        if ts:
                            branch_last = str(ts)

            # Inspect message.content ONLY (never tool_result bodies)
            msg = rec.get("message")
            if not isinstance(msg, dict):
                continue
            content = msg.get("content")
            if not isinstance(content, list):
                continue

            for block in content:
                if not isinstance(block, dict):
                    continue
                btype = block.get("type")
                if btype == "tool_result":
                    # Strictly ignore tool_result bodies
                    continue
                if btype == "text":
                    for uid in _extract_urls(block.get("text") or ""):
                        add_url(uid, "cited_url", ts)
                elif btype == "tool_use":
                    tname = str(block.get("name") or "")
                    tinput = block.get("input") or {}
                    if not isinstance(tinput, dict):
                        continue

                    if tname in _READ_TOOLS or tname in _WRITE_TOOLS:
                        rel_name = "read_file" if tname in _READ_TOOLS else "modified_file"
                        for key in _FILE_ARG_KEYS:
                            add_file(tinput.get(key), rel_name, ts)

                    raw_url = tinput.get("url")
                    if isinstance(raw_url, str) and raw_url.strip():
                        uid = _safe_url_id(raw_url)
                        if uid:
                            add_url(uid, "fetched_url" if tname in _FETCH_TOOLS else "cited_url", ts)

                    # Extract any URLs cited inside prompt/query/command args
                    for arg_key in _URL_ARG_KEYS:
                        val = tinput.get(arg_key)
                        if isinstance(val, str):
                            for uid in _extract_urls(val):
                                add_url(uid, "cited_url", ts)

    if active_session and active_branch and branch_start:
        db.upsert_edge(
            active_session,
            active_branch,
            "worked_in_branch",
            "claude_jsonl",
            valid_from=branch_start,
            valid_to=branch_last or branch_start,
            source_ref=rel_source,
        )
        stats["edges"] += 1

    final_prefix = _prefix_sha256(path, min(offset, PREFIX_BYTES))
    db.set_sync_state(
        "claude_jsonl",
        source_key,
        byte_offset=offset,
        line_count=line_count,
        prefix_sha256=final_prefix,
        extra={
            "session_node_id": active_session,
            "active_branch": active_branch,
            "branch_start": branch_start,
            "branch_last": branch_last,
            "last_cwd": last_cwd,
            "parser_version": PARSER_VERSION,
        },
    )
    return stats


def sync_claude_root(
    db: LinkStoreDB,
    claude_root: Path | str,
    policy: BoundaryPolicy | None = None,
) -> dict[str, int]:
    """Incrementally ingest all *.jsonl transcripts under claude_root."""
    root = Path(claude_root).expanduser().resolve()
    pol = policy or BoundaryPolicy()
    repo_cache: dict[Path, tuple[Path, str] | None] = {}
    totals = {"files": 0, "records": 0, "edges": 0, "skipped_denied": 0}
    if not root.exists():
        return totals

    for jsonl_path in sorted(root.rglob("*.jsonl")):
        if not pol.is_allowed(jsonl_path):
            totals["skipped_denied"] += 1
            continue
        totals["files"] += 1
        res = _sync_single_jsonl(db, jsonl_path, root, pol, repo_cache)
        totals["records"] += res["records"]
        totals["edges"] += res["edges"]
        totals["skipped_denied"] += res["skipped_denied"]
    return totals
