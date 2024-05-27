It'd be nicer to be able to exclude code snippets from unlinked mentions.
You'd never want to add `[[]]` brackets to words in code snippets, since it'd break the code.

impact: Low

[[Obsidian Outgoing links]]

- [reddit thread](https://www.reddit.com/r/ObsidianMD/comments/1eaa9n2/how_to_make_obsidian_ignore_link_mentions_in_code/) that wants to ignore unlinked mentions in code
- [Reddit thread](https://www.reddit.com/r/ObsidianMD/comments/11tg0ii/decline_unlinked_mentions_in_outgoing_links/) asking to decline an unlinked mention. Letting the user review each link and accept or decline it.
	- To store a review state for each word, each word would need to be stored and tracked. Which gets complex when you change a sentence. This review option is a nice idea but doesn't seem straightforward. It'd also break when files are edited outside Obsidian.
	- The comments suggest a workaround: avoid short namespaces. Instead of `covariance`, use `covariance (statistics)`. However, this wouldn't work for aliases, since `covariance` would be an alias meant to help with [[discovery]] of [[unlinked notes]]. 
		- [[when a few links help but many overwhelm]]
- I could consider using data view or query control plugin to create my own backlinks view. advanced, complex to setup, and relies on third party plugins. For now its not worth it, and having found - and rejected - this solution, it's clear I don't really need this, so I'll stop writing this note.

2025-11-16

[[Obsidian improvements]]