[[validation pipeline with pytest]]
## best practices
avoid changing node code to make nodes more reusable
nodes are like imports, you use them but you don't change the imported code
## common exercises and problems a good pipeline should handle
- can run headless.
- if it can run headless, we can run it with GUI and get result at end
- better if we can get results while it's running, see which node failed
  same as traceback
  e.g. validate if tri count is > 5000
- plugin architecture for everything, so you can add validations per team or project.

- i can see what validations ran on a certain input
- i can see which validations failed on an input

WORKFLOW
- option to run validations on same input, e.g. collect meshes
  this avoids running validations accidentally on different input, and duplicate code.
  this could be avoided by doing import my_collect method and only run that.
  but if you ever want to change the input you ll have to change the code in all your validations. 
  (see [[why use instance collection in validation]])
- option to tweak settings (also form of input)
 - load presets. serialize and serialize your pipelines to support different workflows.
 - allow sub workflows, and if visualized these are sub groups or nodes.
   this lets you split your workflows into smaller chunks making them more reusable across projects.
- the order of validation actions can be controlled. e.g. first i want to run A, then B.
  or first i want to run B, then A.
- the order can be controlled in the pipeline config. 
  this allows you to reuse validation plugins in different workflows without having to edit their code. e.g. pyblish sets the order in the plugin itself. collect validate ...
- control if a node is allowed to fail or should throw a warning,without changing node code
  e.g. mesh name starts with capital
  wrapper around pyblish node?

POLISH
- lazy loading
  e.g, when inspecting the node flow outside maya, importing maya.cmds outside of maya results in exceptions which lazy loading could prevent.
  separate the "check" or "node" meta data (name, validation type e.g. mesh, ...) 
  from the functionality (that imports maya)
- ensure if you collect and then validate, the input (e.g. meshes in scene) hasn't changed.
  This could happen if you edit the scene. e.g. your run a fix during a validation workflow, which results in the mesh count being changed during a mesh iter loop.
- can run a validation and it's collector, without running all collectors.
  custom input gives more flexibility. the user can check just 1 mesh instead of all meshes.

create a unit test framework around the gym

[[pipeline as code]]
[[Pyblish issues]]
[[sample pipeline node view.canvas|sample pipeline node view]]
[[validation]]