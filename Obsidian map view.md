I tried out the [[Obsidian plugin]] Map View here: [[SUP in peak district]]
It does the job but a lil tricky to use if in line. since no browsing.
if you create a new note it ll pop up a box to browse for a place.
repo https://github.com/esm7/obsidian-map-view

### Create an embedded map & points
1. Embed a MapView map with the command `MapView: Add an embedded map`
2. Add an embedded point, e.g. 
```
   [LadyBower](geo:53.3691,-1.7004)
```
3. To ensure your embedded map picks up the locations in your note, you need to add an empty `locations` to the [[YAML front matter]] of your note, like this:
```
---
locations:
---
```
4. you can either google the coordinates, 
   or use the command `MapView new geolocation note`, 
   copy the coordinates from the new note to your inline point.
   and then delete the note

### Overview all notes
The `MapView Open mapview` command shows a map with points of all your notes.
Great to search locations in your whole digital garden. 




