If you use [[Obsidian Git]] to auto back up your notes, this can fail when you are not on a branch, e.g. after a failed resolve.
Obsidian will keep committing, but fail to push. 
I discovered no notes were pushed to the server for 4 months.

This happened because of a conflict in my [[git submodule]] vault.
