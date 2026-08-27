---
date: 2026-08-27
created: 2026-08-27
tags:
  - ai
  - pkm
  - architecture
  - agentic
  - philosophy
aliases:
  - 2026-08-27 what an AI buddy actually needs
  - what an AI buddy actually needs
  - AI thought partner architecture
---

The [[AI-native knowledge formats beyond markdown and git]] note asks the wrong question. It asks "what's the ideal data structure for AI knowledge?" when the better question is "what would make an AI genuinely useful to me every single day?"

The answer turns out to be: not better storage, but better memory, better judgement about what to surface, and continuity across interactions. [[track prompt history]]?
The storage layer (markdown, SQLite, whatever) is a solved problem. The intelligence layer is not.

---

## Why the Storage Obsession is a Dead End

The old note proposes Merkle DAGs, CRDTs, typed schemas, FUSE virtual projections. These are interesting engineering ideas but they solve problems that don't actually bottleneck the system:

**Merge conflicts between humans and agents** are rare in practice. In a personal vault, there's one human. Agents run sequentially or on separate files. The scenario where a human and three agents are simultaneously editing the same paragraph simply doesn't happen often enough to justify replacing git with a CRDT framework. And when CRDTs do resolve a conflict, they do it by silently picking a winner — which is arguably worse for a knowledge base than a merge conflict that forces you to look.

**Schema drift across notes** (one note writes `battery: 6m`, another writes `BatteryLife: 180 days`) is a real annoyance but it's a linting problem, not an architecture problem. A validation pass over markdown files catches this. You don't need Markdoc or typed ASTs — you need a script that runs on save.

**Bit rot and corruption** are real but git already content-addresses every object. Adding SHA-256 Merkle hashing on top of git's existing SHA hashing is redundant.

The old note's one genuinely good idea is the **dual-layer compiler** (markdown as source, SQLite as compiled index). That pattern is sound, already partially implemented in [[pkm metadata indexer]], and doesn't require any of the exotic infrastructure the rest of the note proposes.

---

## What an AI Buddy Actually Needs

A PKM is a filing cabinet. You put things in, you search for them. An AI buddy is a thinking partner. The difference is the same as the difference between a notebook and a colleague who's read your notebook.

The capabilities that matter, in order of impact:

### 1. It Knows You (Persistent Identity Model)

Every conversation with an AI today starts from zero. The model doesn't know your health history, your projects, your communication preferences, your recurring mistakes, your values. You either re-explain context every time or you hope RAG retrieval grabs the right notes.

What's needed is a **living user profile** — not a static bio, but a continuously updated document that captures:

- **Facts**: senior software engineer and systems architect, based in Europe, background in graphics pipelines and local-first tooling, active marathon runner
- **Preferences**: keyboard-first navigation, dark mode, local-first tooling, dislikes bloatware, prefers flowing prose over rigid AI template patterns
- **Working style**: hyperfocuses for 4+ hours, builds meta-tools compulsively, energy dips mid-week, peak cognitive flow afternoon and late night
- **Active projects and goals**: PKM system, incubator game projects, DCC / Maya / procedural tooling, smart home BLE automation, health telemetry
- **Recurring failure modes**: forgets to eat/move during hyperfocus, lets medical follow-ups slip, spends time on tool-building that should go to tool-using, trusts AI output without verification

This profile gets injected into every AI interaction as high-priority context. The model doesn't need to be fine-tuned on your data — it just needs to read a good briefing document before every conversation.

ChatGPT's memory feature is a crude version of this (flat key-value facts like "user prefers Python"). The real version is richer — more like a thorough briefing memo that a new colleague would read on their first day.

The profile should be **human-readable and human-editable**. A markdown file, not a database. You should be able to open it, disagree with something, and correct it. The AI maintains it; you have veto power.

### 2. It Remembers Conversations (Episodic Continuity)

Right now every AI session is amnesiac. You discussed an database migration strategy last week. You discussed your ONNX daemon burning 12 cores yesterday. You brainstormed BLE proxy architectures this morning. None of those sessions know about each other.

