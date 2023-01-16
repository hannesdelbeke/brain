Instead of toggle, we can use callouts in Obsidian.

### ✅ Callouts
see the [docs](https://help.obsidian.md/How+to/Use+callouts) for more info
````
> [!FAQ]- 
> some test code:
> ```
> test
> ```
````

> [!FAQ]- 
> some test code:
> ```
> test
> ```

### ❌ Toggle 
the build in support in Obsidian for using `<details><summary>` doesn't work with codeblocks, see:
<details>
<summary>
Install
</summary>
install on windows with [[winget]]
```powershell
winget install -e --id Obsidian.Obsidian
```
</details>

### ❌ Obsidian admonition
[obsidian-admonition](https://github.com/valentine195/obsidian-admonition) is a plugin to support callouts
however without the plugin it just looks like a code block

````
```ad-note
title:
Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nulla et euismod nulla.
```
````

```ad-note
title:
Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nulla et euismod nulla.
```


