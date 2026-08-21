---
tags:
  - ai
  - tools
  - cli
  - antigravity
---
Where Antigravity CLI sessions are stored and how to parse transcripts, subagent trees, background tasks, and artifacts.

## Storage Locations

All session state is stored per conversation ID under the Antigravity application directory:
- **Windows:** `C:\Users\<user>\.gemini\antigravity-cli\brain\<conversation-id>\`
- **Linux / macOS:** `~/.gemini/antigravity-cli/brain/<conversation-id>/`

### Directory Structure
```
brain/<conversation-id>/
├── .system_generated/
│   ├── logs/
│   │   ├── transcript.jsonl        # Compact transcript (large outputs truncated)
│   │   └── transcript_full.jsonl   # Complete, untruncated full record
│   └── tasks/
│       └── task-<id>.log           # Stdout/stderr logs of background CLI commands
├── scratch/                        # Temporary scripts and one-off debug files
└── *.md                            # User-facing artifacts and plans
```

## Transcript Schema (`.jsonl`)

Each line in `transcript.jsonl` is a JSON object with the following schema:
- `step_index`: Sequential integer index of the action.
- `source`: Source identifier (`USER_EXPLICIT`, `MODEL`, `SYSTEM`).
- `type`: Step type (`USER_INPUT`, `PLANNER_RESPONSE`, `SUBAGENT_NOTIFICATION`, `TASK_NOTIFICATION`).
- `status`: Execution status (`DONE`, `RUNNING`, `ERROR`).
- `created_at`: ISO 8601 timestamp.
- `content`: Text response or tool result.
- `thinking`: Model internal reasoning blocks (for planner responses).
- `tool_calls`: Array of tool calls made in the turn (`name`, `arguments`).
- `truncated_fields`: Array of fields truncated in `transcript.jsonl` (view `transcript_full.jsonl` for full body).

## Useful Inspection Commands

### 1. View all user prompts in a session
```bash
grep '"type":"USER_INPUT"' .system_generated/logs/transcript.jsonl
```

### 2. Trace subagent invocations
```bash
grep "invoke_subagent" .system_generated/logs/transcript.jsonl
```

### 3. Check background task outputs
```bash
# View specific task log
cat .system_generated/tasks/task-145.log

# Or check live status within Antigravity:
# manage_task Action="status" TaskId="<conversation-id>/task-145"
```

### 4. Open session in UI
Use the markdown conversation protocol in any Antigravity chat:
```markdown
[Open past session](conversation://<conversation-id>)
```

### Related
- [[how to inspect Claude Code sessions]]
- [[how to inspect Codex sessions]]
- [[agentic tooling upgrades over grep]]
