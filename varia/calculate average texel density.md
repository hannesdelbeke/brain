The average [[texel density]] is a single value representing the model's overall texel  density.

To calculate it:

- Calculate the mesh triangle surface areas.

- **Map Textures to Surfaces**: Identify how textures are mapped to the surfaces. Textures are often UV-mapped, and you'll need to find the UV coordinates for each triangle or polygon to understand how textures are applied to the model.
    
- **Calculate texel density**: 
  Calculate on a per-triangle or per-surface basis. `pixels / cm`
  the ratio of the texture resolution (in pixels) to the surface area (in square units).

- **Average texel density:** 
Take the mean of all the texel densities for all surfaces in the model. 
