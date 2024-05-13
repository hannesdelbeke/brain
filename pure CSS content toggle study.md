
A study on how mkdocs theme toggles a menu without JavaScript
context: if we click the Folder22 label, it opens and shows all labels for the files inside

## Learnings

`.md-nav__toggle` contains checked state
`.md-nav` comes after toggle

```CSS
/* hide the nav that comes after the checkbox, when checkbox is toggled */
.md-nav__toggle:checked~.md-nav{
	display: none;
}
```

## Study

```HTML
<!-- parent elements for reference -->
<nav aria-label="Navigation" class="md-nav md-nav--primary" data-md-level="0">
<ul class="md-nav__list">

<!-- this contains both the parent & child element-->
<li class="md-nav__item md-nav__item--nested">

    [<!-- make a toggle checkbox to control '__nav_6' 
      the previous sibling element is named '__nav_5' -->
    <input class="md-nav__toggle md-toggle" 
    data-md-toggle="__nav_6" id="__nav_6" type="checkbox">
    
    <!-- make a parent label that'll be triggered by the checkbox  -->
    <label class="md-nav__link" for="__nav_6"> <!-- 'for' is an attribute -->
        Folder22
        
        <!-- put an icon in the label, so that it's on the same line,
        and inherits the wrapping/layout -->
        <span class="md-nav__icon md-icon">
        </span>
        
    </label>
    
    <!-- make a child label that shows when clicking the parent -->
    <nav class="md-nav" data-md-level="1">
        <!-- An _unordered list_ starts with the <_ul_> tag -->
        <ul class="md-nav__list">
            <!-- Each list item starts with the <li> tag -->
            <li class="md-nav__item"> 
                <a class="md-nav__link" title="Test2"
                href="http://127.0.0.1:8000/wiki/folder22/test2/">
                    Test2
                </a>
            </li>
        </ul>
    </nav>
</li>
```

`~` is the [[subsequent-sibling combinator]]

```CSS
/* note the ~ */
.md-nav--primary .md-nav__title .md-nav__icon, .md-nav__toggle~.md-nav {
    display: none;
}

/* with ~ we select the nav, after the toggle*/
.md-nav__toggle:checked~.md-nav, .md-nav__toggle:indeterminate~.md-nav {
    display: block;
}
```

**Notes**
- note it uses [[BEM naming convention]]
- md toggle comes from mkdocs, md -> makedocs
- every toggle needs a unique id!

nav icon rotate and hover
```CSS
.md-nav__icon{
	border-radius:100%;
	height:.9rem;
	transition:background-color .25s,transform .25s;
	width:.9rem
}
/* dir is used for directionality of the language 
default we set it rotated to language direction, 
then when 'checked' we rotate it to 0 degrees */
[dir=rtl] .md-nav__icon{
	transform:rotate(180deg)
}
.md-nav__icon:hover{
	background-color:var(--md-accent-fg-color--transparent)
}
/* after inserts text after the element 
done in CSS (instead of HTML) so it's easy to customize */
.md-nav__icon:after{ 
	background-color:currentcolor;
	content:"";
	display:inline-block;
	height:100%;
	-webkit-mask-image:var(--md-nav-icon--next);
	mask-image:var(--md-nav-icon--next);
	-webkit-mask-position:center;
	mask-position:center;
	-webkit-mask-repeat:no-repeat;
	mask-repeat:no-repeat;
	-webkit-mask-size:contain;
	mask-size:contain;
	vertical-align:-.1rem;
	width:100%
}
```

[[CSS]]
