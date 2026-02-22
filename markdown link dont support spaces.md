---
views: 8
---
Markdown links don't support spaces in Obsidian.

## Example
This link `[Blender pip Qt addon](Blender pip Qt addon.md)`
Opens the `Blender.md` file instead, because there is a space in the link.

## Workarounds

> [!fail]
> escape space characters doesn't work in Obsidian
> `[Obsidian - one way wikilinks](<Obsidian\ -\ one\ way\ wikilinks.md>)`
> it creates a new note `wikilinks.md`
> 

> [!success]
> this works
> `[Obsidian - one way wikilinks](Obsidian%20-%20one%20way%20wikilinks.md)`
> [Obsidian - one way wikilinks](Obsidian%20-%20one%20way%20wikilinks.md)

> [!success]
> Wrapping the link target in angle brackets works.
> `[Obsidian - one way wikilinks](<Obsidian - one way wikilinks.md>)`
> [Obsidian - one way wikilinks](<Obsidian - one way wikilinks.md>)
> `[Obsidian - one way wikilinks](<Obsidian - one way wikilinks>)`
> [Obsidian - one way wikilinks](<Obsidian - one way wikilinks>)
> 
> Angle brackets tell the parser to treat everything inside as a literal URL, including spaces.

- https://forum.obsidian.md/t/how-to-use-spaces-in-markdown-links/111489