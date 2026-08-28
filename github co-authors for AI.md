---
tags:
- technical
- git
- github
- ai
- solved
---

# GitHub Co-Authors for AI Models

[[GitHub]] parses [[git]] commit trailers matching `Co-Authored-By: Name <email>` to display multiple authors on commits and PRs.

> [!WARNING]
> GitHub resolves co-authors by matching the **email address** against registered GitHub user accounts, NOT the display name.
> If a generic email like `noreply@anthropic.com` or `gemini@google.com` is registered on an arbitrary user's account, GitHub attributes that user instead.

## Recommended Co-Author Formats

Use GitHub's standard `<username>@users.noreply.github.com` pattern to link directly to official accounts and avoid collisions:

### Claude (Anthropic)
Links directly to the official [claude](https://github.com/claude) profile:
```git
Co-Authored-By: Claude <claude@users.noreply.github.com>
```

### Google Gemini / Antigravity (Google DeepMind)
Links directly to the official [google-deepmind](https://github.com/google-deepmind) profile:
```git
Co-Authored-By: Google DeepMind <google-deepmind@users.noreply.github.com>
```

> [!CAUTION]
> **Never use generic domain emails** like `gemini@google.com`, `antigravity@google.com`, or `noreply@anthropic.com`.
> Third-party users who claimed or added those custom email aliases to their GitHub accounts will hijack the commit co-authorship.
> Always use `<organization-or-user>@users.noreply.github.com` which is strictly namespaced by GitHub.

## Adding Multiple Co-Authors in a Commit

Trailers must be placed at the very end of the commit message, separated by a blank line:

```bash
git commit -m "feat: implement new feature

Detailed explanation of changes here.

Co-Authored-By: Claude <claude@users.noreply.github.com>
Co-Authored-By: Google DeepMind <google-deepmind@users.noreply.github.com>"
```

## Real-World Example: What Went Wrong

When committing code on [[figmapy]] with Claude
[[antigravity|agy]] tried add claude as co author to show in github

```git
Co-Authored-By: Claude <noreply@anthropic.com>
```

But GitHub displayed the co-author avatar and username as `@shimonenator` instead of Claude.

Later, when adding Gemini and Antigravity:

```git
Co-Authored-By: Gemini <gemini@google.com>
Co-Authored-By: Antigravity <antigravity@google.com>
```

GitHub still displayed `@shimonenator`!

**Why this happened:**
1. GitHub resolves commit trailers strictly by matching the **email address** against user account profiles.
2. A single third-party user (`@shimonenator`) happened to have registered both `noreply@anthropic.com` and `@google.com` aliases on their GitHub account.
3. GitHub ignored the display name (`Claude`, `Gemini`, `Antigravity`) and attributed every commit containing those emails to `shimonenator`.
4. Even when Claude was removed from a commit, Simon Schwartz remained because the `@google.com` addresses also pointed to him.

**The Solution:**
Use GitHub's official `<username>@users.noreply.github.com` namespace:

```git
Co-Authored-By: Claude <claude@users.noreply.github.com>
Co-Authored-By: Google DeepMind <google-deepmind@users.noreply.github.com>
```

This guarantees GitHub links directly to `https://github.com/claude` and `https://github.com/google-deepmind`.

## Uncommitted Changes & Automated Sweeps

When an AI agent automatically commits uncommitted human edits left in the working tree, the commit author is set to the human user, with the active AI model appended as a `Co-Authored-By:` trailer to preserve accurate attribution. See [[public/autocommit leftover changes|autocommit leftover changes]].

[[public/git|git]]
[[public/github|github]]
[[public/git author|git author]]
[[public/git cheatsheet|git cheatsheet]]
[[public/autocommit leftover changes|autocommit leftover changes]]
