---
date: 2026-08-19
tags:
  - technical
  - ai
  - agentic
  - architecture
origin-sha: 1f7d513b8
created: 2026-08-19
---


[[Hermes Agent]] (by Nous Research) self-improves through an automated closed-loop learning architecture without model retraining.

---

## The Core Learning Loop

Instead of staying stateless between sessions, Hermes follows a 4-step cycle:

1. **Task Execution:** Breaks down a user request and uses tools (shell, files, APIs).
2. **Outcome Evaluation:** Assesses whether the goal succeeded using user feedback and tool return codes.
3. **Skill Codification:** Distills the successful reasoning steps into a reusable markdown skill file (`SKILL.md`).
4. **Skill Refinement:** Iteratively updates existing skills when it encounters edge cases or better approaches.

---

## Three-tier Persistent Memory

- `USER.md`: Tracks user preferences, working habits, and styling rules.
- `MEMORY.md`: Long-term environmental facts (repo quirks, paths, project setups).
- `skills/`: Directory of modular procedural recipes that the agent dynamically loads when relevant tasks appear.

1 md file, it seems a bit dumb compared to a PKM

---

## Automated Evolution (dspy & GEPA)

Nous Research also uses a companion system (**Hermes Self-Evolution**) that optimizes the agent's prompts and tools:

- **DSPy Integration:** Treats prompt engineering as code optimization.
- **Genetic-Pareto Evolution (GEPA):** Automatically mutates tool descriptions, prompt instructions, and skill templates to find the highest-performing configurations based on benchmark scores.
	- [[learning]]
	- [[evolution]]

---

## References
- [[agentic note taking]]
