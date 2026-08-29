---
energy: 5
sentiment:
- 4
sentiment-hash: fd7a4804
sentiment-label:
- concerned
tags:
- journal
- technical
- hobby
---

it seems [[Obsidian plugin - Git]] is not running on startup anymore, or committing files regularly.
- [[obsidian git backup can fail]]

is this maybe because there are too many changed files?
especially after [[2026-02-22 Obsidian track note view]]

## Evidence

Investigated 2026-08-25 from a clone of the repository. The clone is not the live vault: it was cloned that morning, `.obsidian/` is gitignored so it holds no plugin config. The plugin settings below are read from a reference `.obsidian/plugins/obsidian-git/data.json` (obsidian-git 2.38.6) as a proxy for how the plugin is normally configured, not from the vault that failed.

What the commit history proves:

- Commit rate dropped over the viewcount era and recovered after it. Using the date inside each `auto backup:` message: 2025-10-01 to 2026-02-22 gives 238 backups over 144 days (69 active days); 2026-02-22 to 2026-07-22 gives 107 over 150 days (52 active days); 2026-07-22 to 2026-08-25 gives 100 over 35 days (23 active days). Roughly 1.7, then 0.7, then 2.9 backups per day.
- Median gap between backups inside one working session is 46 min before, 62 min during, 41 min after. Never the 10 min the interval setting asks for.
- Backlog commits exist and match the complaint. Median files per auto backup is 2 across 1836 backups. Three outliers: 384 files at `2026-07-22 11:28` (823 deleted lines, nearly all `views: N` frontmatter), 448 files at `2026-07-29 14:08` (mostly deletions of empty notes), 162 files at `2026-08-23 19:26` (the sentiment frontmatter pass).
- Size is ruled out. 3231 notes, 3285 tracked files, `.git` is 8.8 MB, largest tracked file is a 632 KB pdf. There is no large binary or image churn that could stall a commit.
- Nothing is stuck in the repo itself. No merge or rebase state, no detached HEAD, main tracks origin/main cleanly. The failure mode in [[obsidian git backup can fail]] is not what is happening.
- Some `auto backup:` message dates run days ahead of their git author dates (git 2026-07-13 11:28 vs message 2026-07-22 11:28, and four others), and two commits carry the year 2116/2117. Clock skew or a history rewrite, unrelated to the backup stalling but it makes git dates unreliable for this analysis.

Leading hypothesis, unconfirmed. The proxy settings have `autoSaveInterval: 10` together with `autoBackupAfterFileChange: true`. That second option means "commit-and-sync after you stop editing": every vault write restarts the 10 minute timer instead of letting it run. The [[obsidian-sentinel]] rule from [[2026-02-22 Obsidian track note view]] wrote a `views` frontmatter field on every note open and reset it on every close, so simply reading notes kept restarting the timer and the backup could only fire once Obsidian sat idle for 10 minutes. That fits the halved commit rate during the viewcount era, the 62 min session gaps, and the 384 file catch-up commit. It is a hypothesis: the settings actually in force on the failing machine were never read.

Also unconfirmed: whether the plugin fails to load at startup at all, as opposed to loading and never firing its timer. `autoPullOnBoot: true` and `updateSubmodules: true` both run before the plugin is ready, and this vault has a [[git submodule]], so a slow or hanging boot pull would look identical to "not running on startup".

## Plan

Run these on the machine with the live vault.

1. Open Settings, Community plugins, Git, and record `Auto commit-and-sync interval`, `Auto commit-and-sync after stopping file edits`, `Pull on startup`, `Update submodules`, and `Disable notifications`. Compare against the proxy values above.
2. Turn off `Auto commit-and-sync after stopping file edits`. With it off the 10 minute interval fires on schedule regardless of how much you are typing, which is the behaviour the note expects.
3. Turn on `Show error notices` and turn off `Disable notifications`, so a failed sync is visible instead of silent.
4. Read the plugin log after a session that should have committed: `Ctrl+Shift+I`, Console tab, filter on `obsidian-git`. A stalled boot pull or a submodule error shows up there.
5. From the vault root, check the backlog with `git status --porcelain | wc -l` and `git status -sb`. Anything over a few hundred means the timer is not firing, not that git is slow.
6. Confirm the repo is healthy: `git status -sb` shows a branch and not `HEAD (no branch)`, and `ls .git | grep -E "MERGE_HEAD|REBASE"` returns nothing. This is the failure from [[obsidian git backup can fail]].
7. If pull on startup is the blocker, set `Pull on startup` off and pull manually, or set `Update submodules` off and handle the submodule separately.
8. The [[view count]] churn is already gone: the frontmatter field was removed in the 2026-07-22 commit and the tracking moved to a plugin that stores counts outside the notes, see [[2026-07-22 follow up Obsidian viewcount]]. No action needed there, but it means step 2 is now the only known remaining trigger.
