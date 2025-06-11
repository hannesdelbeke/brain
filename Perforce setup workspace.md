
> [!warning] P4 Streams
> Ensure your stream is setup before pulling latest.
> Else you have to re-get the whole workspace.
> 
> if you try change stream afterwards, you end up with messy folders.
> e.g for the streams `stream 1` & `stream 2`
> without setting up streams, you get 2 folders in the repo `stream 1` & `stream 2`
> if you then setup stream, it will also pull the content from the stream to the root repo folder, without deleting the original stream folders. The user then might accidentally push the stream folders to the selected stream

Perforce syncs files from your computer to a server. This lets you share files in your team with others.

- The server is called the `depot`.
- The files on your computer live in your `workspace`.
## setup workspace

When joining a new project, you need to set up a workspace to get files from the server. 

1. click in the menu `Connection/New Workspace`
2. fill in the details of your workspace:
	- **name**: follow the project naming guidelines. e.g. `first.lastname_projectname`
	- **workspace root**: the location where files will be downloaded
	- **stream**: click the browse button and select your project’s stream.
	  If you can’t see your project contact IT for permission.

## Other
When you open P4V, you can swap between the depot and the workspace.
All your local file changes live in your `workspace`,
You need to submit these changes to a `changelist`, this list tells perforce which updated files to upload to the server. You can also type in a description, which will show in the file history.
And then submit this `changelist` to upload the files to the `depot`

[[Perforce]]