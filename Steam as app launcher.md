Valve's [Steam](https://store.steampowered.com/) is an [[app launcher]] for Steam apps (mostly games)
You can also add custom apps, which allows you to make lists of apps.

Q: So I wondered if you could use Steam as an app launcher for your project.
A: You can, but would be missing out on various features.
## Pro
- version management (*only for steam apps*)
- easy install (*only for steam apps*)
- social integration: 
	- friends, achievements, community, reviews, app score (*only for Steam apps*)
	- see when a friend launches an app
	- chat to friend
- option to set launch args
- add non Steam apps
- not sure what you can use this for: CLI integration [SteamCMD](https://developer.valvesoftware.com/wiki/SteamCMD)
## Con
Missing features that prevent reusing Steam as a software app launcher in production
- no [[environment management]]
	- HACK: launch bat file that edits environment 
- no app presets (e.g. maya, Krita, unreal)
- no easy install non-Steam apps
	- HACK custom script to install & setup apps
- no version management for non steam games.
- app lists are not easily distributed to team members.
