
gathering [[unpythonic]] [[pymel]] examples

below examples show
1. how Pymel does it
2. what IMO would be a more pythonic solution

```python
nt.Joint.getRotation()  # lots more attrs like that in joint
# instead of
nt.Joint.rotation 
```

```python
node.name() # not consistent, why not node.getName() like rotation?
# instead of
node.name
```

```python
# Query the influences for the skinCluster
pm.skinCluster('skinCluster1',query=True,inf=True)
# source
# instead of 
pm.findSkinCluster('skinCluster1')
# or 
mesh.skincluster() # can we have multiple skinclusters attached?
```

```python
pm.ls('GEO') # is not intuitive if you have no cmds background
# instead use
pm.getMesh()  # more descriptive and specific
# or
pm.getTransform()  # separates mesh from transform nodes
```

A function ideally returns something of 1 type not multiple types. (`Mesh` or `transform`), but `pm.ls` can return both types.

Also a hidden second versions of node can be returned. `returnIntermediate=False` by default

```python
pm.listRelatives(node) 
# instead of 
node.children 
# or 
node.parent
```



