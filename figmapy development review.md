Looking back 2 years later, I would do some things different. Let's review.
### Summary
I *finished* figmapy and released it. There were a few polish bits here and there that'd be nice to add, but overall it was pretty complete for a first pass.
So what went wrong?

Figma often updated their API, so figmapy broke, and I had to update it.
The way the code was implemented using inheritance, made this nice to use, but hard to update. So updating the code ended up being too time consuming, and I gave up keeping it updated.

### Overview
Adding extra keys in the returned json, which then need to be added as a supported kwarg.
having to manually update the figmapy module regularly is time consuming. 

- I spent a lot of time adding kwargs to methods. 
  .. and to the inherited methods.
  ... and their inherited methods.
  Mainly because i wanted [[autocomplete]] to work.
  Given the time cost for keeping the methods updated, next time I'll use [[args and kwargs]].
	- It might still be possible to also support a nice way to get possible kwargs, by creating a single place that stores all these vars. 
- A more basic approach could be to keep it text driven.
- Next time I might dynamically create attributes based on the returned dictionary keys, instead of recreate them all myself in a python class. This might reduce [[autocomplete]] support in your [[integrated development environment|IDE]]. 
	- This might be handled by [[stubbing]].

Since inheritance was a time sink, i wonder if this could help. [[composition vs inheritance]]

**Versioning**
It'd be great to read the figma API version, and have backward support for older versions. e.g match the version of figmapy on pypi with the figma API version.

[[my progamming review]]