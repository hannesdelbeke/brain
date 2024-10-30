let's take this [package.json](https://github.com/garettbass/UnityExtensions.SelectionHistory/blob/master/package.json)
with this github URL https://github.com/garettbass/UnityExtensions.SelectionHistory

to install this package in unity.
- open the Package Manager
- click the Plus at the top left
- add package from GIT url (and add `.git` to the url)
- click install

> [!ERROR] 
> The error `package ... name is invalid` will prevent a successful package install.
> Append `.git` to the git url to fix this.
> ```
> [Package Manager Window] Error adding package: https://github.com/garettbass/UnityExtensions.SelectionHistory.
Unable to add package [https://github.com/garettbass/UnityExtensions.SelectionHistory]:
  Package name 'https://github.com/garettbass/UnityExtensions.SelectionHistory' is invalid.
UnityEditor.EditorApplication:Internal_CallUpdateFunctions ()
> ```

official [docs](https://docs.unity3d.com/Manual/upm-ui-giturl.html) on adding package from git
