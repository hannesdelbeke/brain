---
aliases:
  - app link
  - universal link
---


An app [[Uniform Resource Identifier]] launches an app from a [[URL]].
this can be useful if an app wants to open another app.
e.g. clicking [calculator://](calculator://) opens the calculator on Windows

### use cases
- logseq uses this to link to other graphs: [[interwikilinks plugin#reference logseq]]
- [obsidian URI](https://help.obsidian.md/Advanced+topics/Using+obsidian+URI) also supports this

works on Linux, Windows, Android …
also allows opening apps from your browser. great for tutorials

slow command to print all registered URIs `reg query HKCR /s /f "URL Protocol" /c`
This very slow command lists all URIs found in the registry on Windows:
```batch
@For /f "tokens=1* delims=" %%A in ('reg query HKCR /f "URL:*" /s /d ^| findstr /c:"URL:" ^| findstr /v /c:"URL: " ^| Sort') Do @Echo %%A %%B
pause
```

there's an [official list](https://en.wikipedia.org/wiki/List_of_URI_schemes#Official_IANA-registered_schemes) of URIs, so when adding a new one check it's not already in use.

App URI is similar to [[Component Object Model|COM]] dispatch

### custom app URI
from a stackoverflow [answer](https://stackoverflow.com/questions/32694642/registering-an-application-to-a-uri-scheme-in-windows-10)
```csharp
RegistryKey key;
key = Registry.ClassesRoot.CreateSubKey("foo");
key.SetValue("", "URL: Foo Protocol");
key.SetValue("URL Protocol","");

key = key.CreateSubKey("shell");
key = key.CreateSubKey("open");
key = key.CreateSubKey("command");
key.SetValue("", "C:\\oggsplit.exe");
```

AI translated to powershell, not yet tested.
believe this needs to run in elevated mode

```powershell
New-Item -Path "HKEYCLASSESROOT\foo"
Set-ItemProperty -Path "HKEYCLASSESROOT\foo" -Name "" -Value "URL: Foo Protocol"
Set-ItemProperty -Path "HKEYCLASSESROOT\foo" -Name "URL Protocol" -Value ""
New-Item -Path "HKEYCLASSESROOT\foo\shell\open\command"
Set-ItemProperty -Path "HKEYCLASSESROOT\foo\shell\open\command" -Name "" -Value "C:\oggsplit.exe".
```

```python
```python
import registry

key = registry.ClassesRoot.OpenSubKey("mycalc")
key.SetValue("", "URL: Foo Protocol")
key.SetValue("URL Protocol", "")

key = key.CreateSubKey("shell")
key = key.CreateSubKey("open")
key = key.CreateSubKey("command")
key.SetValue("", "calc")
```

[[Python snippet]]