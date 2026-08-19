I was doing git commits to [[linking to git commits and diffs in obsidian via uri|this note]], in order of:
1. human
2. ai
3. human
4. ai 

which attributes it nicely with [[git author]]

But then decided to extract part of it to [[link to git historic notes devlog|this note]], losing all this human/AI history. It's indirectly accessible, both file changes in same commit.
Would AI and scripts used in future be smart enough to find this indirect history?

> [!ai] Yes git blame maintains indirect history
> Tracing Line Provenance Across Note Extractions (Verified on Vault History)
> 1. **Confirmed with Git Blame (`git blame -C -C -C "link to git historic notes devlog.md"`):**
>    - Testing this directly on your new note shows that **Git successfully traverses the extraction**:
>      - `afa8bfb63d (Obsidian Blade) > can we read code for [[Obsidian plugin - Git]]...`
>      - `ccb151b310 (gemini)         > [!ai]- How obsidian-git opens history...`
>    - Even though the file was created in commit `75b6dcaee`, `git blame -C` detects that 60+ lines were moved from `linking to git commits and diffs in obsidian via uri.md` and preserves original human vs. AI line-by-line attribution.
> 2. **AI Semantic & Diff Matching:**
>    - When scripts or AI parse vault history via `git log -p`, simultaneous deletions in Note A and additions in Note B within the same commit are detected as an extraction refactor.
> 3. **Preserving Fine-Grained Provenance (Best Practice):**
>    - Committing extraction changes explicitly (e.g. `refactor: extract devlog from URI note`) makes intent unambiguous.
>    - Adding a footer/backlink like `extracted-from: [[linking to git commits and diffs in obsidian via uri]]` allows instant static link traversal without needing to run `git log -C`.

---

## Related Notes
- [[history]] — Central MOC indexing line-level provenance alongside Git history workflows and temporal integrity.
- [[link to git historic notes devlog]] — The concrete extracted note tested in this experiment: verified with `git blame -C` that human vs AI lines survived extraction.
- [[linking to git commits and diffs in obsidian via uri]] — The original source note from which the devlog content was extracted.
- [[how to keep history]] — The cross-repository counterpart: explains how to transfer Git history when an extracted note is moved across submodule boundaries.
- [[wikilink temporal integrity]] — Complements line provenance by ensuring links created during the extraction maintain their contextual snapshot meaning.



