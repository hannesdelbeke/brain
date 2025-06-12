You can also use CSS to always hide the collapsable part of linked mentions.
cons:  
- you can’t expand backlinks anymore
- search results are also affected!

Place a CSS file in your vault in  `/.obsidian/snippets`.
```CSS
/* backlinks in document - hide expanded parts */
.search-result-file-matches {
    display: None !important;
}
/* backlinks in document - keep the font color grayish instead of white */
.tree-item-self {
    color: var(--nav-item-color) !important;
}
/* hide all arrows, since collapsable arrows don't work anymore */
.search-results-children .tree-item-icon.collapse-icon {
  display: none;
}
```


source [original forum post](https://forum.obsidian.md/t/retain-remember-status-of-backlinks-in-document/20341/39), my [reply](https://forum.obsidian.md/t/retain-remember-status-of-backlinks-in-document/20341/44)