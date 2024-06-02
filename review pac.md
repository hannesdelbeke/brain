review of the first pipeline as code i wrote (now named pac2 oddly enough)
[[pipeline as code]]
## Summary
- had a working prototype in days
- has been finished after a few more days i think.
- then slowly started to evolve out of hand.
- eventually died since never finished "perfectly"
## Breakdown
The original goal was: create [[Pyblish]] but better, since PRs to fix it didn't work out. I was bothered by all the [[Pyblish issues]] so decided to restart from a clean slate. 

First I researched all the things that bothered me with Pyblish, and tried small prototypes to address them. After a few days I had a nice prototype for pac. It went fast, mainly because I was so immersed (obsessed) in Pyblish and validation at the time.
It hit all the goals Pyblish aimed to address, but cleaner. 

> [!WARNING]  I failed to finish the project because
> - I tried to [[feature creep|add more functionality]]. Make it more generic, so it's not just a validation system, but also a pipeline that can be used for batching, exporting, or cicd.
> - I got distracted making the [[perfection|perfect]] code & architecture. Making advanced meta classes that perhaps over [[abstraction|abstracted]] the code. With the goal to keep things extremely simple for the user.

I since have had to make 2 or 3 validation systems at other jobs, and fell back to using Pyblish since it works out of the box. But it sucked and reflected in a subpar validation system being rolled out. 
Meanwhile I had this working prototype lying around, but since it wasn't finished it didn't feel ready use at work. I don't want to bring unfinished projects in work and end up being biased and coding on my little fun project during work.

> [!NOTE] How could I have prevented this? 
> Assuming no [[hindsight]], I could have focused more on the goals, the [[objectives and key results|OKRs]] of the enduser. Once they were hit, I should have made a release and gotten test users.
## Things I learned.
- i was trying to make a [[graph theory|graph]], so researched a bunch of existing solutions and wrote notes.
- nodes don't need `self.id` since python objects all have an id `id(my_object)`
- nodes don't need a name, since all python objects have a name. `self.__class__.__name__`
- nodes don't need actions, since all python objects have methods, which can be private or public.
- i was a bit fuzzy on the exact way, but nodes have connections. since they are always called by another node, which can be (recursively) accessed through the caller_object, using `inspect.stack()`. (Code felt little hacky but did the job)
- i could do complex class manipulation, e.g. [[overriding]] `def __setattr__` so we always stored a link to the node assigned to an attribute. This was really cool but mainly ended up abstracting things. Nice when stuff worked, but a lil harder to debug.
- serialization, config and raw config are surprisingly confusing. Might have made more sense to split that up. see [[composition vs inheritance]].
- nodes don't need a run method, since python objects have `__call__`

[[my progamming review]]