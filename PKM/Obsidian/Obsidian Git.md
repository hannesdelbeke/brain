 [obsidian-git](https://github.com/denolehov/obsidian-git) is a [[Obsidian plugin]] to automatically [[backup]] your Obsidian notes with [[Git]].

Here's a [tutorial](https://github.com/gitobsidiantutorial/obsidian-git-tut-windows/blob/main/README.md) with images on setting up Git with Obsidian for non-tech people.
and the related Obsidian forum [Discussion](https://forum.obsidian.md/t/setting-up-obsidian-git-on-windows-for-the-tech-uninitiated-with-images/15297)

In case of public key error on git push, see [[check ssh github connection]]

might have to run this the first time
```
git submodule init
git submodule update --recursive --remote --merge
```