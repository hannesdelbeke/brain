---
aliases:
  - invalidate caches
---
Sometimes when you install a [[Python module]] while running [[Python]], it won't be importable until a session restart.

To fix this, if any modules are created/installed while your program is running,
run `importlib.invalidate_caches()` to guarantee all finders will notice the new module's existence (and be able to import it).

This does not [[python reload|reload]] any modules already imported, so old code might still be running.