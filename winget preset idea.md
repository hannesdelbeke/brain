# Vision
Imagine easily installing apps when upgrading pc. You log in and your apps automatically install in the background. No more time is wasted on reinstalling apps.

With [[winget]] installing apps has become faster, but not yet smooth. (And still quite technical)
Something similar to the UX from [[Chrome]] would be ideal, you just log in with your [[Gmail]] account, and[[chrome remembers extensions]] and auto installs them for you.

# Existing solutions

## Winget
Winget has [export], it exports a JSON file of **ALL** installed apps. Afterwards you can edit the JSON. The JSON can be loaded by the [import] command to install all apps.

Cons:
- Not much control
- Install all or nothing

Sites that let you search for, and create Winget install lists:
- [winget.run] has no support for profiles
- [winstall.app] uses Twitter to share package lists !?

It's now pretty easy to save apps in a note, and execute the install code directly from the note.
- But it requires 3 apps to be installed:
	- Git
	- Obsidian
	- Winget
	Ideally, I install just 1 app, Winget, to auto install ALL other apps. (Git, Obsidian, and the rest)
- It also means I need to download or access my notes online, or sync them with a new computer. I might not want that on a work computer.

## All in one installers
[NiNite] let's you make a all-in-one installer for some apps. 
Cons
- only a small selection of popular apps
- not a cloud-first mindset
- keeping the installer updated is a hassle
- the installer needs to be transferred to your new pc, more hassle

# TODO
- [ ] think how the perfect UX would be
- [ ] create winget app
- [ ] proof concept works, then propose feature merge in winget

## UX
- make a "profile", e.g. linked to Windows user (Onedrive) or GitHub 
- store installed apps
	- optional: store by host. This info might get outdated?
- optional: allow for "favoriting apps" : heart or star
	can be apps that are not installed

- when logging in on a new device:
	- auto install previous apps
	- or command to load profile with bookmarked apps.

Ideally also supports chocolatey, scoop etc.

#toolidea #cloud

[export]: https://learn.microsoft.com/en-us/windows/package-manager/winget/export
[import]: https://learn.microsoft.com/en-us/windows/package-manager/winget/import
[winget.run]: https://winget.run/
[winstall.app]: https://winstall.app
[NiNite]: https://ninite.com/

[[template]]
[[preset]]