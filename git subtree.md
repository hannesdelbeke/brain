`git subtree` lets you nest one repository inside another as a sub-directory

The difference with [[git submodule]] is that no reference is saved to the original repo, instead it just merges (squashes) in the whole history.
This means no extra steps when you clone the repo like with submodules, that can leave an empty folder.

separate command to push back to the subtree remote repo, see [docs](https://gist.github.com/SKempin/b7857a6ff6bddb05717cc17a44091202)

[[git]]