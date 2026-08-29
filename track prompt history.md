---
tags:
  - ai
  - git
  - pkm
---
How to preserve user prompt history and intent when using AI agents without cluttering note contents.

Related: [[AGENTS.md]], [[public/github co-authors for AI|github co-authors for AI]], [[public/2026-08-28 agent instruction bloat - modular skills and compact synthesis|agent instruction bloat - modular skills and compact synthesis]], [[public/git author|git author]], [[public/autocommit leftover changes|autocommit leftover changes]]

---

## 1. The Prompt Retention Problem
When querying AI agents via CLI, IDEs, or automated bots, the generated content is committed into the vault, but the original human prompt is often lost. Human prompts carry the highest signal: the core user intent, specific operational constraints, and edge cases.

---

## 2. Commit Message Metadata Protocol (Standard)

Store the user prompt directly in the Git commit message body, combined with the human `Co-Authored-By:` trailer:

```git
docs: add solid black background configuration to setup log

Prompt: "set background to dark grey"

Co-Authored-By: Hannes Delbeke <3758308+hannesdelbeke@users.noreply.github.com>
```

### Advantages
- **Zero Note Clutter:** Markdown notes remain clean, atomic, and readable in Obsidian without synthetic prompt headers.
- **Git Grep Searchable:** Retrieve original intent with `git log --grep="Prompt:"`.
- **Accurate Provenance:** Distinguishes between direct agent author and human prompter.

---

## 3. Public vs. Private Sanitization Pass (Leak Prevention)

Because human prompts often include private thoughts, employer project names, or sensitive context, agents enforce a strict sanitization boundary:

1. **Private Repositories / Vault Root:**
   - Prompts are recorded verbatim in the commit body (`Prompt: "..."`).
2. **Public Repositories / `public/` Submodule:**
   - **Sanitization Pass:** Strip out personal identifying data (PII), health metrics, employer specifics, and tokens.
   - **Safe Abstract:** If a prompt cannot be generalized safely, omit the `Prompt:` line completely and use a standard descriptive commit message.

---

## 4. Cross-Vault Portability & Instruction Synthesis

Other vaults and projects can replicate these instructions by compiling them into their local agent instructions (`AGENTS.md` / `CLAUDE.md`) using modular skill synthesis per [[public/2026-08-28 agent instruction bloat - modular skills and compact synthesis|modular skills and compact synthesis]]:

```markdown
- commit AI changes with AI git author (e.g. `Antigravity`, `Claude`). When prompted/guided by human, append human as co-author: `Co-Authored-By: <Name> <<email>>`. Track source intent in commit body: `Prompt: "<prompt>"`.
- public notes prompt sanitization: When committing to public repos, sanitize prompt to strip private data, employer specifics, and tokens. If unsafe to sanitize, omit prompt line.
```

---

## 5. Alternative Approaches

* **Callout Blocks:** Placing prompts in collapsible callout quotes above responses per [[agent answers in callout]]. Best for short Q&A.
* **External Prompt Log:** Storing raw session transcripts and prompt history in JSONL format.

### Related
- [[note utility and synapse strength from session recaps]] — using prompt and commit history to evaluate note usefulness
- [[algo to differentiate between AI and human notes]] — Separating human prompt lines from generated responses.
- [[human vs ai text context]] — Maintaining context between human intent and AI generation.
