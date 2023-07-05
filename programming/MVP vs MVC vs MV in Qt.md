[[MVP example]]
[[MVC python example]]
[[MVP python example]]
[[MVP py sample function]]


in qt, the ui file can be seen as the view. But so can the resources file, the qss (stylesheet) and even the widget.
The widget starts to hookup the UX
Ideally logic lives outside the widget. 

The model always needs a interface.
- **MV** With model view, the logic is hooked up in the widget.
	- things are kept pretty simple. you save yourself time.
	- harder to swap out view, but this rarely is needed IMO. 
- [[model view presenter|MVP]] with model view presenter, the presenter hooks up the widget with the model. all interactions between model and view go through the presenter.
	- the view needs an agreed interface, if this changes the presenter needs updating.
	- more complexity, and slower development
- **MVC** with model view controller, the controller passes the whole model to the view. And the view has direct access to the model. e.g. `self.model`

After reading  [[A Philosophy of Software Design]], I now gravitate more towards MV due to lower complexity. 
The only advantage MVP and MVC  is that the view can run on it's own, without functions hooked up. Nice to develop the view, but harder to develop the tool as a whole. Swapping out the view is something I've never found I needed.
- Updating 1 method in 2 different files creates inconsistencies 
- Empty functions that need to be inherited, are not intuitive.
see [[connascence]] which discusses code complexity.
Instead we can write just a simple widget. And have just the logic separate.

- [ ] todo, add examples of struggles in real life

## reference
A Python [[MVP example]]