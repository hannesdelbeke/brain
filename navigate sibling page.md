## The concept
Andy's note [It’s hard to navigate to unlinked “neighbors” in associative note systems](https://notes.andymatuschak.org/zT6iA52811NuLvbU9W8ixeDc3KUqyCT1wN8) would be address with buttons to go to sibling notes.

The most basic implantation is 
- put notes in a folder
- use `< Previous` and `Next >` to navigate between the notes.

MkDocs material supports this, see [navigation](https://squidfunk.github.io/mkdocs-material/setup/setting-up-the-footer/#navigation)
MkDocs auto falls back on folder structure.
>The [nav](https://www.mkdocs.org/user-guide/configuration/#nav) configuration setting in your `mkdocs.yml` file defines which pages are included in the global site navigation menu as well as the structure of that menu. If not provided, the navigation will be automatically created by discovering all the Markdown files in the [documentation directory](https://www.mkdocs.org/user-guide/configuration/#docs_dir).

The mkdocs material theme  [describes](https://squidfunk.github.io/mkdocs-material/setup/setting-up-navigation/) some other great navigation concepts

### Disadvantage
- Less minimalistic UI
- Might link unrelated notes in a flat hierarchy setup, popular in the Zettelkasten community.
- maintaining a nav file wastes time if not automated

## Obsidian plugin ✅

> [!Question]- Obsidian navigate plugin
> - Next & Previous visual button.
> - customizable next & previous, visualized at the bottom (or top?) of the note.
>   e.g. define `nav-next` & `nav-previous` in the frontmatter
>   use folder hierarchy as default.
>   ![[navigate sibling page-1674170180221.jpeg]]
>   Created a [forum thread](https://forum.obsidian.md/t/navigate-sibling-page-previous-next/52701) to discuss this plugin idea
>   
>   the [2hoplink](https://github.com/tokuhirom/obsidian-2hop-links-plugin) plugin can be used as reference, since it adds page-links at bottom of file.
>   
>   
> ## Solution
> the author from quick explorer got back to me and provided a solution.
> 
> 1. install the plugins
> -   [quick explorer](https://github.com/pjeby/quick-explorer) - for previous & next command
> -   [commander](https://github.com/phibr0/obsidian-commander) - for adding command buttons
> 
> 2. On hovering the top bar, a button appears to add custom command buttons.
>    - Add the previous file & next file commands.
>    - For icon use double left `<<` & double right arrow  `>>`

> [!reference]- 
> - in-depth [discussion](https://forum.obsidian.md/t/daily-notes-next-previous/4573/13) on a previous and next button in the daily notes plugin, and workarounds with templates.
> - short [thread](https://forum.obsidian.md/t/automatic-next-and-previous-sibling-for-breadcrumbs/40469), repeating the same
>   It [mentions](https://breadcrumbs-wiki.onrender.com/docs/Alternative%20Hierarchies/Hierarchy%20Notes) the same concept exists for breadcrumbs too.
> - there are default Obsidian commands for `Open next daily note` and `Open previous daily note`, but no buttons. there [used to be](https://forum.obsidian.md/t/daily-notes-next-and-previous-fail-when-using-folder-in-template/27623), not sure where this is
> - [thread](https://forum.obsidian.md/t/is-there-a-shortcut-for-opening-next-note/23812/2) requesting hotkeys for this feature
> - popular [thread](https://forum.obsidian.md/t/iterate-through-files-in-the-file-sidebar-with-keyboard/629/60) requesting this
> - [quick explorer](https://github.com/pjeby/quick-explorer) plugin adds hotkeys for this feature. But no visual preview.

#PKM #UX #browser #navigation

[[Obsidian plugin]]