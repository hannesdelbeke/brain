---
aliases:
  - IBM
---
The "inverse bind pose" undoes any transformation applied to your model in its bind pose.

Applying the identity matrix to every joint in the model resets the model to the bind pose.
> you can try this by sending a skeleton frame filled with identity matrices. If what results is the bind pose, then you are doing it right).

Don't apply the bind pose matrices (uninverted) to every joint in the model, this would be applying the bind pose twice!

[[matrix]]
[[rigging]]
[[bind pose]]