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

A supervisor that reads agent session transcripts and git history, finds the turns where a human had to correct the agent, clusters the recurring ones, and writes the result back as rules and skills instead of leaving it in chat logs.

**Status, 2026-08-28: nothing built, this is a design.** The ingest half of it exists as [[cross-agent session indexing architecture]], which indexes Claude Code transcripts today and has no Antigravity or Codex adapter. Everything downstream of ingest, the correction detector, the clustering and the rule writer, is unwritten. The numbers below are targets, not measurements.

> *Every prompt is a call to action: write new idea, fix an issue, make a thing. We now have some kind of session tracker or reader. Also relates to tracking prompt history and the automated daily logger. Go through all prompts on this machine, and identify what went wrong. Check the summary if there is one for the session (I know Claude has a recap, unsure if AGY does), then see if the prompt was resolved: what work or note it created, and then in future what issues it caused, or mistakes it made, or things it missed. Then link it to skills we extracted from this. How would this work? Would we store data, store SQL only, links only? Git history and session will be main source of truth (session data distributed across development hardware). End goal: by identifying where we went wrong and where we introduced bugs or shortcomings, we can come up with a system that can be self-learning—an external thing that watches our process day to day, and identifies issues. Nearly every prompt is me spotting an issue and asking AI to fix it. There might be patterns in things AI often breaks. I'd like you to find those patterns, and for that we might need a system.*

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

The corpus is biased toward failures that were noticed. It only contains mistakes a human saw and bothered to type a correction for, so a wrong-but-plausible summary that got committed and never questioned is invisible to it. That is a ceiling on the word self-learning: the system automates distilling the corrections, not noticing them.

## smallest first step

One script over git alone, no transcripts and no index: walk the log of a repository and emit every pair where a commit authored by a human rewrites lines a commit authored by an agent added within the previous day. Print the pair, nothing else. No clustering, no rule writing, no schema, and nothing that needs a machine other than the one holding the clone.

Read the output by hand. What matters is not the tool, it is the count and the shape of the list: whether the same failure shows up ten times or once each. Ten times is a hook worth writing that afternoon, whatever else gets built. A list with no repetition in it means the archetypes are already all known, and the rest of this note is a pipeline for producing four rules a year.

Related: [[cross-agent session indexing architecture]], [[2026-08-28 agent instruction bloat - modular skills and compact synthesis]], [[autocommit leftover changes]], [[human vs AI git history transfers between notes]], [[token efficient PKM analysis architecture]]
