Plugget is a [[package management|package manager]] to easily install tools in your apps.
It aims to dummy proof tool distribution, and is designed to assist artists in the games & VFX industry.

Github repo: [plugget](https://github.com/hannesdelbeke/plugget) 


Plugget is not an [[environment management|environment manager]]

- [ ] make more accessible
	- [x] [[auto install plugget & dependencies]]

## Features
- a pip install is too advanced for artists, so plugget simplifies this with a simple UI & 1click installer.
- a pip install installs to python site pacackages. not all dcc's isolate their python environment. So python scripts installed in the users site packages folder, aimed to be used in unreal, might also show in blender. 
  Plugget instead installs to the correct isolated folder for the dcc to avoid this.
- Instead of every user having to figure out the correct install process, a dev does this once by defining the correct manifest, saving all end users time. 
- The end user maintains control which tools are installed. But a dev can define a tool install list.
- ... TODO describe more features

Private notes
- [[plugget changelog]]
- [[plugget RAW dev notes]]
- [GITHUB PROJECT](https://github.com/users/hannesdelbeke/projects/5) PLANNING
- plugget package [manifest repo](https://github.com/hannesdelbeke/plugget-pkgs) 
