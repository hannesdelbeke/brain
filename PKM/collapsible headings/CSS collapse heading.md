based on the [[pure CSS content toggle study]]

`.md-ch-heading__toggle` contains checked state
`.md-ch-heading-content` comes after toggle
- [ ] How is checked state passed by clicking the icon?
	- likely CSS checked state?

test
 test
  

```CSS
/* hide the nav that comes after the checkbox, when checkbox is toggled */
.md-heading-toggle:checked~.md-ch-heading-content{
	display: initial; /* reset to default value */
}
```

we can reuse the nav icon, it should have default styling
```HTML
<span class="md-nav__icon md-icon">	</span>
```

- [ ] rename md-ch-heading-toggle to md-ch-heading__toggle
- [ ] rename md-ch-heading-content 

current CSS
```HTML
<!-- heading1 -->
<input class_="md-ch-heading-toggle" type="checkbox">
<h2 id="h1">
	h1
	<a class="headerlink" href="..test1b/#h1">¶</a>
</h2>
<div class_="md-ch-heading-content">
   <p>test content text test content 1 </p>
   
   <!-- heading2 -->
   <input class_="md-ch-heading-toggle" type="checkbox">
   <h3 id="h2">
        h2
	    <a class="headerlink" href="..#h2">¶</a>
	</h3>
   <div class_="md-ch-heading-content">
      <p>test content test sdfvsd</p>
      
      <!-- heading3 -->
      <input class_="md-ch-heading-toggle" type="checkbox">
      <h4 id="h3">
          h3
          <a class="headerlink" href="..test1b/#h3">¶</a>
	</h4>
      <div class_="md-ch-heading-content">
         <p>test content test </p>
      </div>
   </div>
</div>
```

we might be able to reuse headerlink, it auto hides when not hovering header
note that it doesn't work on the left side!

```HTML
<a class="headerlink" href="http://127.0.0.1:8000/wiki/folder1/test1b/#h1" title="Permanent link">¶</a>
```

FIX we can add a small offset to headings & content divs style from lists for 
- [x] wrap toggle in the header, before the text