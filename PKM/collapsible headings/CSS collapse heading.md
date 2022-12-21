based on the [[pure CSS content toggle study]]

`.md-ch-heading__toggle` contains checked state
`.md-ch-heading-content` comes after toggle
- [ ] How is checked state passed by clicking the icon?

```CSS
/* hide the nav that comes after the checkbox, when checkbox is toggled */
.md-nav__toggle:checked~.md-nav{
	display: initial; /* reset to default value */
}
```

we can reuse the nav icon
```HTML
<span class="md-nav__icon md-icon">	</span>
```

- [ ] rename md-ch-heading-toggle to md-ch-heading__toggle
- [ ] rename md-ch-heading-content 

current CSS
```HTML
<!-- heading1 -->
<input class_="md-ch-heading-toggle" type="checkbox">
<h2 id="h1">h1</h2>
<div class_="md-ch-heading-content">
   <p>test content text test content 1 </p>
   
   <!-- heading2 -->
   <input class_="md-ch-heading-toggle" type="checkbox">
   <h3 id="h2">h2</h3>
   <div class_="md-ch-heading-content">
      <p>test content test sdfvsd</p>
      
      <!-- heading3 -->
      <input class_="md-ch-heading-toggle" type="checkbox">
      <h4 id="h3">h3</h4>
      <div class_="md-ch-heading-content">
         <p>test content test </p>
      </div>
   </div>
</div>
```