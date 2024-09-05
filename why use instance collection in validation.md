Why do we use instance collection in validation?
Why not just do a simple validation test like this?
```python
# pseudocode
def validate_mesh_tri_count(tri_limit=200):
    meshes = pm.ls(type="meshes")
    for m in meshes:
	    if m.tris > tri_limit:
		    raise Exception
```

limitations:
- it fails on the first mesh that fails. so will only list 1 issue instead of multiple issues.
  Often it makes more sense to get a report of everything that's wrong.
- it only runs on all meshes. if you want to run it on a custom input, you need a second method to "collect" the meshes and pass them as a kwarg.
  What if we only want to validate the character meshes in the scene, but not the collision mesh?

Using a collector is more flexible, and lets you reuse the same piece of code without having to rewrite it.