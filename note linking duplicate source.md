notes in obsidian rely on [[link|links]] between notes.
When you talk about something external, e.g. a github repo, you can't link to it.

So to create connections between notes, you make a note that duplicates the github repo, and just paste the URL in there. Maybe a screenshot and small description.

But it often feels just being able to link to the readme directly would be nicer. it already has an img and description.

see [[link unlinked websites]]

## Solution
Embed the URL in an iframe.
Note in [[Obsidian]], first define height, then width. Else height won't work.  
```HTML
<iframe src="https://github.com/martinlanton" height="800" width="800" ></iframe>
```
<iframe src="https://github.com/martinlanton" height="800" width="800" ></iframe>