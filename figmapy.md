a python module to access [[Figma]]

became a maintainer after rewriting nearly the whole repo
still could use some more work, and every update from figma it tends to break since they add a new type of node.
- [ ] add unit testing
- [ ] add unknown node type support

## review
Figma often updated their API. 
Adding extra keys in the returned json, which then need to be added as a supported kwarg.
having to manually update the figmapy module regularly is time consuming. 

I wonder if next time i would go for a more basic approach where it works text driven. instead of [[object oriented programming|object oriented]].
Or dynamically create attributes based on the returned dictionary keys.

It also would be great to read the version of the figma API, and warn the user when figmapy is outdated and might not work correctly.
[[my progamming review]]