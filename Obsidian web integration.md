---
aliases:
  - Obsidian - publishing
---

R&D notes on how I can make some of my obsidian notes public, and keep them in sync with my personal notes. How to automate the publishing step, what tech to use, where to host, etc.


very messy notes, not formatted or cleaned up, little value for others.


## Goal

### Pros:
- host shared notes
	- some notes in my vault could live on the web. 
		e.g. my dev-notes can be useful to others.
		see [[digital garden examples]]

	- link to other people's vaults. create a community of knowledge
	  stack exchange, reddit, … show the power of this
- no need for software download/install (restrictions), discussed in [reddit post](https://www.reddit.com/r/ObsidianMD/comments/uf0u9e/comment/i789eam) and this [obsidian thread](https://forum.obsidian.md/t/obsidian-for-web/2049)

### existing solutions 


the best solution so far appears to be a [[static site generator]] for [[GitHub pages]]
dynamic render uses JavaScript which might be an issue, but no html generation needed


### static
- [mkdocs](https://www.mkdocs.org/) generates sites from markdown with python, [GitHub](https://github.com/mkdocs/mkdocs) ⭐15k
	- python!
	- static site generator
	- [tutorial](https://blog.elmah.io/hosting-a-mkdocs-driven-documentation-site-on-github-pages/) GitHub pages
	- [material](https://github.com/squidfunk/mkdocs-material) is a theme for mkdocs, ⭐12k
	templates
	- [ ] https://github.com/jobindjohn/obsidian-publish-mkdocs
		- wikilinks
		- github page
	- [ ] [this](https://www.reddit.com/r/ObsidianMD/comments/vql2yi/mkdocs_and_obsidian_templates/) reddit thread wants a update if I find a easy solution
	- [ ] [this](https://www.reddit.com/r/webdev/comments/z01c7j/is_there_anyway_to_host_markdown_files_online/j0p8ine/?context=3) post too
	- [ ] https://github.com/Jackiexiao/foam-mkdocs-template looks good, full GitHub page instructions
	- [x] [obsidian-mkdocs-publisher-template](https://github.com/ObsidianPublisher/obsidian-mkdocs-publisher-template)
		- neat UI, dark theme option
		- supports comments at bottom of post using [giscus](https://github.com/giscus)
		- requires a obsidian plugin, not a full CICD pipeline
- [x] Jekyll was one of the first site generators, has lots of support but a bit slow and dated
	about:
		In 2021, Jekyll developer said that **the Jekyll codebase "is in frozen mode and permanent hiatus**" and recommended users whose needs are not met by the frozen state of Jekyll to move to Eleventy
		- static generator
	a [tutorial](https://uoftcoders.github.io/studyGroup/lessons/misc/jekyll-ghpages/lesson/) on jekyll & github pages
	templates
		- [gitbook](https://sighingnow.github.io/jekyll-gitbook/jekyll/2019-04-27-why.html), 
		- [template](https://github.com/maximevaillancourt/digital-garden-jekyll-template) 500⭐
			- preview hover
			- wikilinks
		- [template](https://github.com/academicpages/academicpages.github.io) with instructions
			- [x] 1.  Register a GitHub account if you don't have one and confirm your e-mail (required!)
			- [x]  Fork [this repository](https://github.com/academicpages/academicpages.github.io) by clicking the "fork" button in the top right.
			- [x]  Go to the repository's settings (rightmost item in the tabs that start with "Code", should be below "Unwatch"). Rename the repository "[your GitHub username].github.io", which will also be your website's URL.
			- [ ]  Set site-wide configuration and create content & metadata (see below -- also see [this set of diffs](http://archive.is/3TPas) showing what files were changed to set up [an example site](https://getorg-testacct.github.io/) for a user with the username "getorg-testacct")
			- [ ]  Upload any files (like PDFs, .zip files, etc.) to the files/ directory. They will appear at https://[your GitHub username].github.io/files/example.pdf.
			- [ ]  Check status by going to the repository settings, in the "GitHub pages" section
			- [ ]  (Optional) Use the Jupyter notebooks or python scripts in the `markdown_generator` folder to generate markdown files for publications and talks from a TSV file.
	- [x] simple-Jekyll template for obsidian [repo](https://github.com/Maxence-L/notenote.link), [forum](https://forum.obsidian.md/t/notenote-link-publish-your-obsidian-notes-with-jekyll-for-free/7951) supporting wikilinks
- [ ] [Eleventy](https://www.11ty.dev/) is the new faster brother of Jekyll, supposed to be easy to use
	- With Eleventy, you can specify a markdown parser to supports wikilinks. [markdown-it-wikilinks](https://github.com/kwvanderlinde/markdown-it-wikilinks)
	- [template](https://github.com/binyamin/eleventy-garden)
- [ ] [mdbook](https://rust-lang.github.io/mdBook/) is a fast doc generator written in Rust
	- open source
	- dark theme
	- markdown
	- supports plugins, suggestions [post](https://news.ycombinator.com/item?id=23324598#23363574)
- [x] Netifly is a hosting/build service, similar to GitHub pages
- [x] lettersmith
	- techy template https://github.com/kmcgillivray/obsidian-lettersmith
		- support wikilinks
- [x] Docusaurus
	- nice [tutorial](https://baky0905.github.io/personal-website/blog/2021/04/02/docusaurus/)
		  [![](https://baky0905.github.io/personal-website/assets/images/landing-a7871b64daf45f3b12ca13d22e39cde8.png)]
	  was able to get tutorial to work
  - no wiki links, feature request [thread](https://docusaurus.io/feature-requests/p/support-link-thumbnail-card)
- Zola
  - [x] [obsidian-zola](https://github.com/ppeetteerrs/obsidian-zola) easy turn a git repo into a website, adding only 1 file
		- bad UI
		- requires a [netifly](https://www.netlify.com/) site, seems to be jekyll 
			- sign in w github account
- [MindStone](https://github.com/TuanManhCao/digital-garden)
	supports wikilinks, graph, ...
	looks pretty decent
	think it's an indie project so lots of bugs.
	
### dynamic
- [x] [docsify](https://docsify.js.org/#/?id=docsify)
	Docsify generates your documentation website on the fly. 
	- it doesn't generate static html files like GitBook, 
	- it displays your Markdown files as a website
	- [tutorial](https://michaelcurrin.github.io/docsify-js-tutorial/#/) 
	- it's not SEO friendly, just like github md preview, use static instead for this
	- works well
	- **no wikilinks** support, 
		wikilinks [plugin](https://github.com/zpengg/docsify-wikilink) , works partially
		- no support for images
		- no support for filename paths in other folders
	- https://docsify-this.net/#/ 
		load public md files with docsify through a 3rd part website
		just pass the URL e.g. to the GitHub .MD file
- GitHub
	- pages can just live in root, no extra clutter
	- easy PR community, online editor
	- no google crawl
- [x] [blot.im](https://blot.im/how/configure)
	- compatible w obsidian
	- 4$ a month
	- no wikilinks
### unsorted
- [ ] tiddlywiki - a stable wiki solution
	
- [x] [docker image](https://forum.obsidian.md/t/obsidian-remote-running-obsidian-in-docker-with-browser-based-access/34312/3) of obsidian, seems advanced
	- [reddit post](https://www.reddit.com/r/ObsidianMD/comments/sy3x92/accessing_my_obsidian_notes_in_the_browser/) going over more docker
- [Quartz/Hugo](https://fulcra.design/Notes/Start-publishing-my-notes) interesting task list from a dev describing the creation of his site
	- https://gohugo.io/
		- hugo is faster than jekyll
	- compatible with obsidian if you use meta data on top.
	  YAML title, date, and lastmod field
	  - [video](https://carpentries-incubator.github.io/blogging-with-hugo-and-github-pages/) tut on hugo 
- [ ]  checkout obsidian thread https://forum.obsidian.md/t/static-site-generators-any-guides/8915
- [ ] this [blogpost](https://www.kez.ie/notes/choosing%20the%20right%20platform%20to%20create%20a%20public%20digital%20garden/) discusses solutions, and shares feeling [[overwhelmed]]. they settled on Eleventy

### Start publishing my notes

https://fulcra.design/Notes/Start-publishing-my-notes
Thinking it through Sept. 16, 2022 I'm currently publishing via Blot. It's an excellent service and has recently launched support for ...

other

- a template [script](https://fulcra.design/) to add meta data to your notes Q.Q
  YAML title, date, and lastmod field. This facilitates integration with Quartz/Hugo. It requires MetaEdit

##### pure markdown readers
- browse repo on github
- [markdown viewer](https://chrome.google.com/webstore/detail/markdown-viewer/ckkdlimhmcjmikdlpkmbgfkaikojcbjk?hl=en) chrome extension
	- works barebones
	- issues:
		- no side bar
		- no filename title
		- no wiki links to other .md files
		- (minor issue) no plugins 
			- no backup (git) 
			- no search
			- no tags
- [ ] look into this chrome [extension](https://chrome.google.com/webstore/detail/obsidian-web/edoacekkjanmingkbkgjndndibhkegad) to search notes for a webpage

### make my own solution
#todo 

- [x]  [[Create a site with mkdocs]]
- [x] [docs](https://squidfunk.github.io/mkdocs-material/setup/adding-a-git-repository/#repository-icon) add edit btn
- [x] wikilinks
- [x] auto build git action
- [x] transfer other branch action
- [ ] setup submodules for clean approach?
- [ ] test with this 3rd party [repo](https://github.com/bralkor/unreal_python_recipe_book?tab=readme-ov-file) and make a PR showing of the build site, see [[Github markdown to site]]

hashtag support to material
- update [this issue](https://github.com/mkdocs/mkdocs/issues/2087#issuecomment-1272116074) if solution is found
- material supports tags in note header, not same convention as obsidian, [docs](https://squidfunk.github.io/mkdocs-material/setup/setting-up-tags/#tag-icons-and-identifiers), [testpage](http://127.0.0.1:8000/folder1/tags/#hashtag1)

goal: a repo you can clone, and all you need to change is settings/drop docs folder in.
option to submodule it.
bonus:
provide link to your notes repo, submodule, auto set settings.

- take a mkdocs template
- only obsidian notes on main (and github workflow)
- workflow copies files to documentation 
- documentation copies files to gh-pages

optional
- [ ] ability to only add github workflow, pulls documentation from hannes repo and sets up new branch
- [ ] support submodules pull latest



- [ ] find a solution to implement this.
- [ ] if notes are in URLs, how can a note be renamed without changing the URL.
	This would break links.
	notion uses a GUID
	[Andy](https://notes.andymatuschak.org/About_these_notes?stackedNotes=z8AfCaQJdp852orumhXPxHb3r278FHA9xZN8J&stackedNotes=z4SDCZQeRo4xFEQ8H4qrSqd68ucpgE6LU155C&stackedNotes=z4Rrmh17vMBbauEGnFPTZSK3UmdsGExLRfZz1) uses some kind of GUIDs, good reference
- [ ] edit on the web
	to support non-tech community
	no need to know git
- [ ] preview on hover, see [Andy](https://notes.andymatuschak.org/)
	- obsidian supports this when pressing ctrl, try it: [[Obsidian improvements]]
#obsidian #notes

Obsidian is running Electron, which apparently is easy to port to the web

challenges
- wiki links not by default supported in markdown
- requires a "root" defined.
	- links are just name of doc, doesn't include folder paths
	- so needs a database?

goals
- avoid plugins that add non default markdown to file (e.g. special header info)
- easy UX to edit and auto/easy backup notes
- collapsible lists

### comments on Obsidian site
- https://forum.obsidian.md/t/comment-section-on-obsidian-publish/11252/9
- discourse
- 
### about obsidian
obsidian has a REST API
	test it [here](https://coddingtonbear.github.io/obsidian-local-rest-api/)
	access e.g. active page through code
	req: the obsidian app needs to be open 
[[Obsidian special formatting]]

[[wikilink]]

[test](my%20app%20launcher.md)