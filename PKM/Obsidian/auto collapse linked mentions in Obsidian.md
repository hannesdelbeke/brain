## Problem
When you open [[Obsidian]], `linked mentions` aren't auto collapsed. Making them harder to read. 
## Workaround
### CSS workaround hack ✅
I'm using this workaround.
CSS to always collapse linked mentions.
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
cons:  you can’t expand anymore
source [original forum post](https://forum.obsidian.md/t/retain-remember-status-of-backlinks-in-document/20341/39), my [reply](https://forum.obsidian.md/t/retain-remember-status-of-backlinks-in-document/20341/44)
### 3rd party plugin
untested
- [forum posts](https://forum.obsidian.md/t/how-do-i-automatically-collapse-linked-mentions/70973/4) suggests to install a experimental plugin
https://github.com/nothingislost/obsidian-query-control
### Links
forum posts requesting this feature
- [20341](https://forum.obsidian.md/t/retain-remember-status-of-backlinks-in-document/20341)  
- [7487](https://forum.obsidian.md/t/add-option-to-collapse-backlinks-and-search-results-by-default/7487)
- [49136](https://forum.obsidian.md/t/dont-automatically-expand-linked-mentions-at-bottom/49136)