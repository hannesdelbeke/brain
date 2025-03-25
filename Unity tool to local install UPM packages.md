This was an old idea, before I knew you could embed UPM packages.
## Proposal
Create a local package that adds other local packages
https://docs.unity3d.com/Manual/upm-localpath.html

create 2 files
- `shared-manifest.json` (included in the git repo)
- `local-manifest.json` (excluded from the git repo)
Then have a script run in unity, check if any changes happened to either files.
If there was an update, e.g. user changed branch and checked out an update, a merge is run.

1. Support addition. Local manifest only adds additional packages, it does not override shared manifest settings.
2. Support override, e.g. changing the package URL to a local URL for dev purposes.
