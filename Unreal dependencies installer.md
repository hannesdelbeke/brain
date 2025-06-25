Auto install [[Python module]] [[dependencies]] in [[Unreal]], using [[py-pip]].
This script currently doesn't has it's own repo, it lives in the [[Unreal python plugin template]]
## cons
The dependencies installer tries to install dependencies every time on startup. It would be nicer to only try once.
Looking back, I wasted dev-time reducing prints in [[py-pip]] , and not doing a subprocess if already installed, to make it faster.
AFAIK plugget already did both, installing dependencies only once, and skipping install if already installed. But it's less drag and drop, requiring the user to first setup plugget.
