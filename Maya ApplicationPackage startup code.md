hey i remember there was a discussion of some very niche way to execute maya (or was it max) startup code.  
it's not [[Maya plugin]] or [[usersetup]]. it's something that bypasses the startup checks etc.  
believe [@theodox](https://tech-artists.slack.com/team/U0A7B2S90) or [@bob.w](https://tech-artists.slack.com/team/U0AGU8571) mentioned it. might have been related to how maya handles translation? if anyone can point me in the right direction ![:pray:](https://a.slack-edge.com/production-standard-emoji-assets/14.0/google-medium/1f64f.png)

i think it might have been related to this max post. something to do with same name file as something will auto run on startup . [[Distributing plug-ins & files on Maya (and 3ds Max) - 2013]]

think it's related to ApplicationPackage  
which is also supported on maya [https://help.autodesk.com/view/MAYAUL/2024/ENU/?guid=Maya_SDK_Distributing_Maya_Plug_ins_DistributingViaTheAppStore_html](https://help.autodesk.com/view/MAYAUL/2024/ENU/?guid=Maya_SDK_Distributing_Maya_Plug_ins_DistributingViaTheAppStore_html)

think it might be this that i m talking about  
`<moduleName>_load.mel/.py`

>  One new thing for Maya is that Maya will now call a `<moduleName>_load.mel/.py` file as soon as a module is detected.

from 