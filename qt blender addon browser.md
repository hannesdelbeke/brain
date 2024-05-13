A add-on browser widget, to quickly open [[Blender]] add-on folders in explorer.
To help speed up add-on development.
https://github.com/hannesdelbeke/qt-addon-browser

## Features
### Main priority 
- [x] no option to right click, open install directory
### copy default blender addon manager features
- [x] enable disable
- [x] list all addons
- [x] search addons by name
- [x] show explorer path (but no copy)
- [x] docs button
- [ ] bug report button
- [x] preferences
- [ ] addon install

### Stretch goals
fix minor issues with the default addon browser 
- [ ] shows all addons, no option to filter out default addons
- [ ] no option to filter by directory
- [ ] no easy option to customize.
- [x] search bar doesn't stay at top when scrolling down
#### Wishlist
- [ ] can we have some kind of view mode to see what data is saved to blender cloud?
  unsure how this works atm
- [ ] support display (e.g. as red) even if addon not correctly installed. (e.g. when a folder with files is in the addon folder without a correct python script setup)
- [ ] show dependencies
	- [ ] python libs based on requirements?
	- [ ] other dependencies, e.g. blend files?
- [ ] editable install (point to local addon working repo or project)

# Dev notes
## Wireframe MVP

| 🔎 search `_______________` |       |
| --------------------------- | ----- |
| ☑️ addon name               | 📄 📂 |
| ☑️ addon name               | 📄 📂 |
| ☑️ addon name               | 📄 📂 |

📄docs 
📂install folder
search filters addon by name

- [x] a button to open the preferences addon tab
- [x] a search text box
- [x] rows of (1 for each addon)
	- a checkbox (addon enable toggle)
	- label (addon name)
	- button (to open documentation) 
	- button (to open install folder) 
## Code reference
> [!code sandbox]-
> 
> ```python
> bpy.utils.user_resource('SCRIPTS', path="addons")
> 'C:\\Users\\hanne\\AppData\\Roaming\\Blender Foundation\\Blender\\3.2\\scripts\\addons'
> 
> bpy.utils.script_path_user()
> 'C:\\Users\\hanne\\AppData\\Roaming\\Blender Foundation\\Blender\\3.2\\scripts'
> 
> script_paths = [Path(x) for x in bpy.utils.script_paths]
> ['C:\\Program Files\\Blender Foundation\\Blender 3.2\\3.2\\scripts\\modules', 'C:\\Program Files\\Blender Foundation\\Blender 3.2\\3.2\\scripts', 'C:\\Users\\hanne\\AppData\\Roaming\\Blender Foundation\\Blender\\3.2\\scripts', 'C:\\Users\\hanne\\OneDrive\\Documents\\repos\\_Blender\\BlenderTools']
> 
> addon_paths = [x / "addons" for x in script_paths  if x.exists()]
> ```
> 


