---
tags:
  - technical
  - git
  - github
  - ai
  - solved
---

# GitHub Co-Authors for AI Models

[[GitHub]] parses [[public/git|git]] commit trailers matching `Co-Authored-By: Name <email>` to display multiple authors on commits and PRs.

## Recommended Co-Author Formats

Use GitHub's standard `<username>@users.noreply.github.com` pattern to link directly to official accounts:

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

## Adding Multiple Co-Authors in a Commit

Trailers must be placed at the very end of the commit message, separated by a blank line:

```bash
git commit -m "feat: implement new feature

Detailed explanation of changes here.

Co-Authored-By: Claude <claude@users.noreply.github.com>
Co-Authored-By: Google DeepMind <google-deepmind@users.noreply.github.com>"
```

## Uncommitted Changes & Automated Sweeps

When an AI agent automatically commits uncommitted human edits left in the working tree, the commit author is set to the human user, with the active AI model appended as a `Co-Authored-By:` trailer to preserve accurate attribution. See [[public/autocommit leftover changes|autocommit leftover changes]].

[[public/git|git]]
[[public/github|github]]
[[public/git author|git author]]
[[public/git cheatsheet|git cheatsheet]]
[[public/autocommit leftover changes|autocommit leftover changes]]
