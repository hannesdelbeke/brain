Artists often want to put all tools on a [[Maya shelf]].
- It's always there in front of them. The artist doesn't has to search for anything.
- it's simple, just click a button to launch the tool.

## Cons
Maya shelves are a little clunky tech wise when distributed to teams through [[version control|source control]], 
I'm a bit rusty on the exact why since I've been avoiding them, i think it related to
- you can't delete/unload a shelf once loaded in Maya
- shelves contain code, which can be edited by the user.
  because of this they can create conflicts with the source repo when getting latest.
  This doesn't happen with tools launched from a menu.

but lets pretend it works as expected. Shelves still have a UX issue

The drawback comes with scaling up.
After a while your team will have many tools, and many shelves.
Over the years more teams join. More projects are spun up. And the shelves turn from a simple solution into a confusing clutter.

[[don't waste time on organizing your tools]]
Teams now start discussing a cleanup, or a reorganize, and are putting resources into something non-productive.

[[don't distract me with your tools]]

The initial [[minimalism]] is lost at one point, and as soon as this happens shelves stop being the easy simple way

Either, you never add more than a few tools to a shelf, 
or you avoid shelves altogether and use a [[menu]].
A menu can contain multiple categories (sub menus), and often menus allow a menu item / menu command to live in multiple menus.

I find menus better, but it isn't the perfect solution.
I wrote an article on why [[every AAA Unity project has bad menu UX]] because of the scale of the project, team, and third-party plugins.

I never ran in this issue in Maya, since often
- only a few people are developing the tools that are added to the menu. 
- not many third party plugins are installed in Maya 

[[toolbar]]