To [[link]] your [[Obsidian]] [[note taking|notes]] to [[Unity]]:
- no native support, got working prototype here [[Unity deeplink RnD]]
	- [[Unity extend right click context menu|right-click]] an asset to generate & copy the [[Uniform Resource Identifier|URI]] link to select the asset.
	- paste the link in an Obsidian note like a normal [[URL]]

## Dev
Unity supports [[app URI]] via `unityhub://` but does not have built-in direct file-opening support. 
```markdown
[Open My Unity Project](unityhub://open?path=C:/Path/To/Your/UnityProject)
```

## Related
[[link Unity asset to asset]]
[[link Unity to Obsidian]]
