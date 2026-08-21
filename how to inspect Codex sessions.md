---
tags:
  - ai
  - tools
  - cli
  - codex
---
Where OpenAI Codex CLI sessions are stored and how to inspect rollouts, SQLite logs, sandbox command outputs, and prompt history.

## Storage Locations

All Codex CLI session data lives in the user home `.codex` folder:
- **Windows:** `C:\Users\<user>\.codex\`
- **Linux / macOS:** `~/.codex/`

### Directory Structure
```
~/.codex/
├── sessions/
│   └── YYYY/MM/DD/
│       └── rollout-YYYY-MM-DDTHH-MM-SS-<uuid>.jsonl   # Full streamed turn transcript
├── history.jsonl                                      # Global prompt and command history
├── logs_2.sqlite                                      # Structured runtime logs
├── state_5.sqlite                                     # Active session & agent state
├── goals_1.sqlite                                     # Sub-goal planner records
├── memories_1.sqlite                                  # Long-term persistent memories
├── config.toml                                        # Global model & provider configs
└── .sandbox/
    └── sandbox.YYYY-MM-DD.log                         # Subprocess sandbox stdout/stderr
```

## Session Rollout Schema (`rollout-*.jsonl`)

Each rollout file is an event-streamed JSONL containing:
- `timestamp`: Event ISO timestamp.
- `type`: `event_msg`, `turn_context`, `response_item`.
- `payload`: Detailed turn events including:
  - `task_started` / `task_finished`: `started_at`, `turn_id`, `model_context_window`.
  - `tool_call`: CLI commands, file diffs, and tool arguments.
  - `token_usage`: Input, cached, and output token accounting per turn.

## Useful Inspection Commands

### 1. Find the latest session rollout
```powershell
Get-ChildItem -Path "$HOME\.codex\sessions" -Recurse -Filter *.jsonl | Sort-Object LastWriteTime -Descending | Select-Object -First 1
```

### 2. View recent prompts from global history
```bash
tail -n 25 ~/.codex/history.jsonl
```

### 3. Query structured logs from SQLite
```sql
sqlite3 ~/.codex/logs_2.sqlite "SELECT timestamp, message, level FROM logs ORDER BY timestamp DESC LIMIT 20;"
```

### 4. Inspect sandbox execution failures
```bash
# Check sandbox command runner output
tail -n 50 ~/.codex/.sandbox/sandbox.log
```

### Related
- [[how to inspect antigravity cli sessions]]
- [[how to inspect Claude Code sessions]]
- [[agentic tooling upgrades over grep]]
