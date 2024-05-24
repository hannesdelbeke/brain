When I started out with game development, I used to develop [[my games]] on [[Dropbox]].

A few issues with that:
- data limit of 2gb for free tier
	- if a project is 500 mb, this will count towards everyone’s free 2gb limit. So if someone has done a few gamejams already, they now can't join.
- The unity library is by default also uploaded, which unnecessary increases the project size and creates conflicts. This should be excluded from your version control, e.g. with a git ignore on [[git]], or a perforce ignore on [[Perforce]]
	- it is possible to exclude it manually
- data is instantly uploaded, quickly resulting in conflicts.