### Manual tool assisted merge
A solution tried in the past is a merge option in Unity.
1. press "ready to merge", a backup of the local package settings is saved, and the project manifest is rolled back
2. change branch, a manifest update is pulled
3. go back to unity, click continue merge, a merge happens to restore the project manifest, adding the local changes back
this requires to much work on the user. User forgets to use this and has a bad auto merge, or is confused by the steps or merge conflicts.