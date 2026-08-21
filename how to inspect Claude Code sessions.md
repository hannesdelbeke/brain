---
tags:
  - ai
  - tools
  - cli
  - claude-code
---
Where Claude Code sessions are stored and how to inspect project transcripts, subagent calls, token costs, and debug logs.

## Storage Locations

Claude Code stores session state per project under the user's `.claude` directory:
- **Windows:** `C:\Users\<user>\.claude\`
- **Linux / macOS:** `~/.claude/`

### Directory Structure
```
~/.claude/
├── projects/
│   └── <project-slug-or-hash>/
│       ├── <session-uuid>.jsonl         # Main session transcript
│       └── <session-uuid>/              # Subagent transcripts (if spawned)
│           └── <subagent-uuid>.jsonl
├── history.jsonl                        # User prompt history across projects
├── debug/
│   └── <session-uuid>.txt               # Verbose runtime & API debug logs
├── cache/
│   └── changelog.md                     # CLI release cache
└── CLAUDE.md                            # Global instructions
```

## Transcript Schema (`.jsonl`)

Each line in a project `.jsonl` file represents a message event with:
- `message.id`: Unique message identifier (note: Claude Code writes one JSONL line per content block and repeats `message.id`; deduplicate on `(message.id, text)`).
- `type`: Block type (`message`, `tool_use`, `tool_result`, `thinking`).
- `role`: `user` or `assistant`.
- `content`: Array of content blocks with text, tool inputs, and results.
- `usage`: Per-turn token metrics (`input_tokens`, `output_tokens`, `cache_creation_input_tokens`, `cache_read_input_tokens`).

## Useful Inspection Commands

### 1. Resume or inspect interactively
```bash
# Resume specific session in terminal
claude --resume <session-uuid>

# Or inside an active session:
/resume
```

### 2. Find latest project transcripts
```powershell
Get-ChildItem -Path "$HOME\.claude\projects" -Recurse -Filter *.jsonl | Sort-Object LastWriteTime -Descending | Select-Object -First 5
```

### 3. Extract assistant text without thinking blocks
```python
import json
from pathlib import Path

seen = set()
for line in Path("~/.claude/projects/.../session.jsonl").expanduser().read_text().splitlines():
    data = json.loads(line)
    if data.get("role") == "assistant":
        msg_id = data.get("message", {}).get("id")
        for block in data.get("content", []):
            if block.get("type") == "text":
                txt = block.get("text", "")
                if (msg_id, txt) not in seen:
                    seen.add((msg_id, txt))
                    print(txt)
```

### 4. Calculate token cost weighting
Formula for base-input equivalent token weighting:
$$\text{Cost Units} = \text{cache\_read} \times 0.1 + \text{cache\_creation} \times 1.25 + \text{output} \times 5 + \text{input}$$
(Multiply by $\$5 / 10^6$ for estimated USD on Claude Opus rates).

### Related
- [[how to inspect antigravity cli sessions]]
- [[how to inspect Codex sessions]]
- [[2026-08-19 open source claude code mobile equivalents]]
- [[agentic tooling upgrades over grep]]
