GPT research, setup a http server in [[Unity]]: 
- [[setup deeplink support for unity - GPT]]
- [[potential issues and named pipe alternative - GPT]]

I decided to instead piggy back on the existing asset store deeplinking support in Unity.
## Dev
I forked [[unity deeplink - needle tools]]
- https://github.com/hannesdelbeke/unity-deeplink
- run menu command
- select assets & [[Unity extend right click context menu|right-click menu]] to copy URI from asset

todo
see [[deeplink redirect - GPT]]
- custom scheme `unity://select?asset/path`
- custom scheme `unity://menu?menu/path`
- maybe support parameters in future? e.g. cube of size 4
- option in plugin to toggle support to copy URI to the correct `unity://select?asset/path` format, if user choses to use that scheme
## Existing solutions
- https://github.com/nicbarker/UnityEditorDeeplinking 
	- not tested
	- not maintained
	- deeplink through TCP/IP socket on `127.0.0.1`m 
	- no UPM support
- [[unity deeplink - hook interceptor]]
	- not tested
- [[unity deeplink - needle tools]]
	- tested, samples didn't seem to work

[[app URI]]