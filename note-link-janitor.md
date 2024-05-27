`note-link-janitor` is a batch script to add [[backlink]] at the bottom for all [[wikilink]] in a file of markdown files. 

The [original version](https://github.com/andymatuschak/note-link-janitor) from [[Andy Matuschak]] dropped support, so I made a [fork](https://github.com/hannesdelbeke/note-link-janitor) with some fixes.

## Github action
`note-link-janitor` can automatically run in a CI pipeline such as GitHub actions.
> [!Github CI instructions]-
> Adding the following to your .yaml GitHub workflow will run note-link-janitor.
> I've got it setup to run on the build files, never on the source! 
> ```yaml
>   # run janitor on markdown input to create backlinks
>   - uses: actions/setup-node@v2
> 	with:
> 	  node-version: '16'
>   - uses: actions/checkout@v2
> 	with:
>       # use fork to support subfolders
> 	  repository: 'hannesdelbeke/note-link-janitor'  
> 	  ref: stable
> 	  path: 'note-link-janitor'
>   - name: install yarn in janitor workspace
> 	run: |
> 		cd ${{ github.workspace }}/note-link-janitor
> 		yarn install
> 		yarn run build
>   - name: Run Note Link Janitor
> 	run: ${{ github.workspace }}/note-link-janitor/dist/index.js ${{ github.workspace }}/docs
>   - name: Remove Janitor folder
> 	run: rm --force -r note-link-janitor
> ```

## Sample use cases
I use this to auto create backlinks from my markdown files in Obsidian.
This enables me to use [[MkDocs]] to create a site with backlinks from my notes.

In case of updates ensure we don't break dependencies
- used in [Obsidian Publisher template](https://github.com/ObsidianPublisher/obsidian-mkdocs-publisher-template/pull/12#event-8149371371)
- used by my wiki / public brain [[Obsidian web integration]]