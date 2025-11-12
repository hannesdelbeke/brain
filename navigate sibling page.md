## The concept
Andy's note [It’s hard to navigate to unlinked “neighbors” in associative note systems](https://notes.andymatuschak.org/zT6iA52811NuLvbU9W8ixeDc3KUqyCT1wN8) would be address with buttons to go to sibling notes.

The most basic implementation is 
- put notes in a folder
- use `< Previous` and `Next >` links to navigate between the notes.

MkDocs material supports this, see [navigation](https://squidfunk.github.io/mkdocs-material/setup/setting-up-the-footer/#navigation)
MkDocs auto falls back on [[folder structure]].
>The [nav](https://www.mkdocs.org/user-guide/configuration/#nav) configuration setting in your `mkdocs.yml` file defines which pages are included in the global site navigation menu as well as the structure of that menu. If not provided, the navigation will be automatically created by discovering all the Markdown files in the [documentation directory](https://www.mkdocs.org/user-guide/configuration/#docs_dir).

The mkdocs material theme  [describes](https://squidfunk.github.io/mkdocs-material/setup/setting-up-navigation/) some other great navigation concepts

### Disadvantage
- Less minimalistic UI
- Might link unrelated notes in a flat hierarchy setup, popular in the Zettelkasten community.
- maintaining a nav file wastes time if not automated

[[navigation]]
[[browser]]
[[UX]]
[[personal knowledge management|PKM]]