[[Pyblish]]  saves errors and warnings in different locations.
This makes it harder to write code for e.g. for a custom UI

Plugins either succeed or fail. There is no soft fail.
Yet in [[Pyblish]] UI, we can see some warnings fail softly <span style="color: orange;">orange</span>, instead of hard error in <span style="color: red;">red</span>

Plugins know if they succeeded or failed, but not if they "warned"
Pyblish UI (simple or qml) fake this by checking the log file attached to each instance. If they detect WARNING in the log, it get's colored orange.

The benefit of this approach is that it can work with standard python logging
and code can only fail or succeed, warning is more of a node state, not native Python.

### Suggestion
A better approach would be to handle warning and error in the same way. (if you write a node based / custom datatype approach like pyblish )
This way the dev can easily change a plugin's fail level from error to warning, without having to rewrite the code to catch the crash, and log a warning.

we could also inherit from a pyblish wrapper to expose this in a variable.
it wraps around our pyblish node, and does a try except, and on failure logs a warning.