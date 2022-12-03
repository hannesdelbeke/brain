An element takes up space (width & height)
The [display](https://www.w3schools.com/cssref/pr_class_display.php) decides if the next element is shown on the same line, or a new one.
e.g. to draw an element next to another without taking up any space

```html
<style>
.testclass {
  float: left;
  position: relative;
  display: inline;
  width:0;
  left:-10px;
}
</style>

<body>
<div class="testclass">
  <button onclick="myFunction()" class="btn">Button</button>
</div><p>testtesttesttest</p>
<body>
```

[[web development]]
[[HTML]] [[CSS]] 