#!/bin/sh
# setup_mac.sh - Configure agent-comms static allowlists, defaults, and TCC permissions on macOS
#
# Usage:
#   sh setup_mac.sh [bus_name]
#
# Example:
#   sh setup_mac.sh project-a

set -eu

BUS="${1:-project-a}"
SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd)
COMMS_SH=$(cd "$SCRIPT_DIR/.." && pwd)/comms.sh

mkdir -p "$HOME/.local/bin"

if [ -f "$COMMS_SH" ]; then
  chmod +x "$COMMS_SH"
  ln -sf "$COMMS_SH" "$HOME/.local/bin/comms"
  echo "✓ symlinked comms -> $COMMS_SH"
fi

export PATH="$HOME/.local/bin:$PATH"

if command -v comms >/dev/null 2>&1; then
  comms config set default_bus "$BUS"
  comms config set git 1
  echo "✓ comms configured: default_bus=$BUS, git=1"
else
  echo "warning: comms command not found in PATH" >&2
fi

# Configure static allowlists in ~/.claude/settings.json
python3 - <<'EOF'
import json
import pathlib
import sys

settings_path = pathlib.Path.home() / ".claude/settings.json"
settings_path.parent.mkdir(parents=True, exist_ok=True)

if settings_path.exists() and settings_path.stat().st_size > 0:
    try:
        data = json.loads(settings_path.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"Warning: could not parse existing {settings_path}: {e}", file=sys.stderr)
        data = {}
else:
    data = {}

permissions = data.setdefault("permissions", {})
allow_list = permissions.setdefault("allow", [])

rules = [
    # comms tool allowlist (covers comms --me <name> <cmd>)
    "Bash(comms *)",
    "Bash(comms)",
    # Read-only and essential git operations
    "Bash(git status*)",
    "Bash(git diff*)",
    "Bash(git log*)",
    "Bash(git rev-parse*)",
    "Bash(git show*)",
    "Bash(git branch*)",
    "Bash(git fetch*)",
    "Bash(git checkout*)",
    "Bash(git switch*)",
    # Agent identity git writes
    "Bash(git -c user.name=Claude -c user.email=noreply@anthropic.com push*)",
    "Bash(git -c user.name=Claude -c user.email=noreply@anthropic.com checkout*)",
    "Bash(git -c user.name=Claude -c user.email=noreply@anthropic.com switch*)",
    # Read-only shell utilities
    "Bash(ls*)",
    "Bash(cat *)",
    "Bash(head *)",
    "Bash(tail *)",
    "Bash(grep *)",
    "Bash(rg *)",
    "Bash(find *)",
    "Bash(which *)"
]

added = 0
for r in rules:
    if r not in allow_list:
        allow_list.append(r)
        added += 1

settings_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
print(f"✓ ~/.claude/settings.json updated: {added} new rules added (total allow rules: {len(allow_list)})")
EOF

# Reset macOS TCC cached denial for Claude Code Documents folder
if [ "$(uname)" = "Darwin" ]; then
  if command -v tccutil >/dev/null 2>&1; then
    tccutil reset SystemPolicyDocumentsFolder com.anthropic.claude-code 2>/dev/null || true
    echo "✓ macOS TCC reset: SystemPolicyDocumentsFolder for com.anthropic.claude-code"
  else
    echo "note: tccutil not found"
  fi
else
  echo "note: skipping tccutil reset (not running on macOS: $(uname))"
fi

echo "Done! Comms setup complete."
