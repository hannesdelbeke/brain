a [[batcher]] tool to run scripts on multiple maya files

![](vucity_batcher.jpeg)

## challenges
...
## breakdown

- input scene list
	- discover local scenes
	- pull scenes from [[Perforce|p4]]

- run script on scenes.
	- each script has 
		- pre load setup
		- main script
		- post script action. e.g. save scene

- output is saved to a log, that can be loaded in an UI to see what worked/failed
- python only 

### learnings
- saves tons of time. implement tiles went from months to hours.
- empowers artists & TAs
- gives TA team more flexibility
	  want to test a prototype with all Tiles lodded? 
	  sure that only takes hours instead of a week now.
-  faster bug fixing
	  discovered a bug on all assets, only have to make a single fix update and run on all assets.
- customizable. supports templates for different actions that are reusable
	- template for validation
	- template for auto fix
	- template for lodding
- spit out a batch report, which scenes failed to process.
	- allow report of reports, e.g. for validation

[[Maya tool]]
[[VuCity]]