To save arbitrary data to a [[Autodesk Maya|Maya]] scene so it persists between sessions.
`cmds.fileInfo` can do simple data. My recommendation is `json` if you need anything with a structure, and `base64` it because `cmds.fileInfo` is annoying about quoting and likes to add `\\` 

Otherwise you're looking at doing something hacky like hiding an attribute on the time node

source: Bob White

[[Maya Python]]