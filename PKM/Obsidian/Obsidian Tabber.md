Tabbers are great for e.g. showing the same code in different languages.
![[Obsidian Tabber-1674600128447.jpeg|150]]

Proposal for Obsidian #pluginidea 
> [!info]+ Tabber proposal
> - markdown friendly
> - still renders nicely when plugin not installed
> 
> > [!TABBER]+
> > > [!TAB]+ tab1 title
> > > Contents tab 1
> > 
> > > [!TAB]- tab2 title
> > > Contents tab 2
> > 
> > > [!TAB]- tab3 title
> > > Contents tab 3
> 
> code:
> ```
> > [!TABBER]+
> > > [!TAB]+ tab1 title
> > > Contents tab 1
> > 
> > > [!TAB]- tab2 title
> > > Contents tab 2
> > 
> > > [!TAB]- tab3 title
> > > Contents tab 3
> ```
> TODO: render tabs in Obsidian preview & HTML publishing
![[Obsidian Tabber-1674601442427.jpeg]]

[discussion](https://forum.obsidian.md/t/tabber-plugin/53054) in Obsidian  forum

### Steps for nice UX in Obsidian
- [ ] plugin to preview tabs in Obsidian 
	⚠️ GREAT [reference](https://marcus.se.net/obsidian-plugin-docs/editor/markdown-post-processing) on editing HTML with markdown post processor.
	[reference](https://publish.obsidian.md/hub/02+-+Community+Expansions/02.01+Plugins+by+Category/Plugins+with+custom+views) of plugins that alter view 
- [ ] publish to mkdocs
	- [ ] since mkdocs already supports tabbers, we can write a convertor, see [docs](https://python-markdown.github.io/extensions/api/)
	- [ ] then on MkDocs build, ensure we use the settings from [material docs](https://squidfunk.github.io/mkdocs-material/reference/content-tabs/)

## Other tab solutions

### MkDocs content tabs
https://squidfunk.github.io/mkdocs-material/reference/content-tabs/
mkdocs already supports a tabber! it looks bad in [[Obsidian]] though
https://facelessuser.github.io/pymdown-extensions/extensions/tabbed/
```
=== "Tab 1"
    Markdown **content**.

    Multiple paragraphs.

=== "Tab 2"
    More Markdown **content**.

    - list item a
    - list item b
```

> [!mkdocs tabber format in Obsidian]-
> === "Tab 1"
>     Markdown **content**.
> 
>     Multiple paragraphs.
> 
> === "Tab 2"
>     More Markdown **content**.
> 
>     - list item a
>     - list item b

### tabber CSS hack in Obsidian
- someone made a hacky tabber solution for Obsidian
  mixing HTML in the text, and using CSS to render the tabs.
  - requires to much manual knowledge and typing
  - doesn't read well without plugin

### R markdown
- r markdown supports `tabsets`, see [docs](https://bookdown.org/yihui/rmarkdown-cookbook/html-tabs.html)
  it uses headers for this, doesn't render nicely without plugin

### MediaWiki tabber plugin

> [!NOTE]- mediawiki [TabberNeue](https://m.mediawiki.org/wiki/Extension:TabberNeue)
> ```
> \<tabber>
> |-|First Tab Title=
> First tab content goes here.
> |-|Second Tab Title=
> Second tab content goes here.
> |-|Third Tab Title=
> Third tab content goes here.
> \</tabber>
> ```
> small bug in obsidian requires \ in front of tabber to render

### HTML tabs
tabber in HTML [source](https://www.w3schools.com/howto/howto_js_tabs.asp)
also option for pure CSS with radio-buttons



