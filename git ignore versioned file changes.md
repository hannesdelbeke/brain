### Ignoring versioned files

Some files in a repository change often but are rarely committed. Usually, these are various local configuration files that are edited, but should never be committed upstream. Git lets you ignore those files by assuming they are unchanged.

1. In Terminal, navigate to the location of your Git repository.
2. Run the following command in your terminal:

`git update-index --assume-unchanged path/to/file.txt`

Once you mark a file like this, Git completely ignores any changes on it. It will never show up when running `git status` or `git diff`, nor will it ever be committed.

To make Git track the file again, simply run:

`git update-index --no-assume-unchanged path/to/file.txt`.

[[git]]