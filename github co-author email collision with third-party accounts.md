---
tags:
  - technical
  - git
  - github
  - ai
  - troubleshooting
aliases:
  - github co-author email collision with third-party accounts
  - github co-author attribution failure example
  - figmapy co-author bug
---

# GitHub Co-Author Email Collision with Third-Party Accounts

A case study on how [[GitHub]] commit trailer resolution matches email addresses instead of display names, and how generic email aliases can hijack commit co-authorship.

## Real-World Example: What Went Wrong

When committing code on [[public/figmapy|figmapy]] with Claude, [[public/antigravity|agy]] tried to add Claude as a co-author to display in GitHub:

```git
Co-Authored-By: Claude <noreply@anthropic.com>
```

However, GitHub displayed the co-author avatar and username as `@shimonenator` instead of Claude.

Later, when adding Gemini and Antigravity:

```git
Co-Authored-By: Gemini <gemini@google.com>
Co-Authored-By: Antigravity <antigravity@google.com>
```

GitHub still displayed `@shimonenator`.

## Why This Happened

1. **Email-Based Matching:** GitHub resolves commit trailers strictly by matching the **email address** against registered user account profiles, completely ignoring the display name (`Claude`, `Gemini`, `Antigravity`).
2. **Third-Party Alias Claiming:** A single third-party user (`@shimonenator`) happened to have registered both `noreply@anthropic.com` and `@google.com` aliases on their GitHub account.
3. **Commit Hijacking:** GitHub attributed every commit containing those generic emails to `shimonenator`. Even when Claude was removed from a commit, Simon Schwartz remained because the `@google.com` addresses also pointed to his profile.

## Resolution

Use GitHub's official `<username>@users.noreply.github.com` namespace to ensure trailers resolve directly to official organization profiles. See [[public/github co-authors for AI|github co-authors for AI]].

Related: [[public/git|git]], [[public/github|github]], [[public/git author|git author]], [[public/github co-authors for AI|github co-authors for AI]]
