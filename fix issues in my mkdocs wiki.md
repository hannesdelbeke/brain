
## review
- [[premature optimization]] causes bugs
	- download without history is faster but loses git commit times
	- not deleting old html pages and only updating or adding is faster but leads to duplicate pages. believe this might also cause a bug in the search [[mkdocs]] extension
- currently doesn't auto build

to manually build, click run workflow [here](https://github.com/hannesdelbeke/wiki/actions/workflows/copy-to-documentation-branch.yml)
# error log summary
The log details several issues related to deprecations and errors in the project build process. Here's a summary:
1. **Deprecated Features**:
    - `material_extensions`: Deprecated and will no longer be supported in future releases.
    - `datetime.datetime.utcfromtimestamp()`: Deprecated and will be removed in future Python versions. Use timezone-aware objects instead.
    - `materialx.emoji.twemoji`: Deprecated. Emoji logic has been moved to `mkdocs-material` version 9.4. Update the configuration in `mkdocs.yml` to use `material.extensions.emoji.twemoji` instead.
2. **Git Revision Date Localized Plugin Warnings**:
    - Several markdown files (e.g., 'wind turbine.md', 'winget manifest query.md') lack git logs, so the current timestamp is being used as a fallback.
3. **File and Link Issues**:
    - A documentation file ('winget.md') contains a link to a non-existent 'install.gif'.
4. **Runtime Error**:
    - An error occurred while building the page 'Chrome.md', causing a "list index out of range" exception. This is likely due to an issue in the `material/plugins/search/plugin.py`.

To address these issues, consider the following actions:
1. **Update Deprecated Features**:
    - Replace `materialx.emoji.twemoji` with `material.extensions.emoji.twemoji` in `mkdocs.yml`.
    - Refactor code to replace `datetime.datetime.utcfromtimestamp()` with timezone-aware alternatives.
2. **Check Git Logs**:
    - Ensure all markdown files have corresponding git logs or handle the fallback more gracefully.
3. **Resolve Missing Files/Links**:
    - Verify the presence of 'install.gif' or update the documentation to remove or correct the link.
4. **Investigate Runtime Error**:
    - Debug the "list index out of range" error in the search plugin, possibly by inspecting the page content or modifying the plugin code to handle empty lists or missing data gracefully.


[[GitHub pages]]
- [ ] todo link to my wiki page / note
- [ ] [[todo]]

[[my wiki]]
