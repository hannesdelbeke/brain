A [[batcher]] [[3ds max tool]] to run scripts on multiple max files for [[VuCity]] tiles

It mostly was used to run the [[VuCity validator]] overnight on 100s of scenes, auto fix any issues it finds, log the fixes it did, and log the scenes it couldn't fix.

![](vucity_batcher.jpeg)

> [!NOTE]- tool features
> ### select task
> - a dropdown list to select the task to run, 
>   e.g. pull latest from [[Perforce|p4]], fix scene, save, re-export, add to changelist
> ### input
> - add scene - add a single path to a max file
> - add folder - add all max files in a folder
> - discover local scenes - i remember there was an option to select & process all vucity tiles.
>   like a [[preset]] folder
> ### actions
> - [[copy paste|copy]] paths to clipboard 
> ### run task
> - process - run the script on all scenes in the same open max instance
> - process crashfree, opens a new [[maxbatch]] instance for each scene, so a crash doesn't stop the whole batch.
> - [[qt loading bar]]
> 
> each script has 3 stages
> - pre load setup
> - main script
> - post script action. e.g. save scene
> 
> output is saved to a log, that can be loaded in an UI to see what worked/failed
> pure python, no maxscript (except for a single render related task)

> [!NOTE]- learnings
> the batcher saves tons of time. ==tile implementation went from months to hours==.
> 
> empowers artists & TAs to do more iterations, deliver faster to clients, try out things
> - want to test a prototype with all Tiles lodded? 
>   sure that only takes hours instead of a week now.
> -  faster bug fixing: 
>    discovered a bug on all assets, only make a single `fix update` and run on all assets.
>    
> customizable and [[modular]] 
> supports templates for different actions that are reusable
> - template for validation
> - template for auto fix
> - template for lodding
> 
> spit out a batch report, which scenes failed to process.
> allow a report of reports, e.g. for validation, we can create a list of all validation reports, 1 for each scene, which is read into the log reader tool as a "master report"



