note-link-janitor is a batch script to add backlinks at the bottom for all [[wikilinks]] in a file of markdown files. The [original version](<[original repo](https://github.com/andymatuschak/note-link-janitor)>) dropped support, see my [fork](https://github.com/hannesdelbeke/note-link-janitor) with some fixes.

note-link-janitor can automatically run in a CI pipeline such as GitHub actions.
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

Incase of updates ensure we don't break dependencies
- used in [Obsidian Publisher template](https://github.com/ObsidianPublisher/obsidian-mkdocs-publisher-template/pull/12#event-8149371371)
- used by my wiki / public brain [[obsidian web integration]]