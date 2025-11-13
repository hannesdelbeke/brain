Datafix used to use [[Python namespace packages]].
During development, I kept running in issues
- [[integrated development environment|IDE]] doesn't support and is confused
- I'm confused, having to track implicit things across projects. [[cognitive load]]
- A change of folder structure affects multiple projects, low [[connascence]]

[[keep it simple|KISS]] so moved away from it.

I had something like this
datafix: `datafix.nodes.collectors.my_collector`
datafix maya:  `datafix.nodes.maya.collectors.my_maya_collector`

but moved back to
datafix: `datafix.nodes.collectors.my_collector`
datafix maya: `datafix_maya.nodes.collectors.my_maya_collector`

The more I write, the more I prefer [[explicit]] over [[implicit]] code.

**Tags**
[[datafix dev]]
[[software architecture|architecture]]
[[my code learnings]]