Episodic memory means: after every significant AI interaction, a background process extracts key decisions, new facts, and open questions, and writes them to a structured memory store. The next conversation starts with those memories loaded.

This is different from "search your notes." Searching finds documents by content similarity. Episodic memory recalls *what happened between us* — what you asked, what I recommended, what you decided, what's still unresolved.

Concretely, this looks like an append-only log of "memory records":

```
2026-08-26 23:52 — User set up new ThinkPad. Key finding: searchd.py ONNX keepalive was burning 12 cores. Fix: set allow_spinning=0 and intra_op_num_threads=2. Status: documented, not yet applied.

2026-08-26 23:38 — Reviewed trending GitHub repos. Removed hallucinated awesome-ai-agents-2026. Identified sqlite-vec as potential replacement for NumPy search in pkm indexer. Status: noted, not started.

2026-08-27 00:15 — Discussed AI second brain architecture. User wants a buddy, not a PKM. Key insight: storage format doesn't matter; memory consolidation and proactive surfacing are the real gaps. Status: this note.
```

Each record is timestamped, has a status, and links to source notes. Simple, greppable, human-readable. Not a database. Not vectors. Just text that gets injected into future conversations when relevant.

### 3. It Thinks When You're Not Asking (Background Consolidation)

The most powerful thing a second brain could do is work while you're asleep. Not generating content — **distilling knowledge**.

Every day, you produce raw material: daily logs, health metrics, code commits, conversations, half-formed thoughts. Right now that material sits where it landed until you manually write an overnote. That overnote process is valuable — the [[2026-08-19 weekly notes overnote]] is proof — but it's manual, infrequent, and inconsistent.

Automated consolidation operates on three timescales:

