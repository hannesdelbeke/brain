---
date: 2026-08-28
created: 2026-08-28
tags:
  - ai
  - agents
  - architecture
  - self-learning
  - prompt-engineering
  - pkm
  - skills
aliases:
  - self learning agent supervisor
  - prompt failure distillation and self learning
  - agent retrospective feedback loop
  - continuous prompt audit and rule synthesis
---

# Proposal: Self-Learning Agent Supervisor & Continuous Prompt Failure Distillation

An architecture proposal for an automated, self-learning supervisor that continuously audits multi-agent session transcripts and Git history across machines, identifies recurring AI failure patterns from user corrections, and distills them into active rules, modular skills, and regression guards.

Related: [[public/cross-agent session indexing architecture|cross-agent session indexing architecture]], [[public/2026-08-28 agent instruction bloat - modular skills and compact synthesis|agent instruction bloat]], [[public/autocommit leftover changes|autocommit leftover changes]], [[public/human vs AI git history transfers between notes|human vs AI git history transfers]], [[token efficient PKM analysis architecture]]

---

## 1. Problem Statement: The Manual Correction Tax

Every user prompt is a call to action: spotting an issue, proposing an idea, fixing a bug, or requesting a build. 

In developer workflows with coding agents (Claude Code, Antigravity/AGY, Codex), a significant portion of prompts consists of **human interventions to fix repetitive agent mistakes**:
* Over-condensing authentic human voice and stripping raw dialogue.
* Using un-namespaced generic emails that hijack commit co-authorship.
* Wiping submodules on uninitialized repository clones.
* Creating dangling or broken wikilinks.
* Busy-spinning background loops that burn CPU cores.

Currently, these learnings remain trapped in ephemeral chat logs or require manual authoring of instructions in `AGENTS.md` or `SKILL.md`.

---

## 2. Core Vision: The Self-Learning Feedback Loop

Transform daily human corrections into a continuous, automated learning loop:

```
[Agent Execution] ──► [Human Correction Prompt] ──► [Git Diff / Commit]
                             │
                             ▼
               [Session Transcript Harvester]
             (Antigravity + Claude + CLI Logs)
                             │
                             ▼
              [Correction & Failure Extractor]
          (Detects "you broke X", reverts, fixes)
                             │
                             ▼
              [Pattern Clustering & Synthesis]
           (Groups recurring errors into archetypes)
                             │
                             ▼
               [Active Rule / Skill Update]
         (Modular SKILL.md, .githooks, AGENTS.md)
```

---

## 3. The 4-Stage Architecture Pipeline

### Stage 1: Ingestion & Transcript Normalization
* **Antigravity CLI:** Transcripts in `~/.gemini/antigravity-cli/brain/<id>/.system_generated/logs/transcript.jsonl`.
* **Claude Code:** Transcripts in `~/.claude/projects/` (cross-synced across developer machines).
* **Nightly Auto-Logger:** Background daily runner that ingests day logs and session transcripts.
* **Git Repository History:** Line-by-line diffs, commit messages, and author trailers (`git log -p`, `git blame -C -C -C`).

### Stage 2: Prompt-to-Correction Correlation Engine
Identifies turns where the human had to intervene or correct the agent:
* **Linguistic Heuristics:** Prompts matching correction signals (*"you lost X"*, *"don't over-condense"*, *"that broke Y"*, *"restore original"*, *"undo"*).
* **Diff Reversions:** Consecutive commits where human edits delete or revert AI-generated lines.
* **Tool Failure / Retry Loops:** Turns where tools returned non-zero exit codes or required multiple attempts.

### Stage 3: Pattern Clustering & Failure Archetype Classification
Groups individual incidents into systemic failure categories:
1. **Context & Tone Truncation:** Over-condensing user dialogue into dry summaries.
2. **Attribution & Provenance Errors:** Generic email trailers colliding with third-party accounts.
3. **Submodule & Workspace Traps:** Git commands executed in wrong directories or uninitialized clones.
4. **Performance & Resource Waste:** Busy-polling loops or runaway token overhead.

### Stage 4: Automated Skill & Rule Distillation
Instead of appending bloat to a monolithic `AGENTS.md`, the system:
1. Matches the failure against the modular skill registry (`skills/`).
2. Synthesizes a discrete, imperative rule or adds a test case to the relevant skill's regression suite.
3. Deploys concrete preventative guards (e.g. `.githooks/pre-commit` link checkers or deletion thresholds).

