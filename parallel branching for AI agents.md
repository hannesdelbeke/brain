---
aliases:
  - parallel branching for AI agents
  - Schrodingers agent
  - speculative branch exploration
tags:
  - ai
  - git
  - philosophy
  - agentic
  - architecture
  - technical
---

> [!prompt]-
> if i want to let agent grow
> i might say, create lots of branches and try every approahc you can thiink of
> in the end i will pick 1 branch with a solution i like, or maybe compare multipe branches simply for research, or perhaps i just like to push the limits of an agent.
> 
> this reminds me of how schrodingers cat is dead or alive
> and that creates a paralel universe
> every choice creates a branch
> 
> [[philosophy]]

Linear agent execution forces an AI to commit to a single solution path early, often getting trapped in local minima or confirmation bias. Parallel branching applies the quantum Many-Worlds metaphor to software development: spawning isolated Git branches where competing technical hypotheses evolve simultaneously until a human or evaluator collapses them into one truth.

## The Quantum Metaphor: Schrödinger's Agent

In quantum mechanics, unobserved superpositions hold multiple contradictory states simultaneously (Schrödinger's cat is both dead and alive). Everett's Many-Worlds interpretation posits that every measurement splits reality into branching parallel universes.

In agentic problem solving:
- A single prompt creates a branching tree of alternative implementations.
- Universe A tries a pure functional approach; Universe B tries an object-oriented architecture; Universe C deletes code to simplify.
- Until evaluation, all solutions coexist in isolated Git branches without polluting master.
- **Wave function collapse:** The human reviews the diffs, benchmarks performance, and merges the winning branch while discarding dead ends.

## Practical Architecture

### 1. Isolated Git Worktrees
Running concurrent agents against a single working tree causes file lock collisions and race conditions. each agent must operate in an isolated worktree:
```bash
git worktree add -b experiment/vector-cache ../worktree-vector
git worktree add -b experiment/flat-json ../worktree-json
```

### 2. Autonomous Divergence
Instruct each subagent to explore a distinct constraint or philosophy:
- **Branch A (Speed):** Maximize throughput using low-level C bindings / GPU acceleration.
- **Branch B (Simplicity):** Zero external dependencies, pure standard library implementation.
- **Branch C (Robustness):** Heavy validation, strict typing, and comprehensive property testing.

### 3. Objective Benchmarking & Pruning
Each branch runs an automated self-test or benchmark suite:
- Failing branches or bloated implementations are pruned with zero cleanup cost (`git worktree remove`).
- Winning ideas can be merged directly or synthesized into a hybrid solution.

## Why This Accelerates Agent Growth

- **Escapes prompt anchoring:** Agents often cling to their first generated idea. Parallel branching guarantees orthogonal exploration.
- **Pushes capability limits:** Stress-tests how far an LLM can innovate when unconstrained by backward compatibility or fear of breaking master.
- **High-signal comparison:** It is much easier for a human to compare three concrete working prototypes than to imagine the trade-offs in abstract chat.

## See also
- [[how hermes agent self improves]] — genetic evolution (GEPA) and iterative skill optimization
- [[4 levels of AI]] — progression from reactive assistants to autonomous parallel explorers
