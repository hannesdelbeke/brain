---
aliases:
- distributing tools - tool installer
sentiment:
- 5
sentiment-hash: 08155e44
sentiment-label:
- factual
tags:
- technical
- planning
- work
---

rolling out tools to users.

in a project, we distribute tons of tools, lots of 3rd-party and dev tools that aren't relevant to everyone. As a TA I prefer a clean setup: install only relevant tools, so the project doesn't end up with 200 tools installed cluttering it or preventing it from launching when one tool's code breaks.

[[package management]]

- use versioning and support rolling back to prevent rolling out a compile error breaking the user's environment
- offer easy updating, since users can't be assumed to be technical (e.g. artists)
- are all tools setup the same on users' pcs? (e.g. a tool [[monorepo]] hosted on [[git]]), 
  or can users pick and choose, creating their own environment (e.g. [[plugget]]?
- How well documented is the whole process?
- How easy is it to set up the tool distribution, is it a 1 click process?

[[temporal integrity in asset pipeline]]


[[tooldev]]
[[file distribution]]
[[environment management]]
