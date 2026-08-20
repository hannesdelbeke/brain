AI started tagging notes
it looks clean in the frontmatter.
some old concerns about tags could be addressed by AI
but should we use it?

---

## Should AI Tag Notes in Frontmatter? (Tradeoffs & Best Practices)

1. **How AI Solves Old Tagging Friction:**
   - **Manual upkeep eliminated:** AI automatically maintains taxonomy consistency without human manual tagging fatigue.
   - **Synonym clustering:** AI maps disparate terms (e.g. `gpu`, `cuda`, `graphics-card`) to a unified canonical topic.

2. **Why Frontmatter Tags are Still Problematic vs. Wikilinks:**
   - no [[hashtag synonyms]]
   - **No Rich Backlinks:** In Obsidian, `#tags` do not support dedicated bidirectional graph pages or embedded context without third-party plugins.
   - **Portability:** Wikilinks (`[[topic]]`) work seamlessly across graph queries, Dataview, and pure markdown exports.

3. **The Recommended Hybrid Pattern:**
   - Use frontmatter for **structural metadata / types** (`type: research`, `status: done`, `author: gemini`).
   - Use **wikilinks** for conceptual topics and relations (`topics: ["[[AI]]", "[[git]]"]`).
   - This gives clean YAML presentation while preserving Obsidian graph connectivity.

## References
- [[use wikilinks instead of hashtags]]
- [[note types]]
- [[no hashtag support in obsidian link]]
- [[differentiate between AI and human notes]]

