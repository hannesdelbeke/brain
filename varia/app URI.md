An app [[Uniform Resource Identifier]] launches an app from a URL.
this can be useful if an app wants to open another app.
e.g. clicking [calculator://](calculator://) opens the calculator on Windows

### use cases
- logseq uses this to link to other graphs: [[interwikilinks plugin#reference logseq]]
- [obsidian URI](https://help.obsidian.md/Advanced+topics/Using+obsidian+URI) also supports this

works on Linux, Windows, Android …
also allows opening apps from your browser. great for tutorials

This very slow command lists all URIs found in the registry on Windows:
```batch
@For /f "tokens=1* delims=" %%A in ('reg query HKCR /f "URL:*" /s /d ^| findstr /c:"URL:" ^| findstr /v /c:"URL: " ^| Sort') Do @Echo %%A %%B
pause
```

there's an [official list](https://en.wikipedia.org/wiki/List_of_URI_schemes#Official_IANA-registered_schemes) of URIs, so when adding a new one check it's not already in use.


App URI is similar to [[Component Object Model|COM]] dispatch