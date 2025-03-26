# Solution
- you now can copy packages from `project\Library\PackageCache` to `project\Packages`, which embeds them in the project.
- add a [[gitignore]] to the Packages folder and you have local packages.

# Problem description
### TLDR
Users cant install local UPM packages without being in conflict with source control.
Forcing all tools (packages) to be installed in the project, instead of a single local install.
### Context
[[Unity]] loads the [[UPM project manifest]] to decide which packages to download and install.
If you use source control for your project (e.g. [[git]]), your manifest will be included, and any local changes show up in git as changes to submit.
Whenever you pull an update or change branch, and there was a change to the project manifest, a merge conflict will occur.
So there's currently no way to have a local manifest with user packages installed.

### Local user override
Installing all packages for a project is like installing all apps for your team on everyone's computer. Coders also get the art apps like Photoshop and Maya, and artists also get visual studio.

A better approach is to only install what you need. This reduces install time, and empowers teams to create their own tools. If a tool is broken, only that team is blocked, instead of everyone in the project being blocked.
Otherwise non-dev teams won't be allowed to submit their own tools without slow reviews from the dev team, in fear of breaking the project for everyone. 

### Challenge
The challenge is to still allow pulling changes in the manifest while maintaining local changes. A basic merge is not sufficient usually, requiring technical knowledge, so can't be used by e.g. artists.
### Ideas
- [[Unity tool to local install UPM packages]]
- [[Unity manifest merge helper]]
- The android manifest might support local edits.
	- [mention](https://forum.unity.com/threads/where-is-the-android-manifest.1233775/) of merge android manifest path
	- [UnityAndroidManifestCallback](https://github.com/Over17/UnityAndroidManifestCallback)
### Other
- [Forum thread](https://forum.unity.com/threads/using-multiple-assetbundle-manifests-in-one-application.484130/) complaining about lack of multiple manifests (2017)
- [Thread](https://forum.unity.com/threads/multiple-package-sources.772961/) on use multiple package sources, can you use a local source to work around this issue?

[[Unity local]]
