# guidelines maya tooling
a guide on writing shared tools between projects

# goals:
- fast code iterations
- stable tools that artists can trust
- reuse code

# split code in UI and functionality

reason:
- can reuse code between tools
- can run code from command-line, making it easy to upscale tools into batchform, or hook them up to a job on a runner in the cloud

examples:
- exporter tool becomes batch exporter tool
- scene validator tool reuses code from an old screenshot tool 
    

## in depth example
the exporter tool can be split into :
- an ui window with an export button (see img above)
- an export function
these both live in separate python files
the export function is generic and can be reused between tools and projects
the UI is specific to the tool and lives in the tool specific folder

the export function is hooked up to the UI export button

any project specific functions, such as a project specific export. live in a project specific shared function location
these are separate from the generic functions such as generic export function
  
# code distribution
for now perforce will be an exact read only copy of bitbucket
we need a CI / jenkins job for this. else copy paste and submit manual for now.
dirty, not ideal solution but fast

all artists will use perforce, not everyone will use git. git is also harder to use
so distribute tools through perforce

# trust between art & tech art
artists need to trust our tools. else they won't be using it for deadlines, and eventually stop using them.

to achieve this:
- release stable tested tools
- offer instant on the spot support to artists for your tools
- keep communication channels open, be approachable
- save them time and effort, help them be creative instead of technical

stable tools can be achieved by understanding the process the artist is doing using your tool.
ideally be able to go through this yourself from start to finish so you can test it locally.
ideally we use TDD ([[test driven development]]) but this takes some time to setup at start and more dev time. if anyone has experience with TTD ping me
# code structure 
code structure should try be understandable to non coders, almost read like a sentence

so instead of 
`if(export_result ==1) : print(“success”)`
use
`if export_result is returncode.successful : print(“success”)`

use PEP8 guidelines

we should do code reviews, not only to catch errors but also to learn from each others code, and stay up to date with new added functionality in the shared code library


## note
2025 observations:
I wrote this when I still was a Lead [[technical artist]] at [[VuCity]].
It could use some better formatting.
[[tooldev]]