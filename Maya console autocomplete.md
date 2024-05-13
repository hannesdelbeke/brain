[[Maya python]]

## native auto-completion
- disabled by default
- primitive when enabled

1. open the maya console 
2. in the menu, toggle: 

- not sure what these do: 
	- Command / Command completion: 	  
		  completes commands. caused a Syntax Error
	- Object Path Completion
	- show tooltip help: shows description of a complete command

## other
- pymel 2023 now includes stubs, see [article](https://dev.to/chadrik/pymels-new-type-stubs-2die) from pymel creators
- (official) maya 2022 [devkit](https://aps.autodesk.com/developer/overview/maya) contains pymel autocomplete. removed in 2023+ [source](https://forums.autodesk.com/t5/maya-programming/maya-2023-devkit-missing-pymel-completion-stubs/td-p/11464367)
  You can use the 2022 in later versions for a fairly accurate autocomplete
- maya autocomplete 2016 - 2022 [repo](https://github.com/roureOsso/MayaAutocomplete) (cmds only, no pymel)
- recent 2024 https://github.com/mackst/maya_stubgen
- https://pypi.org/project/maya-stubs/ claims better cmds stubsthan devkit, minimal openmaya support similar to devkit
- maya 2024 stubs [gitlab](https://gitlab.com/maya-stub-files-release/mayastubfiles_public_release/-/releases/v1.0.0)

[[python stubs]]