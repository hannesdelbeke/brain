Do max plugins handle their own python [[dependencies]]?

[[Autodesk 3ds Max]] itself does not provide a universal dependency manager for plugins; each plugin/package decides how to manage dependencies. 

--- 

  In 3ds Max, plugins can ship Python packages, but dependency handling is typically done by the plugin author via one of these patterns:

  1. Bundle pure-Python libs inside the plugin and add paths at startup.
  2. Bundle compiled wheels matching Max’s embedded Python version.
  3. Run a custom installer/bootstrap step that installs deps into Max’s Python environment.
  4. Use isolated external Python and communicate with Max (less common, more complex).

## My preference
I like the installer/bootstrap step, because it's like a pip install or npm install, and avoids shipping duplicate dependencies. However, it might be less stable and harder to resolve.

If you set up [[CICD]] and build a released plugin package, shipping wheels is more stable, but you might need to build for multiple platforms and Python versions.

Also see [[plugget]], my own dependencies manager for dcc apps.
