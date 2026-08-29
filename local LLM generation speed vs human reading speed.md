---
tags:
- ai
- local-llm
- performance
- workflow
- hardware
aliases:
- offline ai workflows
- local llm generation speed vs human reading speed
- 3B vs 7B local speed threshold
---

Why offline local LLMs on laptop hardware remain practical when calibrated against human reading speed thresholds, and workflow tactics for disconnected environments.

Related: [[lightweight self-questioning models vs monolithic single-shot models]], [[popular AI models landscape]], [[how local AI models search the web and stay up to date]], [[Linux for AI and developer workflows]]

## The human reading speed threshold

When evaluating local LLM performance on laptop CPUs without dedicated discrete GPUs, raw token throughput is best measured against human cognitive reading speed:

- **Human reading speed:** The average adult reads at 200–300 words per minute, equivalent to roughly **5–8 words per second (~7–10 tokens per second)**.
- **7B models on laptop CPU (7–10 tok/sec):** Generation roughly matches reading speed. Usable for reading along as tokens stream, but causes noticeable delays on multi-paragraph answers.
- **3B models on laptop CPU (25–35 tok/sec):** Generates 3x to 4x faster than human reading speed. Output feels immediate and interactive for terminal queries.
- **Cloud models (150–250+ tok/sec):** Blazing fast bulk throughput, but drops to **0 tok/sec** whenever disconnected from the network.

## Offline workflow tactics

To maintain a fast workflow when working disconnected (e.g. on a train or flight):

- **Model sizing by interaction mode:** Use 3B models (`llama3.2:3b`, `qwen2.5:3b`) for interactive tasks like shell commands, regex, git syntax, and code explanations. Reserve 7B/8B models for deeper background synthesis.
- **Focused snippet injection:** Ingesting large files on CPU takes noticeable pre-fill time before generation begins. Pipe tight snippets (`git diff` or specific functions) rather than full repository trees.
- **Deterministic local search first:** Use `ripgrep` or local SQLite FTS5 indexes to locate exact lines in sub-milliseconds, feeding only the relevant lines to the LLM.
- **Background asynchronous jobs:** When dispatching larger refactors or multi-note reviews to a 7B model, run the process in a background terminal or split pane (`tmux`), letting it write to a file while you continue active writing.
