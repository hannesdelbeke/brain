---
energy: 5
sentiment:
- 5
sentiment-hash: f1151341
sentiment-label:
- reflective
tags:
- planning
- journal
- procrastination
- self-reflection
- work
---

> [!NOTE] 
> partly resolved. The scoring rule is decided and runs today with no plugin. Pulling in tasks that live outside this vault is still open, see Not covered.

## Context
some tasks, e.g. tax return, are only for a year from now.
Set a reminder in the calendar, and hopefully you'll do it then.
But the closer to the deadline the more important they become

How can you [[visualize|visualize]] this in planning?

What about the opposite.
A task with no deadline, but the longer it's not done, the more important it becomes?
e.g. a request from your manager, might become more damaging for your career the longer it's not done.
How to visualize this?
- add a priority score every day
- show a [[task list]] ordered by priority

It also would be easier if everything was in 1 system
## goal
become more [[productivity|productive]] and better at [[planning]]

## Plan

### scoring rule
One score, computed on read, covering both shapes. No daily manual scoring.

score = 100 / max(3, days_until_due + 3) + days_since_created / 3

The first term is the deadline shape. It stays near zero while the deadline is far off and climbs steeply in the last weeks. Reference points: due in 365 days scores 0.3, in 30 days scores 3, in 7 days scores 10, in 2 days scores 20, today or overdue scores 33. The max(3, ...) is what caps it at 33 instead of dividing by zero.

The second term is the rot shape, for tasks with no deadline. It adds one point per three days the task has existed. A request left for three weeks scores 7, left for a hundred days it scores 33, the same as a deadline hitting today.

A task with only a created date gets the second term only. A task with both gets both, so an old task with a near deadline outranks a fresh one with the same deadline. Tasks without a due date are treated as due in 10 years, which makes the first term round to nothing.

Two tuning knobs. The 3 inside max sets the ceiling for overdue work, raise it to lower the ceiling. The divisor 3 in the age term sets how fast things rot, raise it to 7 to make rot a weekly rather than near daily pressure.

### task syntax
Plain text on a normal checkbox, anywhere in the vault. Both fields are optional, but a task with neither will never surface. The bracket form is [[obsidian-dataview|Dataview]] inline field syntax, the emoji form is what the Tasks plugin writes, and both are read by the script below, so the syntax does not lock in a tool.

```text
- [ ] file tax return [due:: 2027-01-31] [created:: 2026-08-25]
- [ ] write the doc my manager asked for [created:: 2026-08-25]
- [ ] renew the passport 📅 2026-11-01 ➕ 2026-08-25
```

created is the date the task was written down, not the date it was started. It is the only thing that has to be typed by hand.

### day one, no plugins
No Obsidian plugin on this machine can do this today. Not Dataview, not Tasks, not Kanban, none of them are installed in any vault here, so any query based plan is blocked behind an install. The script is not.

    python skills/pkm-metadata-indexer/urgent_tasks.py

It scans every `- [ ]` line in the vault, skips fenced code blocks, computes the score, and prints the ordered list with file and line. Flags are `--top`, `--min-score`, and `--selfcheck`. The self check asserts the reference points above, so if the formula is ever edited the numbers are still checked. It lives with the other vault scripts in skills/pkm-metadata-indexer.

Tasks with neither date are skipped rather than scored zero, which keeps the old checkbox lists already scattered through the vault out of the way until they are dated on purpose.

### later, in Obsidian
The script prints to a terminal, it does not render inside a note. If seeing the list in Obsidian is worth one community plugin, install Dataview and paste this into a dashboard note. Same formula, same task syntax, no migration.

```dataview
TASK
WHERE !completed
FLATTEN 100 / max(list(3, default((due - date(today)).days, 3650) + 3)) + default((date(today) - created).days, 0) / 3 AS score
WHERE score > 1
SORT score DESC
LIMIT 25
```

The score > 1 line hides everything that is neither near a deadline nor older than three days. Drop that line to see the full ordered list.

### first step
Add created, and due where there is one, to three tasks that already exist. Run the script. Check whether the order matches what you would have picked yourself, and tune the two knobs against that, not in advance.

### not covered
Tasks that live in a work tracker, in a repo, or in [[Todoist]] are not in this score. Both the script and the query only see markdown in this vault, so the one system goal is only met for tasks written here. That is the same gap described in [[task manager cross project]] and it needs a sync or an export, not a formula.

How often a task gets mentioned is also not in the score, so the idea in [[Priority heatmap]] stays separate for now.
