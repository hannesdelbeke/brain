
The bulk of the work is happening when PyMel is initializing a bunch of mel scripts.  
This can be skipped by setting the `PYMEL_SKIP_MEL_INIT` environment variable.

If you just want to skip initializing plugins, you can set `skip_initial_plugins=true` in the `pymel.conf` file
## pymel core
when importing `pymel.core as pm` for the first time, it freezes maya for a few seconds

it takes a while to load, because it scans all the loaded plugins, and then wraps any provided commands with a PyMel version.

workaround
- The best way to speed that process up would be to unload any plugins you’re not actually making use of.

## pymel all
`import pymel.all` operation instead of just an `import pymel.core` can be substantially longer. As it is generating all the various Node classes upfront.



[source](https://www.tech-artists.org/t/pymel-core-import-in-maya-2018-super-slow/10167/11)