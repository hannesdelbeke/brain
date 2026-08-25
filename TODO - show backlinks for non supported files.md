---
sentiment:
- 5
sentiment-hash: caa93928
sentiment-label:
- factual
tags:
- technical
- planning
- solved
---

How can I see [[Obsidian backlinks]] to non-supported files (e.g. [[xlsx]] files).

- a closed [forum post](https://forum.obsidian.md/t/showing-backlinks-to-non-markdown-files/18776/2)
- might be possible with data view or JQL plugin

[[Obsidian improvements]]
[[note linking duplicate source]]

## Answer

Obsidian has no backlinks pane for file types it cannot open. Confirmed on version 1.10.6 in a December 2025 [forum thread](https://forum.obsidian.md/t/attachment-file-types-that-cannot-be-viewed-in-obsidian-are-not-listed-in-the-attachments-folder-in-obsidian/108663): with `Detect all file extensions` on, clicking an xlsx launches the default app instead of opening a tab, so there is no active file for the backlinks pane to follow. The feature request sits in the forum's feature archive, answered with the line that Obsidian is a note-taker rather than a full text editor.

`Detect all file extensions` (Settings > Files and links) only makes such files visible in the file explorer. It does not change backlinks.

File types Obsidian can open do get backlinks. Images, PDFs, audio, video and canvas open in a tab and the backlinks pane follows them like a note. That covers every non-markdown file present in this vault: 27 jpeg, 11 svg, 3 gif, 1 pdf, plus python files under `skills/`. There is no xlsx, docx, pptx or zip in the vault, and the only non-markdown wikilinks are two pdf links and three to python scripts. The problem is hypothetical here.

Two substitutes work today.

- Obsidian search. Type the filename in the search pane and it lists every note containing it, as a link or as plain text. No plugin, no setup, any extension.
- A base. Bases is core since 1.9 and indexes every file in the vault including attachments, and exposes `file.backlinks` as an implicit file property. This gives a table that behaves like a backlinks pane for unsupported files.

[[obsidian-dataview]] is the weaker option. It indexes markdown pages only, so an xlsx is not a page it can resolve `FROM [[...]]` against and you fall back to filtering markdown notes on `file.outlinks`. A base does the same without a plugin. JQL is Jira's query language and does not apply.

The companion note idea in [[note linking duplicate source]] also covers it, at the cost of one note per file. That trade pays off when the file needs tags and a description anyway, not when the only question is what links to it.

## Plan

Set nothing up. There are no unsupported files in this vault, and search answers a one-off question in seconds.

For a one-off: open search and type the filename in quotes, for example `"budget.xlsx"`.

If it becomes recurring, create `attachments.base` in the vault root with this content and open it:

```yaml
filters:
  and:
    - 'file.ext != "md"'
formulas:
  backlinks: 'file.backlinks'
views:
  - type: table
    name: Attachments
    order:
      - file.name
      - file.ext
      - formula.backlinks
```

Each row is a non-markdown file and the backlinks column lists the notes linking to it. `file.backlinks` has to go in `formulas` because the base editor's property picker does not offer it. The docs mark it as performance heavy, so narrow the filter to one folder or one extension if the vault grows. Attachments have no frontmatter, so only implicit properties are available: `file.name`, `file.ext`, `file.size`, `file.ctime`, `file.mtime`, `file.folder`, `file.path`, `file.backlinks`. Adding `file.backlinks.length == 0` to the filter turns the same base into a list of unused attachments, the file version of [[link unlinked notes]].
