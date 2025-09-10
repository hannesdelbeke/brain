---
aliases:
  - PDG
---
a [[Houdini]] file format that can be used in unreal

---

https://www.sidefx.com/products/houdini/pdg/

PDG is a procedural architecture designed to distribute tasks and manage dependencies to better scale, automate, and analyze content pipelines for Film, TV, Games, Advertising and VR.

PDG is designed to describe these dependencies visually using nodes that generate sets of actionable tasks then distributes them to multiple cores on the same machine, the compute farm, or even the cloud. PDG provides a rich set of stock nodes to enhance productivity, and manages the dependencies smartly to minimize recompute upon changes.

## Pipeline
[[Houdini]] and its node-based workflow is often referred to as a pipeline-in-a-box. With PDG, you can break this box wide open to scale up to a bigger procedural pipeline. PDG lets you organize and schedule tasks then distribute them intelligently to your compute farm to work in parallel.

# MANAGE
## Pipeline Dependencies
PDG can describe large parts of your pipeline to ensure that assets are being loaded, processed and saved out efficiently. 

The fine-grained dependencies can ensure a minimum of compute upon a given change. The [[Houdini Task Operators|TOP node]]s can play a number of different roles that will replace manual work and scripts that can bog down a complex studio pipeline. You can even set up TOP networks that fetch other TOP networks to create multiple levels of [[abstraction]] within your pipeline.

[[node editor]]

