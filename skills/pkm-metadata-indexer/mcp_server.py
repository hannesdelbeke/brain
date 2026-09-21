"""Read-only MCP tools for searching and reading the local PKM vault."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from mcp.server.fastmcp import FastMCP


try:
    VAULTS = {
        name: Path(path).expanduser().resolve()
        for name, path in json.loads(os.environ["PKM_VAULTS_JSON"]).items()
    }
except (KeyError, json.JSONDecodeError, AttributeError, TypeError) as error:
    raise RuntimeError("PKM_VAULTS_JSON must map corpus names to vault paths") from error

SEARCH = Path(os.environ.get("PKM_SEARCH_SCRIPT", Path(__file__).with_name("search_vault.py"))).resolve()
PYTHON = Path(os.environ.get("PKM_PYTHON", sys.executable)).resolve()
SEARCH_VAULTS = json.loads(os.environ.get("PKM_SEARCH_VAULTS_JSON", "{}"))

mcp = FastMCP("pkm")


def safe_path(vault: str, note_path: str) -> Path:
    """Resolve a corpus-relative note path without allowing traversal."""
    root = VAULTS.get(vault)
    if root is None:
        raise ValueError(f"unknown vault {vault!r}; use one of {', '.join(sorted(VAULTS))}")
    candidate = (root / note_path).resolve()
    if candidate != root and root not in candidate.parents:
        raise ValueError("note path escapes the selected vault")
    if candidate.suffix.lower() != ".md":
        raise ValueError("only Markdown notes can be read")
    if not candidate.is_file():
        raise FileNotFoundError(f"note not found: {vault}/{note_path}")
    return candidate


@mcp.tool()
def pkm_search(query: str, vault: str | None = None, top: int = 5) -> str:
    """Search local PKM notes and return ranked matching sections."""
    if not query.strip():
        raise ValueError("query must not be empty")
    if top < 1 or top > 20:
        raise ValueError("top must be between 1 and 20")
    command = [str(PYTHON), str(SEARCH), query, "--top", str(top), "--no-rerank"]
    if vault is not None:
        if vault not in VAULTS:
            raise ValueError(f"unknown vault {vault!r}; use one of {', '.join(sorted(VAULTS))}")
        command.extend(["--vault", SEARCH_VAULTS.get(vault, vault)])
    result = subprocess.run(
        command,
        cwd=next(iter(VAULTS.values())),
        capture_output=True,
        text=True,
        timeout=45,
        check=False,
    )
    if result.returncode:
        detail = result.stderr.strip() or result.stdout.strip()
        raise RuntimeError(f"PKM search failed ({result.returncode}): {detail}")
    return result.stdout


@mcp.tool()
def pkm_read_note(note_path: str, vault: str | None = None) -> str:
    """Read one Markdown note from the selected local PKM corpus."""
    if vault is None:
        vault = next(iter(VAULTS))
    return safe_path(vault, note_path).read_text(encoding="utf-8")


if __name__ == "__main__":
    mcp.run(transport="stdio")
