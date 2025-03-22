https://github.com/needle-tools/unity-deeplink
this repo works partialy. (4 years old)

it works to capture basic UPM links. i can print stuff, even for non existing links as long as we start the URI with 
`com.unity3d.kharma:content/`

it doesn't work for custom ones, e.g. `com.unity3d.kharma:runcommand/` even though we should be able to at least print it to the console.
Unity likely filters them out now as invalid, before they reach our patch.