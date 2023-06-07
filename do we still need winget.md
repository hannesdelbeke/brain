---
energy: 4
sentiment:
- 6
sentiment-hash: c43ac415
sentiment-label:
- thoughtful
tags:
- journal
- technical
- self-reflection
- work
---

[[winget|Winget]] was created to solve the lack of [[package management|package manager]] in [[Windows]], but vendor‑supplied one‑line installers make installs just as simple — like:
```powershell
# this installs grok CLI
irm https://x.ai/cli/install.ps1 | iex
```

Compare this to a winget install line, which is more human friendly.
But an AI can easily sit on top and handle that whole UX layer.
Instead of typing a human friendly command, I ask my AI to install chrome.
```powershell
winget install chrome
```

Do we still need winget in the age of [[Artificial intelligence|AI]] ?
It's been very nice to use winget in the last few years, yet surprisingly few people I meet - even devs - know and use it.
