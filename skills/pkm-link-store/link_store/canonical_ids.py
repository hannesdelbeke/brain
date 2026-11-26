"""Shared canonical ID builders for PKM link store entities."""

from __future__ import annotations

import posixpath
import re
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

_SSH_REMOTE_RE = re.compile(r"^[^@]+@([^:]+):(.+)$")
_REMOTE_REF_RE = re.compile(r"^refs/remotes/[^/]+/(.+)$")
_TRAILING_URL_PUNCT = ".,;:!?)>]}\'\""

BOILERPLATE_HOSTS = frozenset(
    {
        "localhost",
        "127.0.0.1",
        "0.0.0.0",
        "example.com",
        "example.org",
        "example.net",
        "w3.org",
        "www.w3.org",
        "purl.org",
        "json-schema.org",
        "schemas.openxmlformats.org",
    }
)

SENSITIVE_QUERY_PARAMS = frozenset(
    {
        "token",
        "access_token",
        "refresh_token",
        "id_token",
        "auth",
        "key",
        "api_key",
        "apikey",
        "secret",
        "password",
        "passwd",
        "sig",
        "signature",
        "code",
        "session",
        "jwt",
        "bearer",
        "credential",
        "private_key",
        "x-amz-signature",
        "x-amz-security-token",
        "x-goog-signature",
    }
)


def session_id(uuid: str, agent_id: str | None = None) -> str:
    """Build canonical session ID, distinguishing parent sessions from subagents."""
    clean_uuid = uuid.strip()
    if not clean_uuid:
        raise ValueError("session uuid cannot be empty")
    if agent_id:
        clean_agent = agent_id.strip()
        if clean_agent.startswith("agent-"):
            clean_agent = clean_agent[len("agent-"):]
        if clean_agent:
            return f"session:{clean_uuid}:agent-{clean_agent}"
    return f"session:{clean_uuid}"


def repo_id(remote_url: str | None = None, fallback_name: str | None = None) -> str:
    """Build canonical repo:<host>/<owner>/<repo> from a git remote URL or fallback."""
    if remote_url:
        raw = remote_url.strip()
        ssh_match = _SSH_REMOTE_RE.match(raw)
        if ssh_match:
            host = ssh_match.group(1).lower()
            path = ssh_match.group(2).strip("/")
        elif "://" in raw:
            parsed = urlparse(raw)
            host = (parsed.hostname or "local").lower()
            path = parsed.path.strip("/")
        else:
            host = "local"
            path = raw.replace("\\", "/").strip("/")

        if path.endswith(".git"):
            path = path[:-4]
        parts = [p for p in path.split("/") if p]
        if len(parts) >= 2:
            owner, repo = parts[-2].lower(), parts[-1].lower()
            return f"repo:{host}/{owner}/{repo}"
        if parts:
            return f"repo:{host}/{parts[-1].lower()}"

    name = (fallback_name or "unknown").strip().lower().replace(" ", "-")
    return f"repo:local/{name}"


def _repo_slug(repo_id_str: str) -> str:
    return repo_id_str[5:] if repo_id_str.startswith("repo:") else repo_id_str


def strip_branch_ref(branch_ref: str) -> str:
    """Strip refs/heads/ or refs/remotes/<remote>/ without stripping feat/ from feat/x."""
    ref = branch_ref.strip()
    if ref.startswith("refs/heads/"):
        return ref[len("refs/heads/"):]
    remote_match = _REMOTE_REF_RE.match(ref)
    if remote_match:
        return remote_match.group(1)
    return ref


def branch_id(repo_id_str: str, branch_ref: str) -> str:
    """Build canonical branch:<repo_id>@<short_branch>."""
    short = strip_branch_ref(branch_ref)
    if not short:
        raise ValueError("branch_ref cannot be empty")
    return f"branch:{_repo_slug(repo_id_str)}@{short}"


def commit_id(repo_id_str: str, sha40: str) -> str:
    """Build canonical commit:<repo_id>@<sha40>."""
    sha = sha40.strip().lower()
    if len(sha) != 40:
        raise ValueError(f"Expected 40-char commit SHA, got {sha40!r}")
    return f"commit:{_repo_slug(repo_id_str)}@{sha}"


def _norm_rel_path(rel_path: str) -> str:
    cleaned = rel_path.replace("\\", "/").strip()
    while cleaned.startswith("./"):
        cleaned = cleaned[2:]
    cleaned = cleaned.lstrip("/")
    return posixpath.normpath(cleaned)


def note_id(vault: str, rel_path: str) -> str:
    """Build canonical note:<vault>/<rel_path>."""
    norm = _norm_rel_path(rel_path)
    return f"note:{vault.strip()}/{norm}"


def file_id(repo_id_str: str, rel_path: str) -> str:
    """Build canonical file:<repo_id>@<rel_path>."""
    norm = _norm_rel_path(rel_path)
    return f"file:{_repo_slug(repo_id_str)}@{norm}"


def url_id(raw_url: str) -> str | None:
    """Canonicalize a URL, filtering boilerplate hosts and redacting sensitive query params."""
    text = raw_url.strip()
    while text and text[-1] in _TRAILING_URL_PUNCT:
        if text[-1] == ")" and text.count("(") >= text.count(")"):
            break
        text = text[:-1]

    parsed = urlparse(text)
    scheme = parsed.scheme.lower()
    if scheme not in ("http", "https") or not parsed.netloc:
        return None

    host = (parsed.hostname or "").lower()
    if not host or host in BOILERPLATE_HOSTS:
        return None

    port = parsed.port
    if (scheme == "http" and port == 80) or (scheme == "https" and port == 443):
        netloc = host
    elif port:
        netloc = f"{host}:{port}"
    else:
        netloc = host

    filtered_qs = [
        (k, v)
        for k, v in parse_qsl(parsed.query, keep_blank_values=True)
        if k.lower() not in SENSITIVE_QUERY_PARAMS
    ]
    query = urlencode(filtered_qs, doseq=True)
    path = parsed.path or "/"
    if path != "/" and path.endswith("/"):
        path = path.rstrip("/")

    canonical = urlunparse((scheme, netloc, path, "", query, ""))
    return f"url:{canonical}"
