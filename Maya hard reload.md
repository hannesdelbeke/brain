https://github.com/csaez/hard_reload
hard_reload is a neat little widget, to delete python module from memory, so they can be cleanly re-imported.
`importlib.reload` doesn't always does it as cleanly.
## pros
- works in Maya out of the box
## cons
- It doesn't handle dependencies, 
- you have to manually reload every module. this might be a pain if you have complex packages with multiple modules.  A workaround: reload all modules containing a unique word that identifies your modules.

[[python reload]]
[[Maya Python]]