---
date: 2026-08-28
created: 2026-08-28
tags:
  - ai
  - agents
  - architecture
  - self-learning
  - prompt-engineering
  - pkm
  - skills
aliases:
  - self learning agent supervisor
  - prompt failure distillation
---
Relies on knowledge [[provenance]] and accurate [[git author]] attribution (including [[github co-authors for AI|AI co-authors]] and [[autocommit leftover changes|human autocommits]]). Tracking prompt intent connects to [[track prompt history]] and [[human vs AI git history transfers between notes]].

A supervisor that reads agent session transcripts and git history, finds the turns where a human had to correct the agent, clusters the recurring ones, and writes the result back as guards and rules instead of leaving it in chat logs.


The name is bigger than the machine. What it automates is distilling corrections a human already made, not noticing failures nobody caught, and the thing it should emit is a hook rather than a paragraph.

**Status, 2026-08-28: nothing built, this is a design.** The ingest half of it exists as [[cross-agent session indexing architecture]], which indexes Claude Code transcripts today and has no Antigravity or Codex adapter. Everything downstream of ingest, the correction detector, the clustering and the rule writer, is unwritten. The numbers below are targets, not measurements.

> *Every prompt is a call to action: write new idea, fix an issue, make a thing. We now have some kind of session tracker or reader. Also relates to tracking prompt history and the automated daily logger. Go through all prompts on this machine, and identify what went wrong. Check the summary if there is one for the session (I know Claude has a recap, unsure if AGY does), then see if the prompt was resolved: what work or note it created, and then in future what issues it caused, or mistakes it made, or things it missed. Then link it to skills we extracted from this. How would this work? Would we store data, store SQL only, links only? Git history and session will be main source of truth (session data distributed across development hardware). End goal: by identifying where we went wrong and where we introduced bugs or shortcomings, we can come up with a system that can be self-learning—an external thing that watches our process day to day, and identifies issues. Nearly every prompt is me spotting an issue and asking AI to fix it. There might be patterns in things AI often breaks. I'd like you to find those patterns, and for that we might need a system.*

> [!todo] next
> **next:** write the four `.githooks` guards for the archetypes already known, starting with `commit-msg` rejecting any `Co-Authored-By` address outside `users.noreply.github.com`, then run the git-only correction walk over a month of repositories and count the pairs
> **blocked:** nothing for steps 1 and 2, a human has to pick which repositories the walk covers before step 3 has a number worth reading

## in short

- the deliverable of learning is a guard, a git hook or a threshold check, not a paragraph in `AGENTS.md` that an agent may or may not read
- the pipeline of ingest, detection and clustering exists to rank which guard to write next, and nothing else
- git alone carries the strongest signal and already syncs across every machine, so the first version needs no transcripts, no index and no daemon
- what decides whether the full system is worth building is a count of repeated failures, obtainable in an afternoon
- the corpus can only ever hold failures a human noticed and corrected, so this distils corrections rather than discovering them

## plan, in priority order

1. **Write the known guards by hand.** Four archetypes are already named and need no pipeline to justify. Start with the `commit-msg` hook for co-author trailers, then a link checker, then a deletion threshold on journal notes, then a polling-loop check. Pays off immediately whether or not anything below gets built. *Blocked: nothing.*
2. **Build the git-only correction walk.** One script over a repository log emitting pairs where a human commit rewrites lines an agent commit added within a day. No index, no schema, no transcripts. *Blocked: nothing.*
3. **Count and decide.** Read fifty pairs by hand, count repeats per failure kind. Repetition means build stage 3, no repetition means stop here and keep writing hooks by hand. *Blocked: a human picks the repositories to walk.*
4. **Add the transcript detector, if step 3 says yes.** Claude Code transcripts only, reusing the existing index, correlating correction prompts with the commits they followed. *Blocked: step 3.*
5. **Frequency table before archetypes.** Emit incident counts with no labels attached and read them, to find the archetypes nobody has named. *Blocked: step 4.*
6. **Rule synthesis with a human merge step.** Draft the guard and the rule line, never apply either unreviewed. *Blocked: step 5.*
7. **Antigravity and Codex adapters, and transcript sync across machines.** Last, because it is the largest build and the least certain payoff. *Blocked: no sync layer exists.*

> [!warning] concerns
> **coverage:** the corpus holds only failures a human noticed and typed a correction for, so a wrong-but-plausible edit that shipped unchallenged is permanently invisible to the system
> **untraceable rules:** an automatically written rule that is subtly wrong degrades every later session and surfaces as unrelated breakage weeks on, which is why no rule reaches an agent without a human merging it
> **detector precision:** the correction-phrasing signal is the weakest of the three and will produce a feed nobody reads if it runs without the git-diff signal beside it
> **payoff:** if the step 3 count shows forty one-off failures rather than a few repeated ones, the full pipeline produces roughly four rules a year and should not be built
> **sync:** transcripts never leave the machine that wrote them, so any transcript-based stage covers one machine until a sync layer exists, where the git-based stages cover all of them today

## the correction tax

