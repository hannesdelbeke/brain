---
sentiment:
- 5
sentiment-hash: e0986ff8
sentiment-label:
- factual
tags:
- technical
- planning
---

apps to replace [[Obsidian]] as the editor. for the same apps judged as a corpus for search and agents to read, with star counts, see [[pkm vault indexing landscape]].

## alternatives

- noteshub (paid) [[noteshub whiteboard]]
	- kanban
	- whiteboard
	- write notes
	- music notes
- [Zim wiki](https://zim-wiki.org/)
- [Standard Notes](https://github.com/standardnotes/app)
- [logseq](https://docs.logseq.com/#/page/videos)
	- looks cool, nice and simple
	- [open source](https://github.com/logseq/logseq)
	- uses markdown, compatible with obsidian
		- [official post with recap](https://hub.logseq.com/integrations/aV9AgETypcPcf8avYcHXQT/how-to-use-obsidian-and-logseq-together-and-why-markdown-matters/1rqp92wgow7wGXS37Ckz1U)
		- [video](https://www.youtube.com/watch?v=knxDHO3U2_8&t=142s) discussing this topic
			- obsidian better for long docs
			- logseq has block based approach (reference other notes)
		- TODO change default behavior for obsidian to support logseq
			- default location new notes: folder "pages"
			- default location new daily notes: folder "journals" YYY_MM_DD
			- [forum post](https://discuss.logseq.com/t/making-obsidian-play-nice-with-logseq/1185) with more info
	- the markdown compatibility above is the file build. the DB rewrite moves storage into SQLite and is beta, so the two builds are not the same app
- [QOwnNotes](https://www.qownnotes.org/)
	- markdown
	- open source
	- great [docs](https://www.qownnotes.org/getting-started/markdown.html)
		- [PR](https://github.com/qownnotes/scripts/pull/136) merged in supports wiki link
- [caret](https://caret.io/)
	- markdown
	- nice minimal UI
- [markor](https://github.com/gsantner/markor)
	- android only
	- markdown
- [org-roam](https://github.com/org-roam/org-roam)
- [Zettlr](https://www.zettlr.com/)

## VS code plugins

- [Foam](https://foambubble.github.io/foam/)
	- [get started](https://github.com/foambubble/foam-template/blob/master/getting-started.md) article
	- [[visual studio code|vscode]] plugin
	- technical GitHub page [template](https://github.com/foambubble/foam-template)
- [memo](https://github.com/svsool/memo), dormant, last commit july 2024
- [dendron](https://marketplace.visualstudio.com/items?itemName=dendron.dendron), visual studio plugin 🔥, [dendron wiki](https://wiki.dendron.so/notes/6DZiBObwhZNYRjnokQ422/), git ⭐7.5k, dormant, last commit november 2025
	pros:
	- markdown
	- wiki links
	- supports several vaults, and remote vaults!
	- can be edited on git, reflected in the wiki
	- supports publish to GitHub
	cons:
	- table with metadata at top of every post ? [example](https://github.com/dendronhq/vault.dendron.community/blob/master/notes/meet.dendrologist.2022.09.md)
	- seems to add metadata to notes

## rejected

- [mindforger](https://www.mindforger.com/#features)
	- markdown
	- crap UI
- [Trilium](https://github.com/TriliumNext/Trilium) is a open source local SQL database. everything lives in 1 file.
	- bad to store on git, but could live in a SQL backup?
	- the old `zadam/trilium` link redirects here, development moved to the TriliumNext fork
- [nota](https://nota.md/)
	- mac only
	- not released
	- supports [[wikilink]]
- [typora](https://support.typora.io/Links/)
	- no wiki links, see [doc](https://support.typora.io/Links/)

## further reading

- [5 reasons why markdown could be your secret weapon](https://elizabethbutlermd.com/5-reasons-why-markdown-could-be-your-secret-weapon-for-effortless-personal-knowledge-management/) covers the advantage of markdown, and several apps
- [hacker news discussion](https://news.ycombinator.com/item?id=29996714)
- [toolfinder list of pkm apps](https://toolfinder.co/lists/best-pkm-apps)
