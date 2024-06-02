# No silver bullet 1987
## Summary
"No silver bullet" talks about why software is difficult, past discoveries that improved productivity, what could improve it, and what people think would but likely won't. 
A silver bullet refers to magic solution for all your problems.

read it [[No_Silver_Bullet_Essence_and_Accidents_of_Software.pdf]]
discuss https://wiki.c2.com/?NoSilverBullet

## Notes
### software is difficult
- **complexity** leads to difficult communication, bugs, etc. this also is a big topic in [[A Philosophy of Software Design]]
- **conform**: all software is different, different interfaces etc.
- **changeable**: easy to change unlike real life buildings, cars, … so it's more tempting to introduce changes mid production.
- **invisible**. you can't see software, you can't easily draw a representation. 2 minds struggle to communicate. [^1]

> [!NOTE]
>   In project planning, [[The DevOps Handbook]] recommends to visualise invisible work (e.g. on a task board)  

## past breakthroughs
- **high level languages** make devs more productive. Removing some complexity.
- **time sharing**, not really understanding this. Seems related to submitting jobs in a queue
- **Unified programming environments** make it easier to use apps together. And create reusable tools

I'd add sharing code and libraries to this, e.g. open source, package repos, ..

### hopes for future breakthroughs
- Ada and other **high-level language advances**: a specific language, seems outdated. Described as likely not a breakthrough
- **[[Object oriented programming]]**. removes some complexity but not enough. [^2]
- **[[Artificial intelligence]]** Author did not expect AI to have a big impact [^3] [^4] 
  `but was wrong, 35 year later AI is taking over` 
- **Expert systems**: A rule based manual written "AI" system. [^3][^5]
*The most powerful contribution by expert systems will surely be to put at the service of the inexperienced programmer the experience and accumulated wisdom of the best programmers.*
`This basicly describes chat GPT.`
- **Automatic programming**:  dated, chatGPT now can help here. [^5]
- **Graphical programming** [^6][^7]
	- argues flow chart is a bad representation [^8], devs draw flowcharts after, not before
	- screens are to small. `dated, now you can zoom easily e.g. on Miro`
	- difficult to visualize
	These days node-based programming has it's place, e.g. [[Unreal]]'s material editor & [[Unreal Blueprints Visual Scripting|blueprints]]. It does often result in messy spaghetti though.
- **Program verification**: testing & bug fixing. Unit testing doesn't save much labor, since you need to write & maintain the tests.
- **Environments and tools** expect marginal improvements.
- **Workstations** Better GPU, CPU Ram won't reduce think-time for a dev. Slightly dated since GPU advancements lead to AI, which significantly sped up dev process. Increase of hardware also enabled cloud.