A large share of prompts to a coding agent are not new work, they are the human catching the same mistake again: an un-namespaced commit trailer that hands authorship to a stranger ([[github co-author email collision with third-party accounts]]), a clone whose submodules got wiped, a wikilink that points at nothing, a background loop that eats twelve cores, half a journal note condensed into summary and the quotes dropped.

Each of those was diagnosed once, in a session, and then the diagnosis stayed in the transcript. Turning it into a rule is a manual step in `AGENTS.md` or a `SKILL.md`, and it only happens when someone remembers to do it.

## the loop

```
[agent execution] ──► [human correction prompt] ──► [git diff / commit]
                             │
                             ▼
               [session transcript harvester]
                (antigravity + claude + codex)
                             │
                             ▼
              [correction and failure extractor]
              (detects "you broke X", reverts, retries)
                             │
                             ▼
                [clustering into archetypes]
                             │
                             ▼
               [rule or skill update, with a guard]
```

## stage 1, ingest

Reuses [[cross-agent session indexing architecture]] rather than adding a daemon. Claude Code transcripts in `~/.claude/projects/` are already scanned by `skills/pkm-metadata-indexer/index_sessions.py` and served by `searchd.py`; Antigravity (`~/.gemini/antigravity-cli/brain/<id>/.system_generated/logs/transcript.jsonl`) and Codex (`~/.codex/sessions/`) still need adapters. Git history is the second source, read with `git log -p` and `git blame -C -C -C` for line provenance.

One thing that note already settled applies here: `tool_result` bodies are 80% of the corpus and are dropped at index time. A correction detector runs on prose and `tool_use` arguments, which is the part that survives.

## stage 2, finding the corrections

Three signals, in falling order of precision:

| Signal | How it reads | Failure mode |
| :--- | :--- | :--- |
| diff reversion | a human commit deletes or rewrites lines an agent commit added, within a short window | a human editing on top of good agent work looks the same |
| tool failure and retry | non-zero exit, then the same tool called again with changed arguments | normal exploration also retries |
| correction phrasing | prompt matches "you lost", "that broke", "don't", "undo", "restore" | catches sarcasm, quoted text and hypotheticals |

The phrasing heuristic is the cheapest and the weakest, and running it alone is how this ends up with a table of noise. Diff reversion is the one worth building first, because it is checkable against git rather than against a wordlist.

## stage 3, clustering

Group incidents into archetypes so a rule is written once rather than per incident. Four are known already: lossy compaction of human voice, attribution and provenance errors, submodule and wrong-directory traps, resource waste from polling loops.

Those four are the ones a human noticed repeating, which is a floor rather than a result. The value of clustering is the archetypes nobody named, so the first output of stage 3 is a frequency table of correction incidents with no archetypes attached, read by a human, to see what is in it besides the four.

## stage 4, distillation

Once an archetype has enough incidents behind it, write it out three ways, in falling order of usefulness:

1. a mechanical guard, a `.githooks/pre-commit` link checker or a deletion threshold, which fires whether or not the agent read anything
2. a test case in the relevant skill's checks
3. a rule line in the matching modular skill under `skills/`, per [[2026-08-28 agent instruction bloat - modular skills and compact synthesis]], not appended to a monolithic `AGENTS.md`

Ordering matters more than it looks. A rule an agent has to read and obey costs context on every turn and is followed unreliably; a hook is read never and followed always. Anything expressible as a guard should not become prose.

## storage

| Layer | Holds | Why not somewhere else |
| :--- | :--- | :--- |
| SQLite, beside the transcripts | sessions, turns, corrections, clusters, rule links | needs joins and counts, which markdown cannot do |
| git history | line attribution and diff pairing | already immutable and already there, so it is not copied in |
| vault markdown | the archetype notes and the skill rulebooks | the human reviews and edits these, so they are files |
| FTS5 and vectors | recall over past errors and fixes | the index already exists for the session corpus |

The database stores pointers, `(transcript path, line)` and commit SHA, not copies of turns. Transcripts routinely carry keys and private code, and a second copy is a second place to leak them.

## walkthrough, lossy compaction of a journal note

The incident, which happened on another machine, so the note and the commits below are not reachable from this vault. An agent ran a condensing pass over the 2026-08-28 day note and replaced verbatim dialogue, *"Food brought to you, isn't it nice?"*, with generic psychological summary. The correction prompt came back the same session: *"i feel a lot of my original notes were lost compared to original first pass note written by me. ai came to a few conclusions or summaries i m unsure about."*

Ingest and detection. Two signals fire together, which is what makes this a high-confidence correction rather than a phrasing guess. The prompt carries *"lost"* and *"unsure about"* and lands immediately after an agent edit, and the diff between the human entry at `21a223cc` and the agent edit at `77bb3586` is a 50% line reduction with the quoted dialogue gone.

Clustering. Filed under `lossy-human-voice-compaction`. The historical scan finds three earlier incidents where the human asked for verbatim quotes to be restored after a summarization pass, which is what takes this over the threshold from one bad day to an archetype.

