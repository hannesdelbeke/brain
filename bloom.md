Bloom is a post-processing effect to make things glow, usually combined with [[high dynamic range|HDR]].


### Bloom & tone mapping
Since post-pro effect order is important, don't use tone mapping before bloom.
Bloom should only affect colors more intense than white (higher than 255 RGB, or 100% or 1 ). 
But if you tone map before bloom, all colors will be capped at 1, resulting in bloom not having a HDR input anymore.
Often people then lower the bloom threshold to e.g. 0.9, to create a fake bloom, which won't look as good.

ref image 
[![400][https://i.imgur.com/nSRGzEo.jpg]]