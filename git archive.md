Download a single file using git archive

Using git archive to download a single file involves accessing a remote repository and piping the output to tar to extract a specific file.
## breakdown
```bash
git archive --remote=<repository-url> HEAD:path/to/directory/filename | tar -x
```
- `git archive`: create an archive (like a `.tar` or `.zip` file) of files from a named tree in the repository.
  
- `--remote=<repository-url>`: create the archive from a remote repository at the URL
  
- `HEAD:path/to/directory/filename`: specifies what to include in the archive. 
	- `HEAD`: the latest commit on the current branch. 
	- `path/to/directory/filename`: file path within that commit. 
  
- `| tar -x` : The output of `git archive` is piped (`|`) directly into the `tar` command. 
  `tar -x` extracts the files from the archive stream it receives from `git archive`.
  As soon as `git archive` creates the archive, `tar` extracts it without having to save and extract the archive.
