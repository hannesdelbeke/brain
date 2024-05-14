### Context
this was my reply to this [tool](https://forums.unrealengine.com/t/figma-import-pipeline/574592)  
### Reply
you can create unreal UMG dynamically without c++
  
in python you can access the widget tree following way  
1. duplicate your userwidget from the template to make a new userwidget, and pass it to the next method 
2. load the root node
   see [unreal.load_object](https://docs.unrealengine.com/4.27/en-US/PythonAPI/module/unreal.html?highlight=load_object#unreal.load_object): 
   first arg is the object's [[Unreal outer|outer]], second arg is the object's name.
```python
import unreal
# given our user widget, we load the widget tree inside, which is a child of the user widget
widget_tree  =  unreal.load_object(userwidget, name_of_widgettree)  
# given the widget_tree, we load the rootnode, which is a child from the widget_tree
root_node = unreal.load_object(widget_tree, name_of_rootnode)
```
3. add children to and save the userwidget.
   (this only works in unreal 5, not yet got it to work in 4)  

[[Unreal Python]]
[[Unreal Motion Graphics]]