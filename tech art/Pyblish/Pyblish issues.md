## I love Pyblish
I have a love hate relation with [[Pyblish]]. I've learned a lot working with it. Gave back several contributions to the various projects, and actively contributed to the forum.
The longer I worked with it, the more I found myself reaching the limits, and feeling limited in attempts to fix and expand it.
I created a long-term plan to improve Pyblish on the [forum](https://forums.pyblish.com/t/long-term-goal/681/3?u=hannes)

Pros
- easy to pick up and get started
- tested in several dcc-s
- ships with UI
- working with Marcus can be educational.
- modular plugin infrastructure & discovery & plugin registration
- support for actions
- plugin dependency management
## My issues with Pyblish
Main issues
- [[Pyblish plugins are hardcoded to the project or studio]] preventing easy plugin reuse
- Pyblish imports plugins but doesn't add their folder to the env
	- this means plugins that import anything not setup in your env wont work
- [[Pyblish has no explicit plugin control]]
- [[Pyblish action and plugin have no direct link]]
- UI/UX is not art friendly (created [[pyblish simple]])
	- Pyblish UI confuses artists
	- show what went wrong, filter by instance type e.g. mesh, or textures
#### High barrier to entry for devs
Pyblish is easy to pick up and use, as is, the way Marcus intended it. 
When you want to do more advanced stuff, it starts to feel limiting
- [[Confusing Pyblish docs]]
* [[Pyblish dependency injection]] is unpythonic, confusing devs
- [[Pyblish development is slow]]
- [[Pyblish inconsistent logic]]
- [[Pyblish default plugins]]
- [[Pyblish warning vs error]]

## Conclusion
The current issues make it hard to expand on Pyblish without hard forking it.
And if you hard fork, you might as well start from scratch again.
Some goals:
- community plugins repo
- explicit workflows / pipelines.
	- config to choose which plugins to run
	- config to override plugin settings, actions, ...

#pipeline