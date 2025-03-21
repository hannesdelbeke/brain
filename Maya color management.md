[[Maya]] saves the Color Management setting on a scene by scene basis instead of saving it in the window or user prefs.

MEL command to disable it
```mel
colorManagementPrefs -edit -cmEnabled 0;
```

You can use "color management policies (external preference files)" to Disable Color Management.
http://help.autodesk.com/view/MAYAUL/2016/ENU/?guid=GUID-AE1F72ED-FA00-4E81-8027-785E3D6058F7
-The policy file overrides the effect of the [[OpenColorIO|OCIO]] environment variable.