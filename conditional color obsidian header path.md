If I open a note, the header at the top of the tab contains the path, e.g.
`Public/my note`
`Private/my personal note`

I want to CSS color the path, based on if it contains text, to make it clear if a note is public.

# step 1

CSS snippets let me color it, but now it always colors.
```CSS
.view-header-title-container .view-header-breadcrumb:first-child {
  color: orange;
}
```

<font color="orange"> Public </font> / my note
<font color="orange"> Private </font> / my personal note

# step 2
use the `javascript init` plugin to run javascript code on Obsidian startup.
this works, but our custom javascript code doesn't work yet

```javascript
document.addEventListener("DOMContentLoaded", function() {
  var breadcrumb = document.querySelector('.view-header-breadcrumb');
  var title = document.querySelector('.view-header-title');

  if (breadcrumb && breadcrumb.innerText.includes("public")) {
    title.classList.add('dark-green-background');
  }
});
```


[[Obsidian]]
[[UX]]
[[Obsidian improvements]]