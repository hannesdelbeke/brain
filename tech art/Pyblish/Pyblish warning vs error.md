[[Pyblish]]  saves errors and warnings in different locations

Plugins either succeed or fail. There is no soft fail.
Yet in [[Pyblish]] UI, we can see some warnings fail softly <span style="color: orange;">orange</span>, instead of hard error in <span style="color: red;">red</span>

Plugins know if they succeeded or failed, but not if they "warned"
Pyblish UI (simple or qml) fake this by checking the log file attached to each instance. If they detect WARNING in the log, it get's colored orange.

### Suggestion
A better approach would be to handle warning and error in the same way.
This way the dev can easily change a plugin's fail level from error to warning, without having to rewrite the code to catch the crash, and log a warning.