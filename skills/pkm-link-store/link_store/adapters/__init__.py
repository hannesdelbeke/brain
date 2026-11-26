"""Adapters and shared boundary policy for pkm-link-store."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from ..canonical_ids import file_id, note_id


def _norm_path(path: Path | str) -> Path:
    return Path(os.path.abspath(os.path.expanduser(str(path))))


def _is_under(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


@dataclass
class BoundaryPolicy:
    """Allow/deny path filter and vault/repo path resolver."""

    allow_roots: tuple[Path, ...] = ()
    deny_roots: tuple[Path, ...] = ()
    vault_roots: dict[str, Path] = field(default_factory=dict)

    @classmethod
    def from_args(
        cls,
        allow_roots: list[str | Path] | None = None,
        deny_roots: list[str | Path] | None = None,
        vault_roots: dict[str, str | Path] | None = None,
    ) -> "BoundaryPolicy":
        return cls(
            allow_roots=tuple(_norm_path(p) for p in (allow_roots or [])),
            deny_roots=tuple(_norm_path(p) for p in (deny_roots or [])),
            vault_roots={k: _norm_path(v) for k, v in (vault_roots or {}).items()},
        )

    def is_allowed(self, path: Path | str) -> bool:
        """Return True if path is not under any deny_root and matches allow_roots (if set)."""
        norm = _norm_path(path)
        for deny in self.deny_roots:
            if _is_under(norm, deny):
                return False
        if self.allow_roots:
            return any(_is_under(norm, allow) for allow in self.allow_roots)
        return True

    def resolve_vault_note(self, path: Path | str) -> tuple[str, str] | None:
        """If path is a .md file inside a configured vault_root, return (note_id, rel_path)."""
        norm = _norm_path(path)
        if norm.suffix.lower() != ".md":
            return None
        # Prefer deepest matching vault root (e.g. public/ inside root pkm/)
        best_match: tuple[int, str, str] | None = None
        for vault_name, root in self.vault_roots.items():
            if _is_under(norm, root):
                rel = norm.relative_to(root).as_posix()
                depth = len(root.parts)
                if best_match is None or depth > best_match[0]:
                    best_match = (depth, vault_name, rel)
        if best_match is None:
            return None
        _, vault_name, rel = best_match
        return note_id(vault_name, rel), rel

    def resolve_target(
        self, path: Path | str, repo_root: Path | None = None, repo_id_str: str | None = None
    ) -> tuple[str, str, str] | None:
        """Resolve a file path to (canonical_id, node_type, title) if allowed."""
        if not self.is_allowed(path):
            return None
        norm = _norm_path(path)
        vault_hit = self.resolve_vault_note(norm)
        if vault_hit is not None:
            nid, rel = vault_hit
            return nid, "Note", norm.name
        if repo_root is not None and repo_id_str is not None and _is_under(norm, _norm_path(repo_root)):
            rel = norm.relative_to(_norm_path(repo_root)).as_posix()
            return file_id(repo_id_str, rel), "File", norm.name
        return None


from .claude_jsonl import sync_claude_root  # noqa: E402
from .git_adapter import sync_git_repo  # noqa: E402

__all__ = ["BoundaryPolicy", "sync_claude_root", "sync_git_repo"]
