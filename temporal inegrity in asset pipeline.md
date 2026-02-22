---
views: 1
last viewed: 2026-02-22
---
If a user rolls back an asset to an older version, that asset might be only compatible with the old tool version, or the old [[asset pipeline]]. 
	*e.g. the new workflow relies on a new naming convention, we updated all tools to work with the new naming convention. But are still relying on a few legacy assets that never needed updating. But now we need to update them and the new tools aren't compatible.*

Ideally we roll back the tool manifest that defines the dependencies, so it points to the old tool. And our tool environment auto handles this rollback for the user, installing the old tool, so the user can just launch the old tool.

This can easily be achieved if your tool manifest lives in the same repo as the files it processes, e.g. a git repo. And it installs tools from a `requirement.txt`

However, source files often don't live in the same [[repository|repo]] as the game.
E.g. [[Perforce]] is more complex: artists can manually roll back a single asset.
Tere's no [[temporal integrity]], since the tool manifest hasn't rolled back. It's now up to the user to do this manually.

---
LLM feedback
> Git (or any versioned system) can roll back cleanly, but Perforce + external toolchains + asset pipelines cannot. When one system is time‑travel‑capable and the others aren’t, you lose historical reproducibility.

Cross‑System Version Drift

---
### the solution 

**Every asset should be processed by the toolchain version that existed when that asset revision was created.**

This means tools must be:
- **versioned**, The tool manifest must support rollback.
- **reproducible**, (immutable)
- installable on demand.

Introduce a “Tool Resolver” Layer, a small service or script that:
- reads the tool manifest for the current asset revision,
- installs or activates the correct tool version,
- launches the tool in the correct environment.
example:
- `nvm` for artists
- `pyenv` for asset pipelines
- [[asdf]] for game tools

Make Tool Environments Immutable
- versioned installers
- versioned configs
- versioned dependencies

If Perforce allows arbitrary rollback on individual assets, then the asset itself must carry the pointer to the tool.
e.g. a custom Perforce attribute, metadata in the file

If tools evolve independently of assets:
- pipelines break,
- naming conventions drift,
- validators mismatch,
- old assets become uneditable.

---
[[tool distribution]]
[[versioning]]
[[version control]]