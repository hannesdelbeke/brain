various solutions to run code on Maya [[startup]]
I recommend [[Maya plugin]] and ignore the rest.

- a [[Maya plugin]] can auto load on startup, which then runs the plugin code.
- a [[usersetup]] mel or python file auto loads on Maya startup, 
  it can live in the Maya installation folder, the Maya folder in your documents, or in a module
- [[Maya ApplicationPackage startup code]]
- [[pth]]
- [[Python run code on startup - sitecustomize and usercustomize]]
- [[Maya _load]] - [[Maya MEL|mel]] scripts that end in `_load.mel` run on startup 
- a [[Maya module]] can contain all the above solutions

other
- [[Maya modules vs plugins]]
### code
- `maya.utils.executeDeferred` defer running startup code
### tags
[[Maya Python]]
