
I implemented this, see https://github.com/hannesdelbeke/electron-unity-hub

### Features
the new features:
- [x] give projects a nickname, so you can have 2 branches checked out of the same project without confusion
- [x] When trying to open a project, that's already open, make that project's window active, Instead of just saying "this project is already open"
- [x] support other [[version control]], not just Unity Version control. e.g. integrate with perforce or git.

existing features
- [x] project name
- [x] project path 
- [x] browse to project
- [x] set unity version
- download unity apps/versions

the unity hub already does a lot of great things.
- download and install unity versions for us, and auto load the correct one for our project.

But it also pushes Unity Version Control and Unity Cloud.
and tabs for learning, and resources.
This adds visual clutter.

Instead of recreating the whole hub, let's rely on the existing hub to manage and install versions. And make a new hub that only acts as a project launcher.

--- 

> This has a lot of overlap with a generic [[app launcher]], why don't we use that?

The difference would be
- **Modified** - show when the project was last opened
- **Editor version** - show unity version of the project
- **version control** integration

A generic launcher can already set a nickname for a launch icon or command, and open a project with a specific version.
But you need to manually set it up every time you change unity version.

---

> How could it integrate with source control?

 Use source control as a thin metadata/safety layer, not as a full VCS client.

  Core integration model

  1. Detect repo type per project (.git, .p4config/workspace mapping, Plastic/UVCS markers).
  2. Use a provider interface: ISourceControlProvider with common calls:
      - GetBranchOrStream()
      - GetWorkspaceRoot()
      - GetStatusSummary() (clean/modified/ahead/behind/conflicts)
      - GetRemoteInfo()
  3. Keep operations read-only by default. Show state, don’t replace Git/P4 GUIs.

  How this solves your 3 new features

  4. Nicknames for same project on different branches:
      - Auto-suggest nickname: ProjectName (branch/stream)
      - Store launcher entries by projectPath + vcsWorkspaceId + branch/stream, not just path.
  5. “Already open” behavior:
      - Track running Unity editors and their project paths.
      - If same path+workspace is open, focus that window.
      - If same path but different branch/worktree is requested, launch that distinct entry.
  6. Multi-VCS support:
      - Git provider: branch, dirty state, ahead/behind.
      - Perforce provider: client/workspace, stream, pending changelists.
      - UVCS/Plastic provider: workspace + branch.

  Practical UX

  - Project row columns:
      - Nickname
      - Path
      - Unity version
      - Source control (Git: feature/foo, P4: //Game/Main, etc.)
      - Modified / Last opened
  - Quick filters: Dirty, My branch, Needs pull, Conflicts.
  - Launch guardrails:
      - Warn if dirty and switching branch/workspace.
      - Warn if lock file/open editor exists; offer “Focus open editor”.

  Implementation tips

  1. Start with a plugin/provider system so Git/P4 ship independently.
  2. Cache VCS info and refresh in background to keep UI fast.
  3. Fall back gracefully when CLI/tooling is missing (show “VCS unavailable”).
  4. Let advanced users define custom status commands per repo.

---

[[tool idea]]
[[Unity Hub]]