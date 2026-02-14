
[[Autodesk Maya]] has [[maya module|maya modules]], that contain scripts and plugins and icons, handling all paths from a config `.mod` file. Does [[Autodesk 3ds Max|3dsmax]] has something similar?

  In 3ds Max, the closest equivalents are:

  1. plugin.ini
      - Main path registration file for plugins/scripts/resources.
      - Typical location: `C:\ProgramData\Autodesk\ApplicationPlugins\...\plugin.ini` or version-specific max folders.
  2. Application Plug-in Bundle (`*.bundle`) with `PackageContents.xml`
      - Modern Autodesk packaging format (used by Max too) (Installed under: `C:\ProgramData\Autodesk\ApplicationPlugins\YourPlugin.bundle\PackageContents.xml`) declares what to load, for which Max versions/platforms, and where files live.

  So unlike Maya’s .mod module system, Max usually uses `plugin.ini` + bundle descriptors (`PackageContents.xml`) for path/load management.

example modern plugin: [[Max dark script editor listener]]