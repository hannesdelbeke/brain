---
tags:
  - git
  - obsidian
  - technical
  - devlog
origin-sha: 72e8d1a53
created: 2026-08-19
---
Technical exploration into how the [[Obsidian plugin - Git]] plugin renders historical diff views and how custom URI schemes or UX interactions can link to past revisions.

## Internal Architecture of `obsidian-git`
Inspecting `main.js` from the installed `obsidian-git` plugin reveals how historical views are constructed:

**1. Custom ItemView Types**
- `split-diff-view`: Desktop side-by-side CodeMirror 6 merge view.
- `diff-view`: Unified diff view (default on mobile).
- `git-history-view`: Sidebar log viewer.

**2. The `openDiff` Method**
When clicking a commit in the history view, `obsidian-git` executes `openDiff()`:
```javascript
openDiff({ aFile, bFile, aRef, bRef, event }) {
    let style = this.plugin.settings.diffStyle; // "split" or "git_unified"
    let state = {
        aFile: aFile,           // e.g. "path/to/note.md"
        bFile: bFile ?? aFile,
        aRef: aRef,             // commit SHA (or HEAD~1)
        bRef: bRef              // commit SHA (or undefined for working tree)
    };
    let leaf = getLeaf(this.plugin.app, event);
    leaf.setViewState({
        type: style === "split" ? "split-diff-view" : "diff-view",
        active: true,
        state: state
    });
}
```

**3. Content Retrieval & Rendering**
Inside `createMergeView()`, the plugin fetches historical text directly from local Git using `git.show([`${ref}:${relativeRepoPath}`])` and mounts a read-only CodeMirror 6 `MergeView` comparing `aRef` against `bRef`.

**4. Custom URI Integration**
Because Obsidian exposes `app.workspace.getLeaf().setViewState({ type: "split-diff-view", state: { aFile: "note.md", aRef: "abc1234" } })`, a lightweight plugin or custom URI handler (e.g. `obsidian://open-git-diff?path=...&sha=...`) can trigger native diff tabs directly.

### References
- [[obsidian git diff ux proposals]]