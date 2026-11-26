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

_URL_RE = re.compile(r"https?://[^\s<>\"'`]+")
_READ_TOOLS = frozenset({"Read", "View", "NotebookRead", "read_file"})
_WRITE_TOOLS = frozenset({"Edit", "Write", "MultiEdit", "NotebookEdit", "edit_file", "write_file"})
_FETCH_TOOLS = frozenset({"WebFetch", "fetch_url", "browser"})
_FILE_ARG_KEYS = ("file_path", "notebook_path", "path", "TargetFile")


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


def _extract_urls(text: str) -> list[str]:
    out: list[str] = []
    for match in _URL_RE.findall(text):
        cid = url_id(match)
        if cid:
            out.append(cid)
    return out


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

    if state and int(state["byte_offset"]) <= file_size:
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

    rel_source = path.relative_to(claude_root).as_posix()
    file_agent_hint = path.stem[len("agent-"):] if path.name.startswith("agent-") else None

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

            sess_uuid = rec.get("sessionId") or (
                path.parent.parent.name if file_agent_hint else path.stem
            )
            agent_id = rec.get("agentId") or file_agent_hint
            if not sess_uuid:
                continue

            sess_node = session_id(str(sess_uuid), str(agent_id) if agent_id else None)
            if active_session != sess_node:
                active_session = sess_node
                db.upsert_node(
                    sess_node,
                    "Session",
                    title=str(sess_uuid) if not agent_id else f"{sess_uuid} (agent-{agent_id})",
                    metadata={"source_file": rel_source},
                )
                db.upsert_alias(rel_source, sess_node)
                if not agent_id:
                    db.upsert_alias(str(sess_uuid), sess_node)
                else:
                    parent_node = session_id(str(sess_uuid))
                    db.upsert_node(parent_node, "Session", title=str(sess_uuid))
                    db.upsert_alias(str(sess_uuid), parent_node)
                    db.upsert_edge(
                        sess_node,
                        parent_node,
                        "child_of",
                        "claude_jsonl",
                        source_ref=f"{rel_source}:{line_count}",
                    )
                    stats["edges"] += 1

            # Session lineage fields if present
            for field_name, rel_name in (
                ("continuedIn", "continued_in"),
                ("derivedFrom", "derived_from"),
                ("forkedFrom", "derived_from"),
            ):
                other = rec.get(field_name)
                if isinstance(other, str) and other.strip():
                    other_node = session_id(other.strip())
                    db.upsert_node(other_node, "Session", title=other.strip())
                    db.upsert_edge(
                        sess_node,
                        other_node,
                        rel_name,
                        "claude_jsonl",
                        source_ref=f"{rel_source}:{line_count}",
                    )
                    stats["edges"] += 1

            ts = rec.get("timestamp")
            git_branch = rec.get("gitBranch")
            if git_branch and last_cwd and isinstance(git_branch, str):
                repo_info = _detect_git_repo(Path(last_cwd), repo_cache)
                if repo_info is not None:
                    repo_root, rid = repo_info
                    short_br = strip_branch_ref(git_branch)
                    if short_br:
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

            repo_info = _detect_git_repo(Path(last_cwd), repo_cache) if last_cwd else None
            repo_root = repo_info[0] if repo_info else None
            rid = repo_info[1] if repo_info else None

            for block in content:
                if not isinstance(block, dict):
                    continue
                btype = block.get("type")
                if btype == "tool_result":
                    # Strictly ignore tool_result bodies
                    continue
                if btype == "text":
                    text = block.get("text") or ""
                    for uid in _extract_urls(text):
                        db.upsert_node(uid, "Url", title=uid[4:])
                        db.upsert_edge(
                            sess_node,
                            uid,
                            "cited_url",
                            "claude_jsonl",
                            valid_from=str(ts) if ts else None,
                            source_ref=f"{rel_source}:{line_count}",
                        )
                        stats["edges"] += 1
                elif btype == "tool_use":
                    tname = str(block.get("name") or "")
                    tinput = block.get("input") or {}
                    if not isinstance(tinput, dict):
                        continue

                    if tname in _READ_TOOLS or tname in _WRITE_TOOLS:
                        rel_name = "read_file" if tname in _READ_TOOLS else "modified_file"
                        for key in _FILE_ARG_KEYS:
                            raw_fp = tinput.get(key)
                            if not isinstance(raw_fp, str) or not raw_fp.strip():
                                continue
                            fp = Path(raw_fp)
                            if not fp.is_absolute() and last_cwd:
                                fp = Path(last_cwd) / fp
                            target = policy.resolve_target(fp, repo_root=repo_root, repo_id_str=rid)
                            if target is None:
                                stats["skipped_denied"] += 1
                                continue
                            dst_id, dst_type, dst_title = target
                            db.upsert_node(dst_id, dst_type, title=dst_title)
                            db.upsert_edge(
                                sess_node,
                                dst_id,
                                rel_name,
                                "claude_jsonl",
                                valid_from=str(ts) if ts else None,
                                source_ref=f"{rel_source}:{line_count}",
                            )
                            stats["edges"] += 1

                    raw_url = tinput.get("url")
                    if isinstance(raw_url, str) and raw_url.strip():
                        uid = url_id(raw_url)
                        if uid:
                            db.upsert_node(uid, "Url", title=uid[4:])
                            url_rel = "fetched_url" if tname in _FETCH_TOOLS else "cited_url"
                            db.upsert_edge(
                                sess_node,
                                uid,
                                url_rel,
                                "claude_jsonl",
                                valid_from=str(ts) if ts else None,
                                source_ref=f"{rel_source}:{line_count}",
                            )
                            stats["edges"] += 1

                    # Extract any URLs cited inside prompt/query/command args
                    for arg_key in ("prompt", "query", "description"):
                        val = tinput.get(arg_key)
                        if isinstance(val, str):
                            for uid in _extract_urls(val):
                                db.upsert_node(uid, "Url", title=uid[4:])
                                db.upsert_edge(
                                    sess_node,
                                    uid,
                                    "cited_url",
                                    "claude_jsonl",
                                    valid_from=str(ts) if ts else None,
                                    source_ref=f"{rel_source}:{line_count}",
                                )
                                stats["edges"] += 1

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
