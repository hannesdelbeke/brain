---
sentiment:
- 5
sentiment-hash: d01afc8b
sentiment-label:
- factual
tags:
- technical
- planning
---

[[Autodesk Maya]] doesn't has the user script folder in [[site-packages]].
so [[pth]] files are not processed. 
- [ ] create a plugin that handles this for maya on startup.

```python
import site
site.addsitedir(r"path/folder")
```
