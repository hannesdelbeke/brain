---
date: 2026-08-28
created: 2026-08-28
tags:
  - ai
  - agents
  - prompt-engineering
  - architecture
  - skills
  - pkm
aliases:
  - 2026-08-28 agent instruction bloat - modular skills and compact synthesis
  - modular agent instruction synthesis
---

# Agent Instruction Bloat: Modular Skill Registries, Prompt Synthesis, and Incremental Distillation

Why monolithic agent instruction files (`AGENTS.md`, `CLAUDE.md`, `.cursorrules`) fail at human scale, how to treat instructions as modular code modules selected via JSON/YAML manifests, and how to incrementally synthesize and distill lean prompts without unbounded token bloat.

Related: [[AGENTS.md]], [[Claude Code]], [[Cursor - The AI Code Editor]], [[2026-08-27 fearless note consolidation - using git history as the deep memory layer|fearless note consolidation]], [[2026-08-27 biomimetic AI - stealing from brains, immune systems, and evolution|biomimetic AI]], [[single source of truth]], [[token efficient PKM analysis architecture]]

---

## 🚫 The Monolithic Trap: Why Human-Managed Instruction Files Rot

As coding agents become standard in everyday developer workflows, the root instruction file (commonly `AGENTS.md`, `CLAUDE.md`, or `.cursorrules`) inevitably becomes an unmaintainable dumping ground:

```
┌─────────────────────────────────────────────────────────────┐
│                    THE MONOLITHIC TRAP                      │
│                                                             │
│  Developer A adds Docker quirks  ──┐                        │
│  Developer B adds React tips     ──┼──► AGENTS.md           │
│  Agent failure patch appended    ───┤    (Bloated, 800+ lines│
│  CI/CD formatting instructions   ──┘     Contradictory)     │
│                                            │                │
│                                            ▼                │
│                              Attention Dilution & Latency   │
│                              Lost-in-the-Middle Failures    │
│                              High Token Tax per Message     │
└─────────────────────────────────────────────────────────────┘
```

### 1. The Human Maintenance Bottlenecks
* **Append-Only Graveyard**: When an agent fails a task, the human instinct is to append a new negative constraint (e.g., *"Never use tool X with flag Y"*). Rules are never pruned, refactored, or audited.
* **Semantic Rot and Contradictions**: Early guidelines clash with newer decisions (e.g., `"Use Jest"` at line 40 vs `"Use Vitest for all new tests"` at line 310).
* **PR Review Friction**: Pull requests touching a single massive prompt file turn into messy subjective discussions with no modular ownership or schema validation.

### 2. Model Performance Degradation
* **Instruction Budget Exhaustion**: Frontier LLMs follow instructions reliably up to a budget threshold (typically ~100–150 dense directives). Beyond that, adherence degrades non-linearly.
* **Lost in the Middle**: Critical safety rules or architectural invariants buried in the middle of a 1,000-line markdown file get overlooked during attention scoring.
* **Compounding Token Tax**: Loading a bloated multi-thousand token instruction file on every single turn burns context capacity and inflates latency and API costs.

---

## 💡 The Core Proposal: Modular Registries, Selective Manifests & Compact Synthesis

Instead of managing `AGENTS.md` directly as a monolithic source of truth, **treat it as a compiled build artifact**:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        DECOUPLED PROMPT PIPELINE                            │
│                                                                             │
│  [skills-registry/]                                                         │
│   ├── git-workflow.json                                                     │
│   ├── testing-vitest.json                                                   │
│   └── secure-storage.json                                                   │
│          │                                                                  │
│          ▼                                                                  │
│  [manifest.json] ──► [Synthesizer / Optimizer] ──► [AGENTS.md (Compiled)]   │
│  (Active Profile)            ▲                        (< 120 lines)         │
│                              │                                              │
│  [New Feedback / Skill] ─────┘ (Incremental Distillation & Merging)         │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Key Components

1. **Atomic Skill / Rule Modules (Source of Truth)**:
   Discrete instructions, domain conventions, and tool recipes live as individual JSON, YAML, or scoped Markdown files (e.g. `skills/testing-vitest.json` or `.rules/docker.json`).
2. **Selective Manifest (`manifest.json`)**:
   Projects or workspaces declare exactly which skills are active for their domain (e.g., `["core-standards", "typescript-strict", "testing-vitest"]`).
3. **Synthesis & Compaction Engine**:
   A lightweight compiler (script or LLM pass) merges selected modules into a tight, cohesive `AGENTS.md` strictly constrained to a line budget (e.g., `< 100-120 lines`). Redundancies are merged, conflicting constraints resolved, and text distilled into imperative bullet points.
4. **Incremental Distillation ("Learn on Top")**:
   When an extra skill, lesson, or edge-case fix is discovered:
   * It is evaluated against the existing skill registry.
   * It is merged into the corresponding modular skill file (or created as a discrete new skill module).
   * The synthesizer recompiles the lean `AGENTS.md` on top of the old state without unbounded linear expansion.

---

## 🔍 Existing Solutions & Prior Art

Industry and research have developed complementary patterns across modular rules, prompt compilation, and compression:

