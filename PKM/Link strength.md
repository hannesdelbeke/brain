some links are loose, others are close.

e.g. 2 tools, sharing various concepts and libraries are closely related.
2 tools, that are used together in a workflow but share no underlying tech are less related
```mermaid
graph LR;
    Validator1 --> Validator2;
    Validator1 --> Maya
    Validator2 --> Blender
    Validator1 --> Pyblish
    Validator2 --> Pyblish
    Maya --> dcc
    Blender --> dcc
```

#link