> [!code reference]-
> default addon manager code `space_userpref.py, def draw(self, context), line 1836`
> ```python
> import os
> import addon_utils
> 
> layout = self.layout
> 
> wm = context.window_manager
> prefs = context.preferences
> used_ext = {ext.module for ext in prefs.addons}
> 
> addon_user_dirs = tuple(
> 	p for p in (
> 		os.path.join(prefs.filepaths.script_directory, "addons"),
> 		bpy.utils.user_resource('SCRIPTS', path="addons"),
> 	)
> 	if p
> )
> 
> # collect the categories that can be filtered on
> addons = [
> 	(mod, addon_utils.module_bl_info(mod))
> 	for mod in addon_utils.modules(refresh=False)
> ]
> 
> split = layout.split(factor=0.6)
> 
> row = split.row()
> row.prop(wm, "addon_support", expand=True)
> 
> row = split.row(align=True)
> row.operator("preferences.addon_install", icon='IMPORT', text="Install...")
> row.operator("preferences.addon_refresh", icon='FILE_REFRESH', text="Refresh")
> 
> row = layout.row()
> row.prop(prefs.view, "show_addons_enabled_only")
> row.prop(wm, "addon_filter", text="")
> row.prop(wm, "addon_search", text="", icon='VIEWZOOM')
> 
> col = layout.column()
> 
> # set in addon_utils.modules_refresh()
> if addon_utils.error_duplicates:
> 	box = col.box()
> 	row = box.row()
> 	row.label(text="Multiple add-ons with the same name found!")
> 	row.label(icon='ERROR')
> 	box.label(text="Delete one of each pair to resolve:")
> 	for (addon_name, addon_file, addon_path) in addon_utils.error_duplicates:
> 		box.separator()
> 		sub_col = box.column(align=True)
> 		sub_col.label(text=addon_name + ":")
> 		sub_col.label(text="    " + addon_file)
> 		sub_col.label(text="    " + addon_path)
> 
> if addon_utils.error_encoding:
> 	self.draw_error(
> 		col,
> 		"One or more addons do not have UTF-8 encoding\n"
> 		"(see console for details)",
> 	)
> 
> show_enabled_only = prefs.view.show_addons_enabled_only
> filter = wm.addon_filter
> search = wm.addon_search.lower()
> support = wm.addon_support
> 
> # initialized on demand
> user_addon_paths = []
> 
> for mod, info in addons:
> 	module_name = mod.__name__
> 
> 	is_enabled = module_name in used_ext
> 
> 	if info["support"] not in support:
> 		continue
> 
> 	# check if addon should be visible with current filters
> 	is_visible = (
> 		(filter == "All") or
> 		(filter == info["category"]) or
> 		(filter == "User" and (mod.__file__.startswith(addon_user_dirs)))
> 	)
> 	if show_enabled_only:
> 		is_visible = is_visible and is_enabled
> 
> 	if is_visible:
> 		if search and not (
> 				(search in info["name"].lower()) or
> 				(info["author"] and (search in info["author"].lower())) or
> 				((filter == "All") and (search in info["category"].lower()))
> 		):
> 			continue
> 
> 		# Addon UI Code
> 		col_box = col.column()
> 		box = col_box.box()
> 		colsub = box.column()
> 		row = colsub.row(align=True)
> 
> 		row.operator(
> 			"preferences.addon_expand",
> 			icon='DISCLOSURE_TRI_DOWN' if info["show_expanded"] else 'DISCLOSURE_TRI_RIGHT',
> 			emboss=False,
> 		).module = module_name
> 
> 		row.operator(
> 			"preferences.addon_disable" if is_enabled else "preferences.addon_enable",
> 			icon='CHECKBOX_HLT' if is_enabled else 'CHECKBOX_DEHLT', text="",
> 			emboss=False,
> 		).module = module_name
> 
> 		sub = row.row()
> 		sub.active = is_enabled
> 		sub.label(text="%s: %s" % (info["category"], info["name"]))
> 
> 		if info["warning"]:
> 			sub.label(icon='ERROR')
> 
> 		# icon showing support level.
> 		sub.label(icon=self._support_icon_mapping.get(info["support"], 'QUESTION'))
> 
> 		# Expanded UI (only if additional info is available)
> 		if info["show_expanded"]:
> 			if info["description"]:
> 				split = colsub.row().split(factor=0.15)
> 				split.label(text="Description:")
> 				split.label(text=info["description"])
> 			if info["location"]:
> 				split = colsub.row().split(factor=0.15)
> 				split.label(text="Location:")
> 				split.label(text=info["location"])
> 			if mod:
> 				split = colsub.row().split(factor=0.15)
> 				split.label(text="File:")
> 				split.label(text=mod.__file__, translate=False)
> 			if info["author"]:
> 				split = colsub.row().split(factor=0.15)
> 				split.label(text="Author:")
> 				split.label(text=info["author"], translate=False)
> 			if info["version"]:
> 				split = colsub.row().split(factor=0.15)
> 				split.label(text="Version:")
> 				split.label(text=".".join(str(x) for x in info["version"]), translate=False)
> 			if info["warning"]:
> 				split = colsub.row().split(factor=0.15)
> 				split.label(text="Warning:")
> 				split.label(text="  " + info["warning"], icon='ERROR')
> 
> 			user_addon = USERPREF_PT_addons.is_user_addon(mod, user_addon_paths)
> 			tot_row = bool(info["doc_url"]) + bool(user_addon)
> 
> 			if tot_row:
> 				split = colsub.row().split(factor=0.15)
> 				split.label(text="Internet:")
> 				sub = split.row()
> 				if info["doc_url"]:
> 					sub.operator(
> 						"wm.url_open", text="Documentation", icon='HELP',
> 					).url = info["doc_url"]
> 				# Only add "Report a Bug" button if tracker_url is set
> 				# or the add-on is bundled (use official tracker then).
> 				if info.get("tracker_url"):
> 					sub.operator(
> 						"wm.url_open", text="Report a Bug", icon='URL',
> 					).url = info["tracker_url"]
> 				elif not user_addon:
> 					addon_info = (
> 						"Name: %s %s\n"
> 						"Author: %s\n"
> 					) % (info["name"], str(info["version"]), info["author"])
> 					props = sub.operator(
> 						"wm.url_open_preset", text="Report a Bug", icon='URL',
> 					)
> 					props.type = 'BUG_ADDON'
> 					props.id = addon_info
> 				if user_addon:
> 					sub.operator(
> 						"preferences.addon_remove", text="Remove", icon='CANCEL',
> 					).module = mod.__name__
> 
> 			# Show addon user preferences
> 			if is_enabled:
> 				addon_preferences = prefs.addons[module_name].preferences
> 				if addon_preferences is not None:
> 					draw = getattr(addon_preferences, "draw", None)
> 					if draw is not None:
> 						addon_preferences_class = type(addon_preferences)
> 						box_prefs = col_box.box()
> 						box_prefs.label(text="Preferences:")
> 						addon_preferences_class.layout = box_prefs
> 						try:
> 							draw(context)
> 						except:
> 							import traceback
> 							traceback.print_exc()
> 							box_prefs.label(text="Error (see console)", icon='ERROR')
> 						del addon_preferences_class.layout
> 
> # Append missing scripts
> # First collect scripts that are used but have no script file.
> module_names = {mod.__name__ for mod, info in addons}
> missing_modules = {ext for ext in used_ext if ext not in module_names}
> 
> if missing_modules and filter in {"All", "Enabled"}:
> 	col.column().separator()
> 	col.column().label(text="Missing script files")
> 
> 	module_names = {mod.__name__ for mod, info in addons}
> 	for module_name in sorted(missing_modules):
> 		is_enabled = module_name in used_ext
> 		# Addon UI Code
> 		box = col.column().box()
> 		colsub = box.column()
> 		row = colsub.row(align=True)
> 
> 		row.label(text="", icon='ERROR')
> 
> 		if is_enabled:
> 			row.operator(
> 				"preferences.addon_disable", icon='CHECKBOX_HLT', text="", emboss=False,
> 			).module = module_name
> 
> 		row.label(text=module_name, translate=False)
> ```

## blender addon extension
make a [[Blender]] addon to extend the addon preferences.

add a folder button to open the location
File: `C:/addon-location` 📂

see space_userprefs.py

reference [repo](https://github.com/urorwell/AddonPreferences-Minimal-UI) that edits the add-on UI

[[qt blender addon browser]]
[[Blender addons]]