
# Anonymous SHA Pointer

When migrating notes across [[git submodule|Git submodule]] boundaries (such as from private root to `public/`), commit the file as a single clean commit in the destination submodule, and record only the origin commit SHA in the [[YAML front matter]]:

```yaml
---
origin-sha: a9b9142b89ae
---
```

Leaving out the repository name prevents leaking private vault names. Because Git SHAs (12+ characters) have effectively zero probability of collision across personal repos ($1$ in $10^{14}$), local scripts and AI agents simply probe available local repositories (`git -C <repo> rev-parse --verify <sha>`) to match the source commit.

---

## When to Inject vs. When to Skip `origin-sha`

To avoid cluttering newly written notes with meaningless pointer metadata:

1. **Inject `origin-sha` (Preserve History):**
   * Use **only** when the note has an existing, multi-commit **git history of changes** in the source repository that carries historical value (evolution of thought, refactors, previous authors).
2. **Skip `origin-sha` (Clean Greenfield):**
   * Do **not** add `origin-sha` if the note was newly created in the current session and simply moved to `public/`, or if there is no prior git change history in the source repo except changing its private/public location.

---

### Related
- [[maintain git history between submodules]] — History preservation trade-offs
- [[moving files across submodules loses created date]] — Preserving timestamps across submodules
- [[AGENTS.md]] — Vault-wide rules for agent operations and metadata injections