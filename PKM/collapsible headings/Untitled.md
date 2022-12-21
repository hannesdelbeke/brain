
`.md-ch-heading__toggle` contains checked state
`.md-ch-heading-content` comes after toggle

```CSS
/* hide the nav that comes after the checkbox, when checkbox is toggled */
.md-nav__toggle:checked~.md-nav{
	display: initial; /* reset to default value */
}
```

- [ ] rename md-ch-heading-toggle to md-ch-heading__toggle
- [ ] rename md-ch-heading-content 
- [ ] 