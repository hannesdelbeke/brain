Don't only focus on the cons, there are a lot of pros too: [[Pyblish pros]]

#### Main issues
- [[Pyblish issue - plugins are hardcoded to the project or studio]] preventing easy plugin reuse
- Pyblish imports plugins but doesn't add their folder to the env
	- this means plugins that import anything not setup in your env wont work
- [[Pyblish issue - has no explicit plugin control]]
- [[Pyblish issue - action and plugin have no direct link]]
- [[Pyblish issue - UI is not artist friendly]]
- UI/UX is not art friendly (created [[Pyblish simple]])
	- Pyblish UI confuses artists
	- show what went wrong, filter by instance type e.g. mesh, or textures
#### High barrier to entry for devs
Pyblish is easy to pick up and use, as is, the way Marcus intended it. 
When you want to do more advanced stuff, it starts to feel limiting
- [[Pyblish issue - docs are confusing]]
* [[Pyblish issue - dependency injection]] is unpythonic, confusing devs
- [[Pyblish issue - development is slow]]
- [[Pyblish issue - inconsistent logic]]
- [[Pyblish default plugins]]
- [[Pyblish issue - warning vs error]]
- a high [[cognitive load]] due to the complexity of the code. mix in support for old style plugins, and new style plugins resulting in nearly double code. Since both are still supported and used.
## Conclusion
[[my progamming review]]
The current issues make it hard to expand on Pyblish without hard forking it.
And if you hard fork, you might as well start from scratch again. 

Use Pyblish as is. Don't try to fix it, it's too complex.

see [[pipeline as code]] for a hard fork.
Some goals:
- community plugins repo
- explicit workflows / pipelines.
	- config to choose which plugins to run
	- config to override plugin settings, actions, ...

[[pipeline]]