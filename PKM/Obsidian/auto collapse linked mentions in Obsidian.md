## Problem
When you open [[Obsidian]], `linked mentions` aren't auto collapsed. Making them harder to read. 
## Workaround
### 3rd party plugin
- [forum posts](https://forum.obsidian.md/t/how-do-i-automatically-collapse-linked-mentions/70973/4) suggests to install a experimental plugin
https://github.com/nothingislost/obsidian-query-control
### CSS workaround hack
```CSS
/* backlinks in document - hide expanded parts */
.search-result-file-matches {
    display: None !important;
}

/* backlinks in document - keep the font color grayish instead of white */
.tree-item-self {
    color: var(--nav-item-color) !important;
}
```
#### CONS
- you can’t expand anymore
- arrows point down by default instead of to the right
source [forum post](https://forum.obsidian.md/t/retain-remember-status-of-backlinks-in-document/20341/39)
### Links
forum posts requesting this feature
- [20341](https://forum.obsidian.md/t/retain-remember-status-of-backlinks-in-document/20341)  
- [7487](https://forum.obsidian.md/t/add-option-to-collapse-backlinks-and-search-results-by-default/7487)