**Nightly (tactical):**
- Read today's daily log, git commits across all repos, any new notes
- Extract: what happened, what was decided, what's unfinished
- Update the user profile with any new facts
- Flag contradictions (e.g. a note says "Claude Code supports remote PC driving" and another says it doesn't)
- Output: a one-page daily digest note, ready for morning review

**Weekly (strategic):**
- The overnote, but automated
- Cluster the week's activity into themes
- Identify patterns: energy levels, productivity cycles, recurring blockers
- Surface stale TODOs and commitments with no recent activity
- Output: the weekly synthesis you currently write manually

**Monthly (reflective):**
- Longer-term pattern detection across health data, work output, personal goals
- Compare this month's activity against stated goals
- Flag drift: "You said you wanted to repurpose old devices three weeks ago. No progress since the note was written."
- Update long-term sections of the user profile

The model doing this work doesn't need to be smart. Gemini Flash or a local 7B model is fine for extraction and summarisation. The intelligence is in the prompt design and the structure of what gets extracted — not in the model's raw reasoning power. Save the frontier model for the conversations where you're actually thinking together.

### 4. It Volunteers Information (Proactive Surfacing)

This is the line between a tool and a buddy. A tool waits for instructions. A buddy says "hey, I noticed something."

Triggers that should cause the system to surface information unprompted:

**Temporal triggers:**
- "Your open-source release milestone deadline is in 5 days."
- "A documentation audit was scheduled for this week."
- "You haven't committed to your active tooling repository in 8 days despite marking it as high-priority."

**Pattern triggers:**
- "Your step count has dropped below baseline for three consecutive days. The last time this happened, your subjective energy scores dropped sharply mid-week. Today is Tuesday."
- "You've spent 6 hours today on tool-building (pkm indexer, BLE skill, searchd optimisation) and 0 hours on the studio deliverables you listed as priorities (engine milestone, pipeline release)."

**Connection triggers:**
- "The sqlite-vec repo you bookmarked would replace the NumPy matrix multiplication in your search daemon — and might fix the 12-core burn problem, since sqlite-vec's C implementation doesn't spawn an ONNX thread pool."
- "The BLE proxy architecture in your repurpose-old-tech note overlaps with the Bermuda room detection project. Combining them would give you room-aware blind automation with hardware you already own."

**Honesty triggers (the hard ones):**
- "You've written 4 notes this week about meta-PKM architecture. You've written 0 notes advancing any of your actual projects. This matches a pattern your own vault documents: compulsive meta-tool building as a dopamine-seeking displacement activity."
- "The AI-native formats note proposes an architecture you'll never build. The Merkle DAG and CRDT sections describe a multi-year infrastructure project that competes with tools backed by full engineering teams (Notion, Obsidian, Logseq). Your comparative advantage is in the *content* of your vault, not its storage format."

That last category is uncomfortable but it's what separates a sycophantic assistant from a genuine thinking partner. A good buddy tells you when you're wasting time.

### 5. It Knows What It Doesn't Know (Belief Management)

The old note's trust decay table is actually good here, but it needs to be active rather than decorative:

**Confidence tracking:** When the system stores a fact, it records how it knows it. "Server uses ARM64 architecture" comes from a clinical specialist letter (confidence: 1.0). "Battery lasts 6 months" comes from an AI synthesis of a product page (confidence: 0.6). "Ava is an ESPHome-compatible Android BLE proxy app" came from a fast model hallucinating (confidence: turned out to be 0.0).

**Contradiction detection:** When new information conflicts with existing beliefs, flag it rather than silently overwriting. The old note identifies this ("AI can't tell 'researched a solution' from 'implemented it'") but doesn't propose a mechanism. The mechanism is simple: before writing a claim, search existing memory for conflicting claims. If found, present both to the human.

**Staleness decay:** Claims that haven't been verified or referenced in 6+ months get automatically flagged for review. "Is this still true? Should this be archived?"

---

## What Exists Today vs What Needs Building

| Component                    | Exists Today                                                                                   | Readiness                                                 |
| :--------------------------- | :--------------------------------------------------------------------------------------------- | :-------------------------------------------------------- |
| User profile document        | ChatGPT memory (crude), custom system prompts                                                  | Build as a markdown file, update with nightly agent       |
| Episodic conversation memory | [Mem0](https://github.com/mem0ai/mem0), [Letta](https://github.com/letta-ai/letta)/MemGPT, Zep | Mem0 is usable today; Letta is more ambitious but fragile |
| Background consolidation     | Nothing off-the-shelf does this well                                                           | Build with scheduled agent runs (cron + Gemini Flash)     |
| Proactive surfacing          | Apple/Google assistant reminders (crude)                                                       | Build with scheduled agent runs + trigger logic           |
| Belief management            | Nothing mainstream                                                                             | Build as a convention in the consolidation agent          |

The honest assessment: **phases 1 and 2 are buildable this week with your existing stack.** A nightly Gemini Flash agent that reads your daily log, updates a user profile, and writes a morning briefing is maybe 200 lines of Python plus a good prompt. The exotic stuff (fine-tuned personal models, CRDT sync, knowledge graphs) is interesting to think about but won't make your life better in the next month.

---

## Concrete Architecture for Your Stack

```
┌───────────────────────────────────────────────────────────┐
│  YOUR VAULT (markdown + git, unchanged)                   │
│  Daily logs, project notes, health data, work notes       │
└────────────────────────┬──────────────────────────────────┘
                         │
          ┌──────────────┼──────────────────┐
          ▼              ▼                  ▼
┌──────────────┐ ┌──────────────┐  ┌──────────────────────┐
│ pkm_index.db │ │ memory.md    │  │ profile.md           │
│ (sqlite-vec  │ │ (episodic    │  │ (living user profile │
│  + FTS5,     │ │  conversation│  │  updated nightly by  │
│  already     │ │  memory log, │  │  consolidation agent,│
│  exists)     │ │  append-only)│  │  human-editable)     │
└──────┬───────┘ └──────┬───────┘  └──────────┬───────────┘
       │                │                     │
       └────────────────┼─────────────────────┘
                        ▼
          ┌──────────────────────────┐
          │  CONTEXT ASSEMBLER       │
          │  Pulls from all 3 stores │
          │  + current daily log     │
          │  to build prompt context │
          └────────────┬─────────────┘
                       ▼
          ┌──────────────────────────┐
          │  CONVERSATION            │
          │  (Frontier model:        │
          │   Opus / Gemini Pro)     │
          └────────────┬─────────────┘
                       │
                       ▼ (after session)
          ┌──────────────────────────┐
          │  MEMORY EXTRACTION       │
          │  (Fast model:            │
          │   Flash / local 7B)      │
          │  Extracts decisions,     │
          │  facts, open questions   │
          │  → appends to memory.md  │
          └──────────────────────────┘

SCHEDULED AGENTS (cron / nightly):
  • Consolidation: daily log → digest + profile updates
  • Surfacing: scan for temporal/pattern/connection triggers
  • Integrity: contradiction detection, staleness flagging
```

The key insight of this architecture: **the vault doesn't change.** Markdown files in git, exactly as they are. No Merkle DAGs, no CRDTs, no typed schemas, no FUSE projections. What changes is what *reads* the vault and what *acts* on it.

Two new files get added:
- **`profile.md`**: living user profile, updated by agents, vetoed by human
- **`memory.md`**: append-only episodic log of AI interaction summaries

Three scheduled agents get added:
- **Nightly consolidation**: reads daily log → updates profile, writes digest
- **Morning surfacing**: scans for triggers → writes briefing to daily log
- **Post-session memory**: after each AI conversation → extracts key records to memory.md

Everything else is existing infrastructure: your search daemon for retrieval, git for versioning, Obsidian for the human interface.

---

## The Philosophical Bit

You said "like a buddy or a second brain, but linked to human so it benefits me." That last clause is the important one.

The risk with AI second brains is that they become a mirror rather than a lens. A mirror reflects what you already think. A lens helps you see what you couldn't see before. Most AI assistants today are mirrors — they're agreeable, they validate your framing, they generate text that sounds like your existing notes.

A genuine second brain would:
- **Challenge your frames**, not just execute within them. "You keep writing PKM architecture notes. Have you considered that the architecture is fine and the bottleneck is actually your willingness to use the system consistently rather than redesign it?"
- **Track your commitments** and hold you accountable. Not nagging, but honest status tracking. "You marked the security audit as a TODO three weeks ago. It's still open."
- **Distinguish between productive thinking and displacement activity.** Meta-tool building feels productive because it uses the same cognitive muscles as real work. But building a Merkle DAG knowledge format when you already have a working vault with 6,447 indexed notes is displacement, not progress.
- **Optimise for your wellbeing, not just your productivity.** Your vault contains extensive health data. The ideal system would notice correlations you're too close to see: "Every time you do 4+ hours of uninterrupted screen work, your physical tension spikes the next day. Movement and mobility sessions correlate with higher energy scores 48 hours later."

This is a higher bar than any current AI system meets. But the building blocks are all here: the data is in your vault, the retrieval works, the models are smart enough. What's missing is the orchestration — the scheduled agents, the trigger logic, the user profile that accumulates understanding over time.

Build the nightly consolidation agent first. Everything else follows from having good distilled memory.

## Related
- [[AI-native knowledge formats beyond markdown and git]] — the original storage-focused architecture note (good on dual-layer indexing and trust decay, over-engineered on everything else)
- [[2026-08-20 PKM workflow and architecture review]] — the three-pillar vault architecture (Git as truth, multi-vault privacy, readability)
- [[2026-08-19 agentic note taking learnings]] — early thinking on raw data vs structured notes
- [[2026-08-19 weekly notes overnote]] — manual consolidation that should be automated
- [[pkm metadata indexer]] — the existing sqlite indexer that forms the retrieval layer
- [[2026-08-18 empirical note generation experiments]] — what makes AI-generated notes actually valuable
- [[2026-08-27 AI - 7 Cognitive Sparring Lenses]]
- [[2026-08-27 biomimetic AI - stealing from brains, immune systems, and evolution]]
