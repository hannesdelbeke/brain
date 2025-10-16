When I started out with game development, I used to develop [[my games]] on [[Dropbox]].

A few issues with that:
- data limit of 2gb for free tier
	- Projects count towards everyone’s limit, so if someone has done a few gamejams already, they can't join without removing a few old projects.
- The [[Unity Library]] is uploaded by default, unnecessarily increasing project size and creating conflicts. This should be excluded from your version control, e.g. with a git ignore on [[git]], or a perforce ignore on [[Perforce]]
	- it is possible to exclude it manually
- data is instantly uploaded, quickly resulting in conflicts.