---

## 4. Data Model & Storage Strategy

A hybrid architecture balancing structured querying, deep memory, and human review:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          STORAGE ARCHITECTURE                               │
├─────────────────────────┬───────────────────────────────────────────────────┤
│ Layer                   │ Purpose & Mechanism                               │
├─────────────────────────┼───────────────────────────────────────────────────┤
│ 1. SQLite Database      │ Structured tables: sessions, turns, corrections,  │
│    (agent_learning.db)  │ failure_clusters, and rule_links.                 │
├─────────────────────────┼───────────────────────────────────────────────────┤
│ 2. Git History          │ Immutable ground truth for code provenance,       │
│                         │ line attribution, and commit diff pairing.        │
├─────────────────────────┼───────────────────────────────────────────────────┤
│ 3. Vault Markdown Hubs  │ Human-readable claims, failure pattern logs, and  │
│                         │ modular SKILL.md rulebooks.                       │
├─────────────────────────┼───────────────────────────────────────────────────┤
│ 4. Vector / FTS5 Index  │ Fast hybrid semantic search across past errors    │
│    (searchd.py daemon)  │ and solutions (<50ms recall).                     │
└─────────────────────────┴───────────────────────────────────────────────────┘
```

---

## 5. End-to-End Walkthrough: Concrete Real-World Example

### Step 1: The Incident (Session Turn)
* **Agent Action:** Agent executes an aggressive condensing pass on `day 2026-08-28.md`, replacing verbatim dialogue (*"Food brought to you, isn't it nice?"*) with generic psychological summaries.
* **Human Prompt (Correction):** *"i feel a lot of my original notes were lost compared to original first pass note written by me. ai came to a few conclusions or summaries i m unsure about."*

### Step 2: Ingestion & Extraction
* The supervisor daemon flags the prompt as a **High-Priority Correction** (signals: *"lost"*, *"unsure about"*, prompt issued immediately after an agent edit).
* Compares Git commit diffs between the raw human entry (`21a223cc`) and the AI edit (`77bb3586`), identifying a 50% line reduction and deletion of quoted dialogue.

### Step 3: Pattern Classification
* Classified under **Archetype: `lossy-human-voice-compaction`**.
* Historical scan finds 3 similar past instances where user asked to restore verbatim quotes after summarization.

### Step 4: Rule Synthesis & Prevention
* The supervisor generates an update to `skills/journal-curation/SKILL.md` and `AGENTS.md`:
  > **Invariant:** When structuring journal entries, preserve verbatim quotes, specific dialogue, and concrete grounding details. Only summarize surrounding context.
* Creates a regression check: If an edit reduces line count by >30% on a human journal note without an explicit instruction to truncate quotes, prompt for confirmation.

---

## 6. Integration with Existing PKM Infrastructure

* **`searchd.py` & Metadata Indexer:** Reuses the existing session scanning engine from [[public/cross-agent session indexing architecture|cross-agent session indexing architecture]] to parse transcripts with zero extra daemon overhead.
* **Nightly Batch Reflection:** Hooks into scheduled daily maintenance runs to execute automated failure clustering and rule distillation.
* **Modular Skills System:** Directly updates JSON/YAML skill manifests per [[public/2026-08-28 agent instruction bloat - modular skills and compact synthesis|modular agent instruction synthesis]].

---

## 7. Original Proposal Prompt (Historical Provenance)

> *Every prompt is a call to action: write new idea, fix an issue, make a thing. We now have some kind of session tracker or reader. Also relates to tracking prompt history and the automated daily logger. Go through all prompts on this machine, and identify what went wrong. Check the summary if there is one for the session (I know Claude has a recap, unsure if AGY does), then see if the prompt was resolved: what work or note it created, and then in future what issues it caused, or mistakes it made, or things it missed. Then link it to skills we extracted from this. How would this work? Would we store data, store SQL only, links only? Git history and session will be main source of truth (session data distributed across development hardware). End goal: by identifying where we went wrong and where we introduced bugs or shortcomings, we can come up with a system that can be self-learning—an external thing that watches our process day to day, and identifies issues. Nearly every prompt is me spotting an issue and asking AI to fix it. There might be patterns in things AI often breaks. I'd like you to find those patterns, and for that we might need a system.*
