## Vision
Imagine a preset to take apps with you when swapping pc.
Or an account that lists your favorite apps for quick installation.

Similar to the UX from chrome, [[Chrome remembers extensions]]

## Existing solutions
Winget has [export] which covers some of these needs. It exports a JSON file of **ALL** installed apps.
Afterwards you can edit the JSON. => Not much control
The JSON can be loaded by the [import] command to install all apps.

#toolidea #cloud

[export]: https://learn.microsoft.com/en-us/windows/package-manager/winget/export
[import]: https://learn.microsoft.com/en-us/windows/package-manager/winget/import