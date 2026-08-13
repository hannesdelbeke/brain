---
sentiment:
- 5
sentiment-hash: 63b2ba06
sentiment-label:
- factual
tags:
- technical
- work
---

To have local [[Unity tool]]s in your project, it needs to be an editor tool in your assets folder.
Packages are not supported because it creates [[Unity local manifest issue|a conflict in the project's package manifest]]

This setup assumes you use [[git]], and creates a local folder that is ignored by git to store your tools in. Other [[version control]] software (e.g. [[Perforce]]) should also support ignore files.
```
📂 _gitignore
  📄 .gitignore
  📂 editor
    📂 tool1
    📂 tool2
```

1. create a folder named `_gitignore`
2. inside the folder
	1. add a textfile named `.gitignore` with content `*`
	2. create a `editor` folder inside
3. place your editor tools in the `editor` folder
