---
views: 14
aliases:
  - coloring links based on folder
last viewed: 2026-02-23
---
I want to visually differentiate between public and private notes.
I want as many of my notes set to public, but when I create a new note from a private note, the new note will be made in the same folder, making it private.

In the past I [[Obsidian - color unlinked notes red|colored unlinked notes red]].
When I tried a similar approach with [[Obsidian css]] snippets only, it didn't work since the link source isn't exposed.

I used [[supercharged links]] to add an attribute to each link containing the path, e.g. `[data-link-path^="public/"]`. And then use some CSS to color public links green (Because I plant my [[Evergreen notes]] in a [[digital garden]] 🌱), and keep my private links the default Obsidian link color,<span style="color:#a028e1; background:rgba(92,92,92,0.2)"> purple </span>.

---
### Update
After using this for a few days, this is great [[UX]]. With just a glance you can:
- Quickly see notes that should be public but were private.
  E.g. for the [[use wikilinks instead of hashtags|tag links at the bottom of a note]]. Sometimes I see a purple link that should be green, which means it's a broken link for anyone trying to access it on [[my wiki|my digital garden]].
- Instantly tell if a public note contains private links, and needs cleaning up. Since these show as dead links on the website.
- See quickly if a note is ready to publish, because it only links to public notes.


> [!warning] 
> I had an empty file `git` in my private notes. And a public file `git.md`.
> The empty file was colored green in the file browser. I deleted it for now, but there might be bugs for notes that share names.
