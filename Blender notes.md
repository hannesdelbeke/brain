seems the best solution would be native text
and add richtext support

## Idea
- toggle from the script editor menu `View/Markdown`
- this doesn't change the text, but changes the way it's displayed

## Dev
1. **Modify the Text Editor's UI**:
    - Blender's UI is Python-driven, so you could extend the **Script/Text Editor** menu.
    - Add a "View/Markdown" toggle option. This can be done by appending a custom operator to Blender's menu.
2. **Create the Markdown Renderer**:
    - Use a Python Markdown library like [`markdown`](https://pypi.org/project/Markdown/) to parse the text content.
    - Render the parsed Markdown as styled text using Blender's **region drawing API** (`bpy.types.SpaceTextEditor.draw_handler_add`).
3. **Non-Intrusive Toggle**:
    - Ensure that toggling the Markdown view doesn’t modify the actual content of the text file. Instead, the renderer should dynamically interpret the content and display it in the viewport.
4. **Styling for Markdown Elements**:
    - Use Blender's GPU drawing module (`bgl` and `gpu`) to style elements like headers, bold/italic text, lists, and links.
    - For instance:
        - Headers (`#`, `##`) can be displayed in larger or colored fonts.
        - Bold/italic styles (`**bold**`, `_italic_`) can have appropriate font weight or style.
        - Links (`[text](url)`) can be underlined or in blue.
5. **Event Handlers**:
    - Add an event listener to detect when the user toggles to Markdown view. Dynamically render the styled output within the text editor's region without impacting the underlying code or text.
6. **Optional Features**:
    - Add syntax highlighting for Markdown-specific elements.
    - If possible, make URLs clickable by capturing mouse events (though Blender text editors aren't inherently designed for interactivity).
### Basic Implementation Snippet (Concept):
Here’s a starting point for appending a "Markdown View" toggle to the Text Editor menu:
```python
import bpy

# Custom operator to toggle Markdown view
class TEXT_OT_toggle_markdown(bpy.types.Operator):
    bl_idname = "text.toggle_markdown"
    bl_label = "Toggle Markdown View"
    bl_description = "Display the text in Markdown format"

    markdown_enabled: bpy.props.BoolProperty(default=False)

    def execute(self, context):
        self.markdown_enabled = not self.markdown_enabled
        if self.markdown_enabled:
            self.report({'INFO'}, "Markdown View Enabled")
            # Add Markdown parsing and rendering here
        else:
            self.report({'INFO'}, "Markdown View Disabled")
            # Remove the renderer here
        return {'FINISHED'}

# Append to the menu
def draw_markdown_toggle(self, context):
    self.layout.operator(TEXT_OT_toggle_markdown.bl_idname)

# Register
def register():
    bpy.utils.register_class(TEXT_OT_toggle_markdown)
    bpy.types.TEXT_MT_view.append(draw_markdown_toggle)

def unregister():
    bpy.utils.unregister_class(TEXT_OT_toggle_markdown)
    bpy.types.TEXT_MT_view.remove(draw_markdown_toggle)

if __name__ == "__main__":
    register()
```

This adds the "Toggle Markdown View" option in the Text Editor's **View** menu. You’d expand on this by implementing the Markdown rendering logic.


## native
- use the script editor to save text files in Blender files
	- can have multiple text nodes in the file
	- text nodes can be linked to frame nodes in [[Blender geometry nodes]] or shader nodes
		- see Node annotator plugin that extends on this.
	- no [[URL]] or richtext support
		- see Markdown plugins
			- https://github.com/TheDuckCow/blender-markdown
				- fixed code for new Blender, [download](https://blenderartists.org/uploads/short-url/3IGX1gxS8KmOf7xoEWWkgLzgPMd.py), from this [thread](https://blenderartists.org/t/markdown-in-blenders-text-editor-and-ui/1405542)
				  *Now it doesn’t support links, bold/italic, and the headers level are only shown by how many dots are placed below them. It’s very limited, but maybe someone with more knowledge than me can do something.*
## existing
- generic_note 
	- doesn't work for people who don't have the extension installed
	- archived
	- [repo](https://github.com/ly29/GenericNote) & [code](https://raw.githubusercontent.com/ly29/GenericNote/master/generic_note.py)
