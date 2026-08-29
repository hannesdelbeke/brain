---
aliases:
- live hook into Obsidian for AI agents
- Obsidian DOM bridge for AI
- Obsidian live hook for AI agents
created: 2026-08-29
energy: 5
tags:
- technical
- obsidian
- ai
- architecture
---

## What is a live AI session hook

A live hook connects an external AI session directly to a running Obsidian instance. Instead of only reading static `.md` files from disk, the agent connects over a local socket (WebSocket, MCP, or IPC) to inspect the live DOM, read computed CSS, evaluate JavaScript, and listen to editor events in real time.

## Core capabilities enabled

### Rendered HTML inspection
Reading the rendered DOM rather than raw markdown.
- Inspect rendered visual elements like Mermaid diagrams, Dataview tables, MathJax formulas, and custom callouts.
- Verify that CSS styling and HTML layouts render correctly after generating content.

### Computed CSS and theme debugging
Querying computed CSS styles and theme variables (`--background-primary`, `--text-normal`).
- Detect layout shifts, contrast bugs, and broken styling from conflicting snippets or plugins.
- Test CSS tweaks live in the renderer without reloading Obsidian.

### Real-time cursor and selection context
Listening to active leaf change and editor selection events.
- An agent knows the exact note, heading, or paragraph you are focused on when you ask *"explain this section"* or *"clean up this list"*.
- Eliminates manual path copy-pasting.

### Dynamic JavaScript execution (`eval`)
Running arbitrary JavaScript in the Obsidian renderer process.
- Access `app.workspace`, `app.metadataCache`, and plugin APIs directly.
- Execute commands via `app.commands.executeCommandById(...)` or trigger modal dialogs.

## Implementation mechanisms

### 1. Local MCP server inside Obsidian
An Obsidian plugin acts as a Model Context Protocol (MCP) server over WebSocket or SSE on `localhost`.
- Exposes tools like `execute_js`, `get_active_dom`, `get_computed_css`, and `read_rendered_html` directly to AI tools (Antigravity, Claude Code, Cursor).
- Cleanest architecture for agent tool-use.

### 2. Local WebSocket and REST API
A plugin running an HTTP/WebSocket server inside Obsidian (e.g. `obsidian-local-rest-api`).
- Emits event streams for note changes, active leaves, and selection ranges.
- Allows external scripts to POST JS execution payloads or fetch file states.

### 3. Native Obsidian CLI IPC (`obsidian eval`)
Obsidian v1.12+ includes official CLI IPC support. See [[Obsidian CLI + Agent Context at Scale]].
- Running `obsidian eval "..."` executes JavaScript against the running instance and returns JSON output.
- Zero extra plugin dependencies, though limited to request-response rather than continuous event streaming.

### 4. Chrome DevTools Protocol (CDP)
Launching Obsidian with `--remote-debugging-port=9222`.
- Gives external tools raw DevTools protocol access to inspect DOM trees, capture screenshots, and evaluate scripts directly in the Chromium runtime.

## Existing plugins and tools

- [obsidian-local-rest-api](https://github.com/coddingtonbear/obsidian-local-rest-api): standard REST and WebSocket bridge for vault operations and command execution.
- [obsidian-mcp-connector](https://github.com/istefox/obsidian-mcp-connector) and [obsidian-devtools-mcp](https://github.com/jjjjguevara/obsidian-devtools-mcp): in-app MCP servers that expose `obsidian_execute_js` and vault tools to MCP-compatible AI clients.
- [obsidian-runjs](https://github.com/eoureo/obsidian-runjs) and [obsidian-js-engine-plugin](https://github.com/mProjectsCode/obsidian-js-engine-plugin): internal execution of arbitrary JavaScript modules and DOM manipulation.
- [Obsidian CLI](https://obsidian.md/cli): official command-line IPC tool for running `obsidian eval`.

## Related notes
- [[Obsidian data worth exposing to AI agents]] — high-value in-memory metadata and telemetry to expose
- [[Obsidian CLI + Agent Context at Scale]] — official CLI IPC vs file-based retrieval
- [[ai optimize obsidian plugins]] — automating plugin configuration and startup optimizations
- [[2026-08-29 Startup Metrics Logger devlog]] — devlog for programmatic metric extraction
