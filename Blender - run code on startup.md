run code on [[Blender]] [[startup]]

- Cleanest way is to wrap your code in a [[Blender addon]], and run the startup code on addon load. Then enable addon to load on startup
- register a text block, to load code when you load a blend file
- copy into the Blender install directory `scripts/startup/` folder, and it will run on Blender startup

[[Blender scripting]]
