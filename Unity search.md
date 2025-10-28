---
aliases:
  - Unity Asset searcher
  - Unity Command searcher
---
[[Unity native feature|Unity ships with]] a default search tool.  
in the project Tab, next to the search bar there's an expand icon.
You can search assets, [[GameObject|gameobjects]] in your open scene,  menu commands, and settings.

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

Unity search 
- saves its favorites in 
`project_name\UserSettings\Search.settings`
- only saves favorites to disk when you close Unity or Unity search, not when you favorite something
- Only reads the favorite list on Unity startup, then just keeps it in memory. External edits while Unity is in use will be lost.

because of the above, it's hard to extend. No API, and closed source.

missing features
- right-click an asset in the project window to (un)favorite it
- a way to see all favorites


[[file browser]]
[[dcc search bar]]

similar to [Unity quick search](https://docs.unity3d.com/Packages/com.unity.quicksearch@1.1/manual/index.html#api)