[source](https://adamj.eu/tech/2022/06/17/mike-actons-expectations-of-professional-software-engineers/)

1. **I can articulate precisely what problem I am trying to solve.**
    
    It’s all too easy to get stuck in the weeds and lose track of why you’re doing what you’re doing. Keep top of mind what the actual end goal is do, and you might spot an alternative path.
    
2. **I have articulated precisely what problem I am trying to solve.**
    
    Communicate the problem “out loud” to other team members, your product manager, etc.
    
3. **I have confirmed that someone else can articulate what problem I am trying to solve.**
    
    Communication! Ensure your team is all on the same page. Make sure your understanding of the problem is complete.
    
4. **I can articulate why my problem is important to solve.**
    
    If you solve the problem you’re working on, who benefits, and how much?
    
5. **I can articulate how much my problem is worth solving.**
    
    If you say it’s worth “as long as it takes”… Mike does not have friendly words for you. For _any_ problem there’s a maximum amount of time and effort worth investing in solving it. At least have some idea of the upper bound.
    
6. **I have a Plan B in case my solution to my current problem doesn’t work.**
    
    Imagine you’re days or hours before the deadline, and you can tell that completing Plan A will be impossible. What do you do instead? Maybe you have a simplified algorithm, or you can disable a certain subsystem. Have more than one plan.
    
7. **I have already implemented my Plan B in case my solution to my current problem doesn’t work.**
    
    Mitigate risk by writing the backup version first. This means you always have a safety net and you can learn more about the problem space in order to iterate on Plan A.
    
8. **I can articulate the steps required to solve my current problem.**
    
    Programming only works when you break down problems into manageable chunks. Have a sketch of the steps to the end state before you begin.
    
9. **I can clearly articulate unknowns and risks associated with my current problem.**
    
    There are always going to be things you don’t know. You should know where they are in your plan, so you can manage them.
    
10. **I have not thought or said “I can just make up the time” without immediately talking to someone.**
    
    Say it’s Wednesday, you have a project due on Friday, and you get some new task dropped on your lap. You think “I’ll do the new thing now, and make up the time for the original task by Friday”… mistake! Communicate about the conflict on Wednesday. Your product manager will help manage the timing and risk.
    
11. **I write a “framework” and have used it multiple times to actually solve a problem it was intended to solve.**
    
    If you’re writing a tool of some kind, you should verify it works in practice. Too often people create something in isolation and it doesn’t end up delivering in the real world.
    
    (This is [how Django came to be](https://docs.djangoproject.com/en/stable/faq/general/#why-does-this-project-exist): from a real team making real websites, on deadlines!)
    
12. **I can articulate what the test for completion of my current problem is.**
    
    If you don’t know when to stop, you might find yourself going down rabbit holes, chasing unimportant marginal gains.
    
13. **I can articulate the hypothesis related to my problem and how I could falsify it.**
    
    If a hypothesis cannot be proven wrong, there’s no knowledge to be gained. As Karl Popper showed, science only works through [falsification](https://en.wikipedia.org/wiki/Falsifiability).
    
14. **I can articulate the (various) latency requirements for my current problem.**
    
    Any time you write code, you should consider when the output data is required. Not every caller needs output data instantly, and nor do you have an unbounded amount of time to perform everything. At least get an idea of the sensible bounds.
    
15. **I can articulate the (various) throughput requirements for my current problem.**
    
    How much data needs to come through the system? How many bytes, requests, or frames per second?
    
16. **I can articulate the most common concrete use case of the system I am developing.**
    
    You should know what actual users of your system will actually be doing most of the time. Having a vague idea doesn’t help, since knowing which pattersn are common informs which way to write a given piece of code.
    
17. **I know the most common actual, real-life values of the data I am transforming.**
    
    Beyond use cases, you should know the data inside the system. For example, if your function works with integers, you’d probably write it quite differently if 99% of the values are 0.
    
18. **I know the acceptable ranges of values of all the data I am transforming.**
    
    Computer systems always have limits. Know the ranges for the data types you’re working with (and enforce them).
    
19. **I can articulate what will happen when (somehow) data outside that range enters the system.**
    
    Murphy’s Law says “anything that can go wrong will go wrong”. Know how your system will behave in such cases, and handle such problems if necessary.
    
20. **I can articulate a list of input data into my system roughly sorted by likelihood.**
    
    Have an idea of the space of possible data, what’s most likely, second most likely, etc. Code appropriately, for example checking for common error conditions first.
    
21. **I know the frequency of change of the actual, real-life values of the data I am transforming.**
    
    Reason about the frequency of change and figure out how often you’ll want to calculate derived values.
    
22. **I have (at least partially) read the (available) documentation for the hardware, platform, and tools I use most commonly.**
    
    Read the friendly manual! Go a step beyond day-to-day reference, and try reading the full documentation to gain a deep understanding.
    
    (Jens Oliver Meiert calls reading the HTML specification [the Web Developer’s Pilgrimage](https://meiert.com/en/blog/web-developer-pilgrimage/).)
    
23. **I have sat and watched an actual user of my system.**
    
    Watching users can massively break shift your view of how your software works. Do it!
    
24. **I know the slowest part of the users of my system’s workflow with high confidence.**
    
    Any workflow has a bottleneck. Make sure you know what it is so you can focus efforts there, if need be.
    
25. **I know what information users of my system will need to make effective use of the solution.**
    
    Think about what documentation or data users need to understand and use your solution.
    
26. **I can articulate the finite set of hardware I am designing my solution to work for.**
    
    Software requires hardware. Know what hardware your program targets, such as:
    
    - CPU architectures
    - Minimum requirements for memory, CPU speed, and network bandwidth
    - Input devices
    - Output devices
    - The environment the hardware runs in (e.g. data centre or living room)
27. **I can articulate how that set of hardware specifically affects the design of my system.**
    
    If you’re targetting low end devices, how do you ensure you don’t exhaust memory? If some users don’t have pointing devices, how do you accommodate them?
    
28. **I have recently profiled the performance of my system.**
    
    If you’re developing a local app, run profiling tools regularly to gain an idea of performance over time. With server based programs, you can install an APM (Application Performance Monitoring) tool in production and have continuous profiling data.
    
29. **I have recently profiled memory usage of my system.**
    
    Make sure you aren’t wasting memory.
    
30. **I have used multiple different profiling methods to measure the performance of my system.**
    
    There’s no perfect profiling tool, so know how to use more than one.
    
    For example, some great Python profilers are [cProfile](https://docs.python.org/3/library/profile.html), [py-spy](https://github.com/benfred/py-spy), [Austin](https://github.com/P403n1x87/austin), [Scalene](https://github.com/plasma-umass/scalene), [Fil](https://pythonspeed.com/fil/), and [memray](https://bloomberg.github.io/memray/). They all have different characteristics and complement each other.
    
31. **I know how to significantly improve the performance of my system without changing the input/output interface of the system.**
    
    Do you know the next step to optimize your system? You don’t have to do it right now, as it may not be worth it, but you should have an idea what you’d do next to make your code faster. For example, use a faster but less convenient data structure, or convert a hot function into a faster language (such as Python to C with Cython).
    
    This should also guide you to designing interfaces that are optimizable in the first place. For example, don’t commit to returning expensive-to-compute results immediately, but instead return a promise.
    
32. **I know specifically how I can and will debug live release builds of my work when they fail.**
    
    Bugs are inevitable. You should know the tools that will let you work through those problems in production, such as logs, debuggers, or a live shell.
    
33. **I know what data I am reading as part of my solution and where it comes from.**
    
    Know where the data comes from, in what format, and how you can read it.
    
34. **I know how often I am reading data I do not need as part of my solution.**
    
    Data access is rarely optimal. You’ll often be moving data that’s not required for your solution, such as unnecessary fields or wrapper objects. If you don’t know about this waste, you can’t reason about whether it’s worth the overhead or not.
    
35. **I know what data I am writing as part of my solution and where it is used.**
    
    All output data is intended for use by a human or another program. Be organized enough to know what the downstream consumers of your output are.
    
36. **I know how often I am writing data I do not need to as part of my solution.**
    
    Data output is also rarely optimal. Are you frequently writing out data that hasn’t changed? Are you writing many fields when only one is used downstream? Again, know about it so you can reason about it.
    
37. **I can articulate how all the data I use is laid out in memory.**
    
    Many programming languages and frameworks can handle memory for you, but that doesn’t abdicate you of responsibility. Know how your tools lay out memory, so you can tell when another approach makes sense.
    
    For example, in Python most objects are based on dictionaries, so you should have a solid understanding of how they work, and alternatives like [slotted classes](https://docs.python.org/3/reference/datamodel.html#slots) or [arrays](https://docs.python.org/3.10/library/array.html).
    
38. **I never use the phrase “platform independent” when referring to my work.**
    
    Any system depends on many things below it. Know what they are.
    
39. **I never use the phrase “future proof” when referring to my work.**
    
    Future-proofing is “100% a fool’s errand”. “You can’t pre-solve problems you have no information of.”
    
40. **I can schedule my own time well.**
    
    “You’re an adult person, just use a calendar.”
    
41. **I am vigilant about not wasting others’ time.**
    
    Don’t waste time asking questions that you can google in five seconds. But also don’t waste loads of time struggling for days alone when you could get help from a team member in minutes! Find the balance.
    
42. **I actively seek constructive feedback and take it seriously.**
    
    Ask for feedback and do something about it.
    
43. **I am not actively avoiding any uncomfortable (professional) conversations.**
    
    If there’s something wrong at work, don’t put off talking about it.
    
44. **I am not actively avoiding any (professional) conflicts.**
    
    If you’ve noticed something is going wrong, whether technically or communication wise, get those conflicts out in the open. Letting them stew never helps.
    
45. **I consistently interact with other professionals, professionally.**
    
    Be courteous and professional! Mike jokes about setting an incredibly low bar: no yelling, no hitting, …
    
46. **I can articulate what I believe others should expect from me.**
    
    Have a standard for yourself and be ready to tell your co-workers what it is.
    
47. **I do not require multiple reminders to respond to a request or complete work.**
    
    “Waiting for someone else to poke you is not an effective way to get your job done.”
    
48. **I pursue opportunities to return value to the commons (when appropriate).**
    
    All our work builds on top of the work of countless others. At some point, you’ll have opportunities to give back to the community at large. For example, talking at meetups, making open source contributions, or even just discussing topics with your team to boost everyone’s skills.
    
49. **I actively work to bring value to the people I work with.**
    
    You’re part of a team, so work to help them.
    
50. **I actively work to ensure under-represented voices are heard.**
    
    Don’t stand by leaving this to be someone else’s problem. Do something to make sure that minorities are heard. This might mean ensuring that the minority person at work gets a chance to speak, that your hiring process is unbiased, or that your website is accessible for users who rely on screen readers.

[[programming]]