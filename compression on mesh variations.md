To save data, we could save mesh variations as diffs / deltas in our project.

## cons
- limited to [[ASCII]]
- can't think of many realistic uses
	- different UVs. but usually same meshes reuse same UVs.
	- small mesh variations. sphere with 100k verts and only a few different verts. can't see this happening in practice.

- it might work if someone duplicates a mesh a few times in the project.
  e.g. outsource studios duplicate a mesh, so they can independently change it without screwing another studio over. It's hacky but happens.

> [!example]-
> - Unity & Unreal projects often contain mesh variations, leading to duplicate data. 
> - These duplicate meshes are also likely to be duplicated on the perforce repo

## Saving deltas

> [!example]
> A 100mb mesh variation, where only the UV is different. It's wasteful to have two 100mb file instead of just 1.
> 
> [[git]] only saves the changes between 2 textfiles, instead of saving 2 full textfiles

A file **reference with override capabilities** can handle this, but runs into issues if the original file changes.

Git solves this by never changing the *original file* in the git history.

Only Maya has support for this, Unity, unreal, and blender don't. See [[dcc referencing comparison]]

## similar tech
- **USD (Pixar's [[Universal Scene Description]])**: Supports **layered editing**, where changes (position, material, etc.) are stored as deltas in layers — very similar to what you're proposing.
- **Delta Mush / Delta [[Blendshape]]**: Not file diffs, but examples of storing deltas for deformation

## ideas
what if we add a manager build on git
- by default history of ASCII files doesn't show in the asset browser.
- a file revision can be tagged as a separate file, so it shows in our browser
- git can have branches for variations, but this might get messy with many branches?
history just points to a commit
- Artist won't be able to have both variants open on their pc at same time. Unless the asset manager somehow pulls only the file ([[git sparse-checkout]] or [[git archive]]) the artist wants, to a new temp repo?

Perforce saves files, not diffs. So this won't work in perforce
## tags
[[compression]]
[[compression vs. deduplication]]