---
date: 2026-08-19
tags:
  - technical
  - ai
  - tools
  - agentic
  - pkm
origin-sha: da71e78b4
---

# Tool Research: Herdr, Roo Code, Devstral, OpenClaw, Hermes Agent

Brief overview of five tools, what they solve, whether you can use them in your workflow, and links to related PKM notes.

---

## Herdr (`github.com/herdrdev/herdr`)
- What it is: A Rust terminal multiplexer built specifically for AI coding agents.
- What it solves: Unlike tmux or Zellij, Herdr is agent-aware. It tracks background CLI sessions (Claude Code, Codex, Aider) and shows their real-time state (working, idle, blocked on permission) in a sidebar.
- Could you use it: Yes. Especially when running multiple CLI agents simultaneously or driving sessions remotely from phone via SSH or CCGram.
- Related notes: [[phone as pc dock]], [[2026-02-15 phone to ai on pc]], [[2026-08-19 open source claude code mobile equivalents]].

---

## Roo Code (`github.com/roocodeinc/roo-code`)
- What it is: An open-source autonomous coding extension for VS Code and Cursor (fork/evolution of Roo Cline).
- What it solves: Gives an in-editor AI agent full filesystem and terminal access with custom modes (Architect, Code, Ask, Custom roles) and MCP server integration.
- Could you use it: Yes, inside VS Code / Cursor when you prefer an in-editor GUI sidebar over pure CLI terminals.
- Related notes: [[mcp server home assistant]], [[2026-01-20 opencode]], [[agentic note taking]].

---

## Devstral
- What it is: Mistral AI's family of open-weight models trained specifically for agentic software engineering (24B Small and 123B large).
- What it solves: Standard LLMs often write isolated functions; Devstral is trained to navigate repositories, edit multiple files, and solve real GitHub issues. The 24B version runs locally on an RTX GPU via Ollama.
- Could you use it: Yes. Good candidate for local/offline agent runs on your PC when API tokens run out or for privacy-sensitive work.
- Related notes: [[offline GPU embeddings with incremental cache]], [[2026-01-19 try CLI LLMs]], [[cheap AI]].

---

## Openclaw (`github.com/openclaw/openclaw`)
- What it is: A self-hosted personal AI assistant gateway bridging LLMs to messaging apps (Telegram, WhatsApp, Discord) with local tool use.
- What it solves: Turns chat apps into a remote control hub for your PC. It can run shell commands, manage files, and interact with GitHub from your phone.
- Could you use it: Yes, directly relates to your Telegram PKM bot and mobile control experiments, though security/permissions need careful sandboxing.
- Related notes: [[2026-08-18 pkm voice agent addon install]], [[agentic note taking on mobile]], [[2026-02-05 openclaw poor security]].

---

## Hermes Agent (nous Research, `github.com/NousResearch/hermes-agent`)
- What it is: A self-improving AI agent framework focused on long-term learning loops.
- What it solves: Most agents forget lessons between sessions. Hermes evaluates task outcomes, extracts reusable reasoning patterns, and saves them as markdown skill files so it gets faster and smarter over time.
- Could you use it: Yes. Highly relevant to your goal of letting AI learn from vault history and human feedback.
- Related notes: [[algo to differentiate between AI and human notes]], [[2026-07-31 historic obsidian links]], [[agentic note taking]].

---

## Openhands (`github.com/all-hands-ai/openhands`, Formerly Opendevin)
- What it is: A fully open-source autonomous software engineering platform running in Docker containers with web UI, terminal, and browser control.
- What it solves: Full-scale autonomous execution across entire codebases, repository issues, and cloud/browser tasks without manual intervention on every step.
- Community reality check (r/LocalLLaMA):
  - Setup friction: Requires Docker and sandboxed environment configuration.
  - Model dependency: High failure rates when run on small local LLMs (agentic loops require massive reasoning/context). Performs best with Claude or specialized models like Devstral / Qwen2.5-Coder.
  - Token heavy: Autonomous self-healing loops consume large amounts of context quickly.
- Could you use it: Yes, as a self-hosted cloud or containerized agent server to fire-and-forget background tasks from web/mobile, paired with Devstral or Claude.
- Related notes: [[2026-08-19 open source claude code mobile equivalents]], [[cheap AI]], [[agentic note taking]].

---

## Gptme
www.github.com/ErikBjare/gptme
- What it is: A lightweight, terminal-native personal AI agent designed to execute shell commands, run Python code, edit local files, and browse the web directly in your CLI.
- What it solves: Gives an agent direct execution access inside terminals, tmux panes, and SSH sessions without bloated UI or heavy Docker setups. Supports local LLMs (`llama.cpp`) alongside cloud providers (OpenAI, Anthropic, Gemini, OpenRouter).
- Could you use it: Yes. It is an excellent lightweight CLI companion for terminal-driven workflows, headless scripts, and phone-over-SSH control ([[2026-02-15 phone to ai on pc]]).
- Related notes: [[2026-01-19 try CLI LLMs]], [[agentic note taking]].

---

## Summary Matrix

- Herdr: Terminal multiplexer with agent state tracking. Solves multi-agent terminal clutter.
- Devstral: Mistral's open coding model (24B/123B). Solves offline/local agent execution.
- OpenClaw: Self-hosted messaging-to-PC agent bridge. Solves remote mobile chat.
- Hermes Agent: Self-improving agent saving markdown skills. Solves persistent learning from feedback.
	- [[how does hermes self improve]]
- OpenHands: Docker-sandboxed autonomous engineering platform. Solves async whole-repo tasks.
- gptme: terminal for agents. SSH allows remote access.

skip for now
- Roo Code: VS Code agent

---

## References
