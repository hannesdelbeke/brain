---
sentiment:
- 5
sentiment-hash: 68a07e09
sentiment-label:
- factual
tags:
- technical
---

`git subtree` lets you nest one repository inside another as a sub-directory

The difference with [[git submodule]] is that no reference is saved to the original repo, instead it just merges (squashes) in the whole history.

This means you don't need any extra steps after you clone the repo, like you do with submodules, which when forgotten, leave an empty folder instead, breaking your project.

A separate command to push back to the subtree remote repo, see [docs](https://gist.github.com/SKempin/b7857a6ff6bddb05717cc17a44091202)

[[git]]
