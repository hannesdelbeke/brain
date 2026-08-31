---
name: attention-budget
description: Human attention budgeting for AI agents — cognitive load pricing, review pitching, queue caps, and distraction interception
created: 2026-08-31
aliases:
  - attention budget
  - cognitive budgeting
  - review queue optimization
  - attention span budgeting
tags:
  - skill
  - agent
  - productivity
  - workflow
---

Human attention is the strictly bounded resource in agentic workflows. While compute and token costs scale with budget, the human review queue has a single server with fixed bandwidth and finite daily cognitive energy.

Unbudgeted agents bankrupt this queue by outputting unbounded speculative notes and open-ended "decide whether" prompts. Attention budgeting forces agents to price, pitch, and cap their demands on human focus.

## Cognitive Cost Tiers

Every agent-generated decision or review item must carry an explicit cognitive cost tier:

- `🟢 10s Fast Gate`: Binary approval (Yes/No) or a pre-set default applied automatically if unreviewed. Zero open-ended deliberation.
- `🟡 1m Glance`: 1-paragraph summary with a single explicit recommendation and trade-off comparison.
- `🔴 5m Deep Dive`: Architectural, financial, or strategic pivot requiring full context load. Hard-capped at max 1–2 items per day.

## The Review Pitch Protocol

Agents must package review requests like high-leverage internal copywriters rather than dumping raw deliberation:

- **Hook**: 1-line summary explaining immediate value or why this decision unblocks work right now.
- **Decisive Recommendation**: Never ask "What should we do with X?". Propose the concrete path: "Adopt X because Y."
- **Zero-Cost Fallback (Default Action)**: State what happens if the human does nothing (e.g. "Default: Will proceed with Option A after 24h").
- **Cost Tag**: Prefix review requests with estimated time (e.g., `[Attention Cost: 30s]`).

## Queue Quotas & Automatic Pruning

- **Active Quota Cap**: Maintain a strict threshold on pending `**needs from you:**` items across the vault (e.g., max 3 active review items).
- **Auto-Default Pruning**: When the review queue reaches capacity, low-impact items are automatically committed with their recommended defaults rather than lingering in the queue.
- **Cold Staging**: Defer low-urgency speculative proposals to background archive drafts instead of pushing them into active daily digests.

## Distraction & Rabbit Hole Interception

When an exploratory or tangent research prompt arrives while core daily priorities or scheduled execution are pending:

- **Distraction Awareness**: Detect when an ad-hoc query represents a context-switching distraction loop vs a blocking dependency.
- **Async Park & Protect**: Intercept the rabbit hole by offering to delegate research entirely to an async background note, keeping human focus anchored on immediate execution.
- **Batch Delivery**: Consolidate non-urgent updates into a single periodic review digest rather than continuous interruptive pings.

## Related Skills
- [[public/skills/token-thrift/SKILL|token-thrift]] — token budgeting and cost-cutting heuristics
