## Vision
Imagine a preset to take apps with you when swapping pc for [[winget]]
Or an account that lists your favorite apps for quick installation.

Similar to the UX from chrome, [[Chrome remembers extensions]]

## Existing solutions
Winget has [export], it exports a JSON file of **ALL** installed apps. Afterwards you can edit the JSON. 
The JSON can be loaded by the [import] command to install all apps.

Cons:
- Not much control
- Install all or nothing

Sites that let you search for, and create winget install lists:
- [winget.run] has no support for profiles
- [winstall.app] uses twitter to share package lists !?

# TODO
- [ ] think how the perfect UX would be
- [ ] create winget app
- [ ] proof concept works, then propose feature merge in winget

## UX
- make a "profile", e.g. linked to Windows user (Onedrive) or GitHub 
- store installed apps by host
- allow for "favoriting apps" : heart or star
- when logging on a new device:
	- command to load profile
	- auto install previous apps

#toolidea #cloud #winget

[export]: https://learn.microsoft.com/en-us/windows/package-manager/winget/export
[import]: https://learn.microsoft.com/en-us/windows/package-manager/winget/import
[winget.run]: https://winget.run/
[winstall.app]: https://winstall.app