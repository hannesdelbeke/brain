- Morphs and bones can be combined, it's not just 1 or the other. E.g. bones for body, morphs for face
- If no further customization & deformation is needed, the deformation can be baked to the mesh.
- deciding when to use morphs or bones depends on the needed flexibility, performance, and quality. It can be different for movies, different games, or NPCs vs hero characters.
- bones blend between layers, morphs add layers 
## Bones = cluster animation
Tends to be heavier on the CPU, calculating more bone transforms
Lighter on GPU & memory
### Pros
- doesn't require 1-1 vert match, supports different models more easily
- better for sharing animations across a large number of unique characters
- rigs can be LODded for better performance
### cons
- less fine control, e.g. for mouth corners
- max bone count per vert might be higher than needed, resulting in performance loss
- Scaling bones can be bad practice, so you might not be able to "scale up" a mesh with bones unless you have a complex bone setup. e.g. a bigger belly requires multiple bones near the belly to be moved outwards 
- creating a rig is more complex than a morph
## Morph = vertex based animation
Tends to be heavier on the GPU & memory, storing more vertex data, and animating it on the GPU.
Lighter on the CPU
### Pros
- great for expressions & customizations
- allow full control in artist hand, so often used in animation e.g. Pixar
- great for different bodyshapes, e.g. a bigger belly
- creating a morph is easy, and can be done by the artist.

### Cons
- Don’t use morph targets for models that are a single shape for the whole body; amateurs love making that mistake.  This is a game engine, not a Disney Pixar production environment for offline rendering.
- requires 1-1 vert count match between source & target. so can't be reused between different meshes
- morfs need to be saved in the mesh, taking up more memory
- morfs can't be LODded, LODs would need their own morph

## Scenarios
- A crowd of 1000 people (meshes)
	1000 rigs and animations is more expensive, than a single vertex shader combining all 1000 people in 1 drawcall, with a prebaked animation in the morph.
- [Creating the Art of ABZU](https://www.youtube.com/watch?v=l9NX06mvp2E) uses rigs to animate, then bakes the animation to blendshapes for use in game. To avoid using rigs in game for better performance. A vertex shader animations the animals.

Deformation watch out for
- Doesn't always work nicely with LODs

- discussion [thread](https://forums.unrealengine.com/t/morphs-v-s-bones-for-facial-rigging/111257/8) 