## so what can we improve
all productivity improvements are limited by (reminds me of [this xkcd](https://xkcd.com/1205/))
$$Time of task=∑(Frequency×Time)$$
If most time is spend on the concept, instead of the technicalities of software, then focusing on improving technicalities wont improve productivity much.

**Buy versus build**. The most radical possible solution for constructing software is not to
construct it at all. Proposes marketplace for modules [^9]
- saves money
- but can it be applied to my problem?
	- people used to buy custom programs, now they buy of the shelves. Because a computer used to be 2mil, an extra 250k for software was ok. Now a computer is 50k, so custom software is relatively much to expensive.
- spreadsheets have solved many problems, removing need for custom apps.
- many computer users now solve problems without any coding knowledge 

**Requirements refinement and rapid prototyping**
*The hardest single part of building a software system is deciding precisely what to build...*
*No other part of the work so cripples the resulting system if done wrong. No other part is more difficult to rectify later.*

- client doesn't know what they want exactly. Plan for iterations
- it's impossible to set final specs before trying a version of the product
- rapid prototyping tools promise big productivity gains
- prototype the important interfaces, and perform the main functions. without worrying about performance or hardware limits. main purpose is so client can test it.
- present day development (1987) relies on final specs before starting development, which is flawed. Instead you should build (not write) incrementally.
- building is now dated, living things grow instead. [^10]
	- first make it run
	- bit by bit flesh it out, with calls to empty stubs.
	- improved performance & understanding with students#
	- ⚠️ One always has, at every stage in the process, a working system [^11]
	
**Great designers**
- To improve the software, you need good people
- Good design practices can be taught, and can change poor design in to good designs
- But won't turn good designs into great ones. Great designs come from great designers.
*Study after study shows that the very best designers produce structures that are faster, smaller, simpler, cleaner, and produced with less effort. [^12] The differences between the great and the average approach an order of magnitude.*

- So the most important single effort we can mount is to develop ways to grow great designer
	1. reward amazing devs with huge salary, perks, status. (FAANG does this now)
	• **Identify top designers early**, the best are often not the most experienced.
	• Assign a career mentor responsible for the development of the prospect, and keep a career file.
	• Devise and maintain a career development plan for each prospect, including carefully selected apprenticeships with top designers, episodes of advanced formal education, and short courses, all interspersed with solo-design and technical leadership assignments.
	• Provide opportunities for growing designers to interact with and stimulate each other.

> [!Issues ]- 
> This argument has 2 flaws. 
> - It assumes we can identify a top designer.
> - It rejects anyone who is not a top designer.
> 
> #### identify top talent
> Google found that dev interview scores had no correlation with performance, of devs who got hired. [source](https://www.forbes.com/sites/forbeswealthteam/2023/06/15/the-richest-person-in-every-state-2023/?sh=57e1f4d25567)
> Anecdotes:
> - Albert Einstein was seen as lazy when young.
> - Michael Jordan was rejected cause he was to short when he was young
> - Stephen King was rejected by 30 publishers before becoming famous.
> 
> #### improve average designers:
> - higher teacher wages likely lead to better students, [article](https://www.educationnext.org/do-smarter-teachers-make-smarter-students-international-evidence-cognitive-skills-performance/)
> - the [[social how our brains work]] book recommends to focus on the social aspect, try teaching and explaining your program to others. To help with this shared vocabulary is extremely helpful, such as [[connascence]].
> - find out how to motivate people so they want to learn more. e.g. I personally enjoy programming, it's fun.

## REFERENCES
[^1]: D.L. Parnas, "Designing Software for Ease of Extension and Contraction," IEEE
Transactions on Software Engineering, Vol. 5, No. 2, March 1979, pp. 128-38.
[^2]: G. Booch, "Object-Oriented Design," Software Engineering with Ada, 1983, Menlo
Park, Calif.: Benjamin/ Cummings.
[^3]: lEEE Transactions on Software Engineering (special issue on artificial intelligence
and software engineering), l. Mostow, guest ed., Vol. 11, No. 11, November 1985.
[^4]: D.L. Parnas, "Software Aspects of Strategic Defense Systems:" American Scientist,
November 1985.
[^5]: R. Balzer, "A 15-year Perspective on Automatic Programming," IEEE Transactions
on Software Engineering (special issue on artificial intelligence and software
engineering), J. Mostow, guest ed., Vol. 11, No. 11 (November 1985), pp. 1257-67.
[^6]: Computer (special issue on visual programrning), R.B. Graphton and T. Ichikawa,
guest eds., Vol. 18, No. 8, August 1985.
[^7]: G. Raeder, "A Survey of Current Graphical Programming Techniques," Computer
(special issue on visual programming), R.B. Graphton and T. Ichikawa, guest eds.,
Vol. 18, No. 8, August 1985, pp. 11-25.
[^8]: F.P. Brooks, The Mythical Man Month, Reading, Mass.: Addison-Wesley, 1975,
Chapter 14.
[^9]: Defense Science Board, Report of the Task Force on Military Software in press.
[^10]: H.D. Mills, "Top-Down Programming in Large Systems," in Debugging Techniques in
Large Systems, R. Ruskin, ed., Englewood Cliffs, N.J.: Prentice-Hall, 1971.
[^11]: B.W. Boehm, "A Spiral Model of Software Development and Enhancement," 1985,
TRW Technical Report 21-371-85, TRW, Inc., 1 Space Park, Redondo Beach, Calif.
90278.
[^12]: H. Sackman, W.J. Erikson, and E.E. Grant, "Exploratory Experimental Studies
Comparing Online and Offline Programming Performance," Communications of the
ACM, Vol. 11, No. 1 (January 1968), pp. 3-11.
Brooks, Frederick P., "No Silver Bullet: Essence and Accidents of Software Engineering,"
Computer, Vol. 20, No. 4 (April 1987) pp. 10-19.