### 1. Scoped & Modular Rule Registries
* **Cursor Rules 2.0 (`.cursor/rules/*.mdc`)**: Replaced monolithic `.cursorrules` with modular rule files triggered conditionally via glob patterns (e.g., `src/api/**/*.ts`). Context is injected only when relevant files are edited.
* **Anthropic Tool & Skill Registries (`.claude/skills/` / Antigravity Skills)**: Self-contained skill directories (`SKILL.md` + scripts + references) discovered and loaded dynamically on-demand rather than polluting the root system prompt.
* **Repomix / Pack**: Context bundling tools allowing declarative JSON/YAML configs to selectively pack repository context into standardized LLM inputs.

### 2. Prompt Compilers & Programmatic Optimization
* **DSPy (Stanford NLP)**: Replaces fragile hand-written prompt strings with declarative modules and teleprompters/optimizers (e.g., **MIPROv2**, **BootstrapFewShot**). Compiles, tests, and optimizes prompt instructions mathematically against evaluation metrics.
* **Prompt Poet (Character.ai)**: Dynamic templating engine that packs and truncates prompt elements in real time based on token budgets and priority hierarchies.
* **Promptfoo**: Test-driven assertions, regression suites, and evaluation matrices to verify that new prompt modifications do not degrade existing model behavior.

### 3. Prompt Compression & Token Pruning
* **LLMLingua / LongLLMLingua (Microsoft Research)**: Small language models (GPT-2, Phi-3) compute token perplexities to prune non-essential words, achieving 5×–20× compression while preserving semantic meaning.
* **TextGrad / OPRO**: Frameworks utilizing LLM feedback gradients to iteratively rewrite prompt text into dense, optimal phrasing.

### 4. Continual Learning & Skill Memory
* **Voyager / Reflexion**: Agents maintain an external, vector-searchable "Skill Library" of verified code and recipes learned from past failures, dynamically retrieved when needed.
* **MemGPT / Letta**: Employs two-tier memory architecture (Core Memory vs. Archival Memory), continually synthesizing new learnings into compact memory slots.

---

## 🛠️ Reference Implementation Blueprint

### 1. Atomic Skill Module (`skills/testing-vitest.json`)
```json
{
  "id": "testing-vitest",
  "domain": "testing",
  "priority": "high",
  "rules": [
    "Use Vitest for all unit tests. Mock external network calls with msw.",
    "Colocate tests next to source files using *.spec.ts suffix.",
    "Run tests with `pnpm test:unit` before completing tasks."
  ],
  "anti_patterns": [
    "Do not use Jest globals (import describe/test from 'vitest')."
  ]
}
```

### 2. Workspace Manifest (`agent-manifest.json`)
```json
{
  "project": "web-platform",
  "target_line_budget": 100,
  "active_skills": [
    "core-standards",
    "typescript-strict",
    "testing-vitest",
    "git-conventions"
  ]
}
```

### 3. Incremental Learning Flow

```
                      ┌─────────────────────────┐
                      │   New Rule / Lesson     │
                      └────────────┬────────────┘
                                   │
                                   ▼
                      ┌─────────────────────────┐
                      │  LLM Diff & Classifier  │
                      └────────────┬────────────┘
                                   │
                 ┌─────────────────┴─────────────────┐
                 ▼                                   ▼
        [Existing Skill Match]              [New Domain Module]
       Merge & Deduplicate Rule             Create new *.json skill
                 │                                   │
                 └─────────────────┬─────────────────┘
                                   │
                                   ▼
                      ┌─────────────────────────┐
                      │   Synthesizer Engine    │
                      │ (Compacts & Deduplicates)│
                      └────────────┬────────────┘
                                   │
                                   ▼
                        [Compiled AGENTS.md]
                        - Strict Line Budget (<100)
                        - Primacy/Recency Layout
```

### 4. Synthesizer Compaction Prompt
```markdown
You are a Prompt Compactor and System Architect.
Given a set of input skill modules and a strict budget of 100 lines:
1. Merge redundant instructions across modules.
2. Resolve contradictory rules (prefer newer and more specific directives).
3. Structure output:
   - Primacy Zone: Critical safety invariants and non-negotiables.
   - Core Commands: Build, test, and lint commands.
   - Specific Guidelines: Bulleted imperative directives.
4. Output ONLY the compiled, production-ready AGENTS.md markdown.
```

---

## 📊 Summary Comparison

| Dimension | Monolithic `AGENTS.md` | Modular Compiled `AGENTS.md` |
| :--- | :--- | :--- |
| **Source of Truth** | Giant, human-edited markdown | Discrete JSON/YAML skill modules |
| **Incremental Updates** | Blind appending (linear growth) | Semantic merge & synthesis (fixed budget) |
| **Token Overhead** | 2,000–5,000 tokens / message | 300–600 tokens / message |
| **Conflict Handling** | Contradictions accumulate quietly | Resolved automatically at synthesis |
| **Code Review / Git** | Merge conflicts on one huge file | Clean, scoped PRs per skill module |

---

## 🔗 Related Notes
- [[2026-08-31 research on compressing llm reasoning and notes without losing information]] — the research backing this: llmlingua-2's "classify essential tokens, cut the rest" is the same move this note applies to instruction files
- [[AGENTS.md]] — vault agent instructions and conventions
- [[2026-08-27 fearless note consolidation - using git history as the deep memory layer|fearless note consolidation]] — treating active notes as lean neocortex and Git as hippocampal tape
- [[2026-08-27 biomimetic AI - stealing from brains, immune systems, and evolution|biomimetic AI]] — lossy compression, synaptic pruning, and sleep consolidation
- [[token efficient PKM analysis architecture]] — optimizing token budgets across agent operations
- [[single source of truth]] — maintaining atomic records of truth across repositories