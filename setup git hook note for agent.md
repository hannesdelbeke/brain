
A git pre-commit hook has been set up to validate the YAML frontmatter in markdown files before committing. 

Specifically, it checks for duplicate keys (e.g., duplicated `origin-sha`) in the frontmatter block at the top of markdown files.

## Details
The script has been installed as a pre-commit hook in two locations:
1. **Root repository:** `.git/hooks/pre-commit`
2. **Public submodule:** `.git/modules/public/hooks/pre-commit`

## How it works
The hook is written in Python. Upon running `git commit`, the script:
1. Retrieves a list of all staged markdown files (`.md`).
2. Reads the frontmatter block (enclosed between `---` at the top of the file).
3. Parses the keys line-by-line and detects duplicates.
4. If duplicate keys are found, it prints the errors indicating the file and line number, and aborts the commit.

This ensures that broken or duplicated frontmatter does not get checked into version control.

- [[Anonymous SHA Pointer]] - this tech triggered the bug that requires this git hook