---
tags:
- ai
- workflow
- planning
---
# AI Review Queue Workflow

## The Goal
A centralized inbox where the AI logs any note it creates or heavily modifies autonomously. You can asynchronously review this list, drop feedback, and the AI will process it offline.

## 1. The Trigger (Agent Rule)
We add a global rule to `AGENTS.md` (or as a system hook): 
*"Whenever you create a new note or make significant autonomous changes, append a link to it in [[AI Review Queue]] along with a 1-sentence summary of what was done."*

## 2. The Queue Format (`AI Review Queue.md`)
The queue is a simple markdown list of checkboxes. When you review it, you just drop your thoughts as sub-bullets:

- [ ] [[new note name]] - Extracted the zepp sleep data into a summary.
    - *User feedback: make the tone less robotic, and add a graph.*
- [ ] [[another note]] - Created new script for auto-backups.

## 3. The Offline Batch Processor 
An Antigravity agent scheduled cron job (or just an agent you trigger manually with a `/goal`) runs periodically:
1. It reads `AI Review Queue.md`.
2. It looks for any `[ ]` unchecked items that have user feedback sub-bullets attached.
3. It opens the linked note and applies the requested feedback/edits.
4. It marks the checkbox as `[x]` (or deletes the block) to indicate the feedback was resolved.

## Benefits
- **Asynchronous pair programming**: You don't have to wait for the AI to finish typing during your active work sessions. You batch your reviews on your own time.
- **Traceability**: You never lose track of what the AI has been doing while running in the background or while you were asleep.
