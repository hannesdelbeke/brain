repo https://github.com/hannesdelbeke/blender-pyflow
mentioned this on blender artists node [thread](https://blenderartists.org/t/unreal-blueprints-houdini-nodes-in-blender/1484937/3)

# Goal
i want to add [[PyFlow]] support as a Blender addon
- Why do i want node base editor in Blender?

> [!WARNING] on hold
>   Since I don't have a strong answer for this I'll put this R&D on hold.
>   Best use case likely is marketing. users love this shit.
>   could use this to sell the idea of [[plugget]]. download nodes on a marketplace
>   
>   in combination with [[plugget]], a user can download some nodes. and e.g. run validation node on a mesh. set up a quick and simple pipeline.
  The idea of a universal node graph is cool. But what really matters is [[environment management]] and [[validation]]

### workflow
how i imagine users would use this.
1. open the node editor from the menu `window/pyflow node editor`
2. create a node graph, or load a demo
3. click run
### features
- open editor
- run node network
- run node network from CLI
- see output of node network on fail
	- create a sphere with position
	  8/3 8/2 8/1 8/0->error  8/-1 8/-2 
	  divide by 0 exception
	- show case where we "warn", node execution continues
	- show case where we "fail" node execution stops
### demos
include demos with the project to show off features:
- create a grid of cubes
- create a circle with a timer, that creates spheres in a circle in x seconds.
- run a custom piece of code/addon

# Progress
- [x] launch pyflow in blender
- [x] add nodes
	right click in the canvas, a node context menu pops up. drag and drop nodes in the canvas to place them.
- [x] learn how to control flow
	i can create a `timer` node, and hook it up to `console output` node
	select the `timer` node and the `properties` panel will show execute buttons. Click start to start the timer, and stop to stop it. it prints `None` every second in Blender's console.
	the `doOnce` node is similar, and executes once when clicking the button.
	![[Blender PyFlow-1725710300844.jpeg]]
	
> [!NOTE] delta time issue
> Delta time seems to not work well. e.g. when set to 0.1, it doesn't print every 0.1 sec. Timing is also irregular. sometimes slow, sometimes fast. 
> likely a Qt / Blender timer hookup issue. running without bqt atm.

- [x] learn how to make custom node
	made a custom node [createBlenderCube](https://github.com/hannesdelbeke/blender-pyflow/blob/main/createBlenderCube.py) that creates a cube in Blender
	couldn't figure out how to easily do multi input slots for e.g. positions (int, int, int)
	default nodes are manually hooked up in `PyFlow\Packages\PyFlowBase\__init__.py`
	- [x] node to create cube
	- [ ] node to set position

> [!NOTE] divide by 0 issue
>  when dividing by 0, there is no visual feedback. only an exception in the console. and output of a divide by 0 node is 0, which is wrong.

overall i m not as impressed as I expected I'd be.
- The UI is great, but learning how to make a node is complex.
- documentation is rough
- the UI UX flow is also quite rough. e.g. creating a new node is not as fluent as in Unreal.
- CLI is not a first class citizen. user is expected to create nodegraphs in the editor.

# Notes
- [Serpens](https://blendermarket.com/products/serpens?ref=94) is a paid addon that does this already