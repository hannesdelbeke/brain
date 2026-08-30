---
tags:
  - ai
  - git
  - github
  - architecture
  - agents
  - automation
  - cli
  - pkm
---
The infrastructure layer under [[proposal - self-learning agent supervisor and continuous prompt failure distillation|the self-learning supervisor proposal]]: where an agent is allowed to look (multi-repo search), whose name its commits carry (attribution), and what record exists that a work session happened at all (autocommit, coding diary). The supervisor proposal assumes all three already work and builds a correction-learning loop on top; this note is the part underneath that nothing has proposed yet.

## 1. Multi-repo search and sandboxing

[[simple options for multi-repo agent search]] and [[single-repo vs multi-repo agent search]] already name the three gaps (CWD sandboxing, no org catalog, no map-reduce across repos) and a zero-server MVP: a weekly `org-map.md` catalog plus `gh search code` plus a local loop script. Nothing to add to that design; what's new from a 2026 tool scan:

- **Zoekt** (Apache-2.0) — sub-50ms search across multi-GB, multi-repo corpora, CLI + indexserver, self-hosted, no cloud or embeddings API. Fits the "zero ongoing server maintenance" MVP better than Sourcegraph, whose self-hosted tier has effectively been discontinued in favor of a $49+/user/month cloud product agents can't call programmatically anyway (it's browser-only).
- **WarpGrep, CodeGraph, GitNexus** — MCP-native, agent-callable search/knowledge-graph servers, local-first (no code egress). Same category as this vault's own `.codegraph/` setup, just aimed at multi-repo rather than single-repo.
- **`gh search code` / grep.app** — zero-setup, already-available fallback for anything public or already covered by `gh` auth; matches Gap 1 Option B in [[simple options for multi-repo agent search]] exactly, no build needed.

Recommendation: keep the MVP as scoped (catalog + `gh` CLI + loop script), add Zoekt only if/when repo count makes `gh search code` too slow — that's the upgrade path, not a day-one dependency.

## 2. Git attribution and autocommit

[[autocommit leftover changes]] is a working protocol (presume human authorship, commit under the human's identity, `Co-Authored-By` trailer for the active model, push before AI passes begin). [[rewrite git history for ai authorship migration]] is the one-off backfill for history predating that protocol, using `git-filter-repo`. Both already reference the collision risk in `github co-author email collision with third-party accounts` and the `commit-msg` hook the supervisor proposal's step 1 calls for.

2026 tool-scan findings:
- GitHub's own bot convention is `<id>+github-actions[bot]@users.noreply.github.com` — namespaced, collision-proof by construction. The vault's own hook plan (reject any `Co-Authored-By` outside `users.noreply.github.com`) is exactly this pattern generalized; nothing to redesign, just confirmation it matches prevailing practice.
- `git-filter-repo` remains the correct tool for the one-off history rewrite; no newer tool has displaced it for commit-splitting/history-rewriting at this scale.
- Emerging alternatives to overloading `Co-Authored-By`: an `AI-assistant:` trailer (tool + model in one field), and a tiered `Assisted-by` / `Co-authored-by` / `Generated-by` scheme paired with human `Signed-off-by`. Neither is standardized yet; not worth adopting ahead of tooling support, but worth knowing the current `Co-Authored-By` overload is a recognized-elsewhere problem, not a local one.
- Counter-position worth knowing: the `no-ai-coauthors` movement argues bot co-authorship dilutes human accountability. Doesn't change this vault's protocol (attribution here is for provenance/blame, not credit), but explains why some orgs strip the trailer entirely.

Recommendation: no change to the autocommit protocol; write the `commit-msg` hook the supervisor proposal already scoped as step 1, restricting `Co-Authored-By` addresses to `users.noreply.github.com`. That hook is this section's only concrete deliverable, and the supervisor proposal shouldn't re-derive it.

## 3. Coding diary / session tracking

[[auto track coding dairy|auto track coding dairy]] wants a terminal-history-derived daily log of what was worked on, filtered of noise (`ls`), with a summary pass on top. The supervisor proposal's stage 1 ingest already reads Claude Code transcripts (`~/.claude/projects/`) and git history for the correction-detection pipeline — that's most of this for free, since a transcript already carries every tool call in order.

Recommendation: don't build a second logger. Point the coding-diary idea at that same ingest stage; the gap it doesn't cover is bare shell commands run outside any agent session, which would need a thin `history`-based capture (a cron reading `~/.bash_history` timestamps) feeding the same SQLite the supervisor proposal already designs, rather than a parallel note-generation pipeline.

## Adjacent but not merged in

[[how to give LLM control my Android]] and [[HA AI connection goal]] both describe an agent needing standing access beyond its default sandbox — a device control channel (ADB/scrcpy) and a persistent MCP connection (Home Assistant), respectively. That's the same shape as Gap 1 above (CWD sandboxing), just for a device and a service instead of a repo. Not folded into this proposal because the fix in each case is local setup (ADB pairing, MCP auto-connect script), not shared tooling — flagged here so the "agent needs a bigger sandbox" pattern isn't rediscovered as new each time it shows up.

## Related
- [[proposal - self-learning agent supervisor and continuous prompt failure distillation]] — sibling proposal; that one is the learning loop, this one is the substrate it runs on
- [[simple options for multi-repo agent search]]
- [[single-repo vs multi-repo agent search]]
- [[autocommit leftover changes]]
- [[rewrite git history for ai authorship migration]]
- [[auto track coding dairy]]
- [[how to give LLM control my Android]]
- [[HA AI connection goal]]
