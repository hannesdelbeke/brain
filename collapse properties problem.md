
properties in obsidian add [[visual clutter]]
hiding them with a toggle resolves this.
Initial implementation with js collapses properties on opening a note.
`.obsidian/plugins/collapse-properties`

- [x] fixed flicker on open note
- [x] properties text label distracts from our note, replaced with icon
- [ ] maybe in future move this plugin to its own repo. 
      [[Amazon API Gateway|Sample note]] for screenshots.

> [!bug]- Collapse properties flicker
> ## Problem
> When opening a note, the Properties section briefly appears expanded and then collapses, causing a visible animation/flicker.
> 
> ## Cause
> The plugin collapsed Properties on `file-open`, but this happened after render, so the expanded state was visible for a moment.
> 
> ## Fix applied
> - Disabled Properties transition/animation in plugin CSS.
> - Temporarily hid expanded Properties during the collapse pass on `file-open`.
> - Removed the temporary hide class immediately after collapse.

### Links
- [forum discussion](https://forum.obsidian.md/t/add-setting-to-collapse-fold-properties-across-all-notes-by-default/67943/49) 
- alternative plugin:
	- https://community.obsidian.md/plugins/fold-properties
	- [github repo](https://github.com/itsonlyjames/obsidian-fold-properties)
	- [forum post](https://forum.obsidian.md/t/plugin-fold-unfold-properties-in-all-files/110715)
