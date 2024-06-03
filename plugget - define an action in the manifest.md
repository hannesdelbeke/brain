an example of defining a custom action in the [[plugget manifest]]
```json
{
	"repo_url": "https://github.com/plugget/plugget-unreal-plugin",
	"repo_paths": ["Plugget"],
	  "actions": [
	    {
	      "label": "Open Plugget",
	      "command": "import plugget_qt;w = plugget_qt.show()"
	    }
	  ],
	"docs_url": "https://github.com/plugget/plugget-unreal-plugin"
}
```
