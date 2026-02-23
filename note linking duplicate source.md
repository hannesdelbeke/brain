---
aliases:
  - wrap in iframe
views: 4
last viewed: 2026-02-22
---

notes in obsidian rely on [[public/link|links]] between notes.
When you talk about something external, e.g. a github repo, you can't link to it.

So to create connections between notes, you make a note that duplicates the [[GitHub repo]], and just paste the URL in there. Maybe a screenshot and small description.
Example: the note [[Chocolatey Python API]] contains some [[wikilink|wikilinks]] and the [[URL]]

- If only I could link directly to a URL, and also able to add tags and wiki links.
- [[TODO include project READMEs in Obsidian|Linking directly to the README of a repo]] would be nicer. It already has an image and description.

see [[link unlinked websites]]

## Solutions

### Crawl links
crawl your note vault for links, e.g 2 notes both have the link www.example.com
- the crawler either replaces the link with a link to a note, and creates said note.
- or the crawler simply tracks the links in a database, and uses this to show this data somewhere e.g. in the [[Obsidian graph view]].

Look into [[annotate websites]], for more discussion on storing notes for a site.
### iframe
Embed the URL in an [[iframe]].
Note in [[Obsidian]], first define height, then width. Else height won't work.  
```HTML
<iframe src="https://www.example.com" height="200" width="800" ></iframe>
```
---
<iframe src="https://www.example.com" height="200" width="800" ></iframe>
