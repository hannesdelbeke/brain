#### Pyblish inconsistent logic
Some of the core logic is flawed IMO:
 - actions are not directly aware of the plugins/instances they belong too
 - no option to swap between warning or error on failure. they use different systems.
	
- aims to be data driven instead of explicit. 
	  *so relevant logic is run based on correct input, 
	  e.g. run the mesh validation when a mesh is detected*
  but instead it does both sometimes.
	  *e.g. deregister [[Pyblish default plugins]] is explicit, overal plugin registration is implicit.*

[[Pyblish warning vs error]]
warning and error are 2 different types of data. no easy way to swap a task from soft to hard fail.
warning lives in the log, error is an exception.