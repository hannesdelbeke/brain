> I'm implementing some custom manipulators and contexts, and I was wondering how to implement the `Tool Settings` UI for my custom context. I've noticed that if you implement `MPxContext::setTitleString`, the text will show up at the top of `Tool Settings`, but I couldn't find any resources for displaying UI elements or attributes there. Does anybody know how to do this?
> ![](https://groups.google.com/group/python_inside_maya/attach/613d3dad2c85b/Capture.PNG?part=0.1&view=1)

First, in your plugin you need to implement either `stringClassName` or `getClassName` functions to tell Maya what the name of your context is.

Then Maya will look for two files/procedures based on your class name:  `<Class Name>Properties.mel` and `<Class Name>Values.mel`.
In the Properties procedure you create all of your UI, and in the Values procedure you set the current state of the UI.  The first time your tool becomes active you should see your Properties procedure being called, and then every time you enter it Maya will call your Values procedure to update it.

To double check that you have your class name correct, you can set your tool active and then run:  `contextInfo -q -class 'currentCtx'

Take a look at the helixTool example in the [[Maya devkit]], it creates a context and a Tool Settings panel.

And related to this is how to create an Options marking menu for your context, this is the menu you get when you are in your context and you hold Ctrl-Shift-RMB.  There Maya expects a file named `<Class Name>OptionsPopup.mel`.  The helixTool example doesn't create one of these, but you can look at a Maya example like lassoOptionsPopup.mel.  
`D:\Program Files\Autodesk\Maya2026\scripts\others\lassoOptionsPopup.mel`

[source](https://groups.google.com/g/python_inside_maya/c/x3WTjXg61o8)

[[MEL snippet]]
[[Maya Tool Box]]