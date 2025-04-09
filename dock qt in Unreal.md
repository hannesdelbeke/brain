docking a [[Qt]] widget in unreal is not possible by default.
parenting is.

## possible workaround
[[Unreal]] supports dockable slate widgets.
can we make a slate widget that passes it's coords to QT
and QT draws a [[window (computing)|window]] on top in the same coordinates?
when we move it, it moves with it.
- challenge would be to avoid a move loop. e.g. only move & resize if different. but in both directions

## reference
- https://docs.unrealengine.com/4.27/en-US/API/Runtime/Slate/Widgets/Docking/SDockableTab/
- https://forums.unrealengine.com/t/dock-qtwidget-to-unreal/132235/4
  > you can dock any kind of custom widget (SCoumpondWidget) using the FGlobalTabmanager singleton instance, create a SDockTab widget and set your custom widget as its content

- c++ ref http://www.kehomsforge.com/tutorials/multi/uColumns/part14
- py https://discourse.techart.online/t/editor-utilitty-widget-menus-in-unreal/12923
	
#[[Unreal]] #slate #widget #ui #toolidea