Distillation. The rule, written into a journal curation skill: when structuring journal entries, preserve verbatim quotes, dialogue and concrete grounding detail, and summarize only the surrounding context. The guard, which is the part that actually holds: an edit cutting more than 30% of the lines of a human journal note, with no instruction to truncate, stops and asks.

The second archetype shows the same split more sharply. The co-author collision at [[github co-author email collision with third-party accounts]] is written up in full, and the write-up did not prevent the next occurrence, because a note is only read by whoever goes looking for it. What would have prevented it is six lines of `commit-msg` hook rejecting any `Co-Authored-By` address outside `users.noreply.github.com`.

## what would have to be true

The detector needs precision, not recall. A feed where one in three entries is a false positive becomes something nobody reads, and the cost of a missed correction is that it stays a manual fix, which is the status quo, so erring toward silence is cheap.

No rule reaches an agent without a human approving it. An automatically written rule that is subtly wrong degrades every session after it and is close to untraceable, because the symptom appears in unrelated work weeks later. Stage 4 proposes, a human merges, and that stays true however good the clustering gets.

Archetypes have to be earned from counts. Below some threshold of incidents, an archetype is one bad day, and encoding it as a rule taxes every future session for a one-off.

The rules have to be removable. Rules synthesized automatically accumulate, and the deletion path matters more than the write path, per [[2026-08-28 agent instruction bloat - modular skills and compact synthesis]].

Cross-machine sessions are a sync problem before they are an analysis problem. Transcripts live on the machine that produced them, and there is no sync layer today. The git half has no such problem, because a clone of the remote carries every machine's commits already, so a git-only detector covers all hardware on day one and the transcripts are what has to wait.

## Prior Art & Theoretical Framing

This architecture builds upon and departs from several major lines of research in experiential and self-reflective agent systems:

### Academic Foundations
* **[[public/2026-08-27 biomimetic AI - stealing from brains, immune systems, and evolution|Voyager (Wang et al., 2023)]]:** Pioneered lifelong learning agents that synthesize executable code into an embedding-indexed skill library. Our design adopts the modular skill library concept but extends it to compile deterministic verification guards (`.githooks`) rather than unconstrained action scripts.
* **Reflexion (Shinn et al., 2023):** Introduced verbal reinforcement learning, where agents reflect on failed trajectories and store episodic self-critiques. Our approach replaces LLM self-critique (which suffers from blind spots and hallucinated success) with the **empirical human delta** (Git reversions and steering prompts).
* **ExpeL (Zhao et al., 2023):** Explored extracting cross-task heuristics from experience. We ground these heuristics into structured, testable rules tied to specific line provenance rather than free-form advisory prompts.
* **AutoSpec & RuleChef (2024–2026):** Counterexample-guided inductive synthesis for extracting symbolic linter rules and safety invariants from execution traces.

### Industry Frameworks & Defense-in-Depth
* **Cognitive Memory Architectures ([[public/2026-08-27 Mem0 memory architecture - cloud pricing, security, and local privacy|Mem0]], Letta / MemGPT):** Multi-tier memory separating working context from episodic and archival memory.
* **Deterministic Guardrails vs. Advisory Prompts:** Industry consensus shows agents treat `AGENTS.md` and `CLAUDE.md` instructions as probabilistic suggestions. Modern engineering relies on defense-in-depth: intercepting workflows via lifecycle hooks (`PreToolUse`) and enforcing validation at the storage boundary via Git pre-commit hooks that cannot be bypassed with `--no-verify`.

### How Our Design Compares

| Dimension | Industry / Academic Standard | Our Architecture |
| :--- | :--- | :--- |
| **Ground Truth of Failure** | LLM self-evaluation or simulated unit tests. | **Human delta:** Git diff reversions within 24h + human steering prompts. |
| **Primary Output** | Expanded prompt files or fine-tuning datasets. | **Deterministic guards first:** Emits `.githooks` checks and linter rules; prose is a fallback. |
| **Context Hygiene** | Monolithic prompt files grow indefinitely. | **Modular skill lifecycle:** Dynamically loaded [`SKILL.md`](public/2026-08-28%20agent%20instruction%20bloat%20-%20modular%20skills%20and%20compact%20synthesis.md) files with explicit prune/retire paths. |
| **Privacy & Topology** | Cloud memory services with telemetry egress. | **100% Local-First:** ONNX DirectML embeddings, SQLite FTS5, and local Git history. |

---

## Related Notes
- [[public/cross-agent session indexing architecture|cross-agent session indexing architecture]]
- [[public/2026-08-28 agent instruction bloat - modular skills and compact synthesis|agent instruction bloat - modular skills and compact synthesis]]
- [[public/autocommit leftover changes|autocommit leftover changes]]
- [[public/git author|git author]]
- [[public/github co-authors for AI|github co-authors for AI]]
- [[public/track prompt history|track prompt history]]
- [[public/human vs AI git history transfers between notes|human vs AI git history transfers between notes]]
- [[public/token efficient PKM analysis architecture|token efficient PKM analysis architecture]]
- [[public/progress - local-first search daemon and indexer|local-first search daemon progress]]

