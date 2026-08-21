
Commit the file as a single clean commit in the destination [[git submodule|submodule]], and record only the origin commit SHA in the [[YAML front matter]]:

```yaml
---
origin-sha: a9b9142b89ae
---
```

Leaving out the repository name prevents leaking private vault names. 

Because Git SHAs (12+ characters) have effectively zero probability of collision across personal repos ($1$ in $10^{14}$), local scripts and AI agents simply probe available local repositories (`git -C <repo> rev-parse --verify <sha>`) to match the source commit.