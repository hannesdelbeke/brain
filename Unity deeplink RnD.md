
## Existing solutions
- https://github.com/nicbarker/UnityEditorDeeplinking 
	- not tested
	- not maintained
	- deeplink through TCP/IP socket on `127.0.0.1`m 
	- no UPM support
- https://github.com/AdamCarballo/HookInterceptor
	- not tested
	- uses native unity asset store URI
	- [blogpost](https://f10.dev/blog/using-a-stream-deck-in-unity/) 
- [[unity deeplink - needle tools]]
	- tested, samples didn't seem to work

## Dev
I forked [[unity deeplink - needle tools]]
- run menu command
- select assets & right-click to copy URI from asset

todo
see [[deeplink redirect - GPT]]
- custom scheme `unity://select?asset/path`
- custom scheme `unity://menu?menu/path`
- maybe support parameters in future?
- option in plugin to toggle support to copy URI to the correct `unity://select?asset/path` format, if user choses to use that scheme
