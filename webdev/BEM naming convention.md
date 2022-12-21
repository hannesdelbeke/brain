CSS & HTML classes use the BEM convention for their naming convention 
This blog [1] explains it well

## BEM convention

B block
```CSS
.stick-man {}
```

E element
```CSS
.stick-man__arms {}
```

M modifier
```CSS
.stick-man--green {}
```

combined:
```CSS
.stick-man__arms--green {}
```

These are all class names for an HTML element
```HTML
<div class="stick-man__arms--green js-site-navigation">
```

## Renaming breaks JavaScript 

To prevent the site breaking when renaming classes without knowing you have to rename in JavaScript , explicitly start class names with `js-*` if referenced in JavaScript.

[[A Philosophy of Software Design]]: Non explicit references can lead to complex code

%% #todo better quoting once [[A Philosophy of Software Design]] page has a summary%% 

```HTML
<div class="site-navigation js-site-navigation"></div>
```

```JavaScript
const nav = document.querySelector('.js-site-navigation')
```

## Spaces in class name
A class name **can’t** have spaces. A space-separated string in your `class` attribute, gives your element _several_ classes.


#CSS #naming-convention #HTML

[1]: https://www.freecodecamp.org/news/css-naming-conventions-that-will-save-you-hours-of-debugging-35cea737d849