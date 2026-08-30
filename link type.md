---
sentiment:
- 5
sentiment-hash: dccbc0e1
sentiment-label:
- factual
tags:
- technical
- planning
- work
- hobby
---

if `son` is linked to `mother`, what kind of link is this? 
- if you could add a type we could say the link is of type `family`.
  This would allow to make more complex links than just a normal [[wikilink]].
- If 1 directional links are supported, `son` could link to `mother` with a link of type `parent`.

Support for link types would allow us to add relationships or [[1 directional annotations|descriptions/notes to links]].

right now we can [[public/link]] note A to note B, but it's not always clear why they are related.
Ideally the note says: Note A relates to note B because of reason.
e.g. `[[Bob]] is [[Lucy]]'s dad'`

there's a great forum discussion on this [add support for link types](https://forum.obsidian.md/t/add-support-for-link-types/6994/38)

also see [[Link strength]]

In [[JIRA]], you can define type of link. e.g. related, blocking, duplicate, ...

## Don't confuse with
link types could also be confused with, what type of link is it. e.g. :
- [[backlink]]
- [[wikilink]]
- hyperlink / [[URL]]

See [[proposal - typed directional links for obsidian]] for the unified proposal.
> [!learning] the Breadcrumbs plugin (github.com/michaelpporter/breadcrumbs) already does typed, directional links today — parent/child, next/prev, or custom types defined via frontmatter, tags, or a naming scheme, rendered as its own directed graph.
