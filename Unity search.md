---
aliases:
  - Unity Asset searcher
  - Unity Command searcher
---
[[Unity]] ships with a default search tool.  
in the project Tab, next to the search bar there's an expand icon.
You can search assets, gameobjects in your open scene,  menu commands, and settings.

![](https://docs.unity3d.com/uploads/Main/search-profile-package.png)

features
- Save searches
- a [[tool launcher]] for tools added to the menu
	- You can't create tool/command categories. The closest alternative is sub menus and saving your search.
	- The unity menu doesn't support thumbnails, so neither does this searcher
	- You can [[favorite|star]] results/tools. Favorited items always show at the top of a search.
	  There's no easy way to see favorites unless you do a search containing that favorite.
	  Favorited items can be accessed with [SearchSettings.searchItemFavorites](https://docs.unity3d.com/ScriptReference/Search.SearchSettings-searchItemFavorites.html)

see https://docs.unity3d.com/Manual/search-overview.html
[[file browser]]