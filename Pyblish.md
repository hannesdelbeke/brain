Pyblish let's you create content pipelines, and is aimed at VFX & games.
It's a plugin based system, that's [[dcc independent]], so you can use the same pipeline in different apps, such as [[Autodesk 3ds Max|max]], ,maya, [[Blender]], substance, …

It's great especially for [[validation]], so artists can run the tool and it will tell them what's wrong with their file.

Pyblish is created around the concept of plugins:
- collector plugins collect instances, which are saved in the context
	  (e.g. collect meshes) 
	  [[why use instance collection in validation]]
- validator plugins validate instances
	  (e.g. the mesh has no n-gons)
- extraction plugins export instances
	  (e.g. export the mesh from dcc to disk)
- integration plugins handle various integrations
	  (e.g. update Jira or the CMS for the mesh) 

The plugin workflow is very powerful, allowing for the creation of a more modular pipeline. Whereas the traditional gamedev pipeline is often unique for each studio and [[hardcoded]] to the project, making it hard to reuse.

## Limitations
- Pyblish has it's root in the VFX industry, so some parts make less sense for gamedev.
- It's maintained by only 1 person, Marcus. Who's not actively working on it anymore.
- My studies on the limits of Pyblish: [[Pyblish issues]]

## my notes
- proposed feature: 
	- [[Pyblish marketplace]]
	- adaptors