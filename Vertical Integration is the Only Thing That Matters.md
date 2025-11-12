Article [source](https://becca.ooo/blog/vertical-integration)  - 2025-11-10

On the subject of developer tooling, or perhaps computer programs more broadly, I have become increasingly convinced that vertical integration is the only thing that matters. I also think that the inability of developer productivity startups to vertically integrate their offerings has hindered their adoption and utility. I’d like to talk about what I mean by “vertical integration” and why we don’t have it today.

## What is vertical integration?

When I say “vertical integration”, I am referring to tight integration between different tools in a stack.

Here are some workflows that are possible with a vertically-integrated stack:

1. You create a new branch and build the project you’re working on. You haven’t made any changes yet, so the build finishes in under a second because your build system shares artifacts with builds from CI and deploys. This build system also caches artifacts from builds you initiate locally, so a coworker who checks out your branch (also a single click from the PR) will be able to run your code immediately.
    
2. A test fails in CI. You click a button to open the failing test in your editor, which gives you an interactive call-stack (potentially spanning multiple binaries and programming languages) to explore.
    
3. A check on your PR fails because your code wasn’t formatted correctly. You click a button to apply the formatting changes directly to your code, and they’re immediately reflected in your editor.
    
4. You merge a PR which breaks a service. Your PR is initially deployed as a canary to a small portion of clients. The deploy system detects an elevated failure rate, and rolls back your PR automatically. This adds a note to your PR and messages you on your Slack-equivalent. The note indicates which checks failed, and you can click them to see a history of those checks.
    
5. You click on a function in your editor and are presented with a list of usages of that function. The list includes entries from other projects, written in other languages, and across RPC boundaries.
    
6. A service crashes in production. A ticket is automatically opened and routed to your team (or a note is added to an existing ticket). You click a button to open the line of code that crashed in your editor, and again you’re shown an interactive call-stack for the failure.
    

All of these workflows span multiple parts of the stack: local builds and CI builds, the test runner and the editor, the code review system and CI, the deploy system and version control. These features are often derisively referred to as “[[glue code]]”. **The glue code _is_ the vertical integration work.**

I’d like to draw your attention to a couple different themes here:

1. None of the features here are particularly shocking, but they all require cooperation between tools that aren’t used to cooperating. Your test runner knows the call stack of a failing test, but it can’t make that information available in a format your editor or terminal is able to consume. Your deploy system runs an optimized build and then throws away all the artifacts, so if you want to build the same commit you need to start from scratch. The compilation was already run, but your build system isn’t able to grab artifacts from CI because your build system doesn’t know that you _have_ CI.
    
2. [[integrated development environment|IDEs]] make some of these workflows possible, albeit scoped to a single project. This is because IDEs implement glue integrations between a bunch of different test runners, build systems, languages, and so on.
    
3. Many of these workflows require infrastructure to be running independently of your CI, deploy system, and developer workstations. If you want CI to tell you if a test has failed recently in other builds, you need a system that knows when that test was run and what the results were. If you want to share build artifacts between CI and developer builds, you need a system to cache those artifacts and accurately identify when they can be reused.
    

## Why isn’t a vertically-integrated stack the default?

The reasons why vertically-integrated stacks aren’t common are a bit different for open source and industrial users, but industry funds open source so there’s a fair amount of overlap.

### Vertical integration in open source

Open source projects tend to be miniscule. Even projects with hundreds of thousands of lines of code are uncommon, while codebases of that size seem quaint to industrial engineers.

While I’m sure that many engineers would enjoy having access to the workflows I described at the start of the post, the motivation is a lot less pressing. Who needs shared build artifacts when a clean optimized build takes a couple minutes? Who needs integration between the test suite and the code editor when the entire codebase fits in the working memory of the only engineer who seriously works on it? And gradual rollouts don’t even make sense when the project doesn’t publicly provide a hosted instance of the software.

Integrated stacks also present a coordination issue for open source projects. Does the integration between the test runner and the code editor live in the test runner or the code editor? How is it tested? Open source is full of petty kings and overgrown forum moderators, so this sort of collaboration is rarely feasible in practice.

Open source is also full of software freedom acolytes who insist that each tool must “do one thing well.” To these engineers, project A maintaining an integration with project B is a threat to the ability of users to swap out project B for a different tool; the best approach, to them, is for every tool to behave as if no other tool exists. The fact that this results in strictly less-capable tools seems to be lost on these engineers.

At the same time, many open source projects are owned or funded largely by a single corporation with no motivation (or ability) to make their internal stack available externally. Any integrations in the project must therefore be compatible with the stack used by those corporations internally. For similar reasons, it is also common to see projects with test suites or build systems that cannot be used outside of the organization that funds them.

### Vertical integration in industry

Industrial users aren’t interested in a smooth developer experience because it makes engineers’ lives easier. Industrial users want a vertically-integrated stack because engineer time is _expensive._ This means that a vertically-integrated stack must save time in an absolute sense; that is, _including_ the time it takes to implement and adopt the system.

These migration costs push industrial users away from tools that span the stack. When startups are small, the overhead of implementing such a system increases the likelihood that the startup will fail. An organization must be stable enough in order for spending time on integration work to be justifiable. But once an organization _is_ stable enough to want to build out a smoother developer experience, they’ve already developed their own bespoke build and deploy system, often spanning multiple repos with complex dependencies and subtle quirks. At this point, the costs of switching to an off-the-shelf vertically-integrated stack are prohibitively large.

Organizations that investigate e.g. switching to Bazel will hear horror stories of migration efforts that went on for years before being scrapped. This is another issue with implementing tight vertical integrations across the stack: deep investment is needed, over an extended period of time, in order for benefits to materialize. Many younger organizations used to bringing features from planning to production in one or two quarters find this sort of investment very challenging to justify.

### Vertical integration as a product

Could we build a vertically-integrated development environment as a product and sell it to companies who would otherwise build a similar but less-capable system internally? On the surface, this sounds like a great idea: lots of organizations are devoting a lot of effort to building out pretty similar systems for building, deploying, and editing code. It would be fantastic if we could centralize that effort, saving each organization valuable engineering time while delivering a better experience.

But remember what we’re talking about: integrations between a code forge, build system, deploy system, CI, and code editor. Large organizations are either unwilling or unable to adopt radically different tools. Your developer tools startup will then need to build and maintain integrations between _N_ products for each of your _M_ large clients. At the same time, you’ll have to compromise on features; if you can’t ship a patch to GitHub, you can’t build a link to open a failing test case locally into their UI.

Selling integrations is also a risky position for a company to be in. There’s a natural incentive for the companies being integrated to write replacement integrations in-house and claw back some of the profits that are going to the external competitor. Vendors selling integrations may also find themselves in an uncomfortable position when the services they’re integrating with raise their prices or restrict API access. Cursor, for example, had to [hastily change their pricing](https://techcrunch.com/2025/07/07/cursor-apologizes-for-unclear-pricing-changes-that-upset-users/) after Anthropic changed their prices. Cursor also had to [beg Microsoft to unban Cursor](https://devclass.com/2025/04/08/vs-code-extension-marketplace-wars-cursor-users-hit-roadblocks/) from the VS Code extension marketplace. Anthropic and Microsoft both view Cursor as a competitor and would rather they did not exist at all. This is not a foundation for a dynamic of productive collaboration between these companies on integrations between their services!

For smaller organizations, adopting an integrated developer environment requires a huge leap of faith. GitHub is a very well-known and mature product. Every enterprise developer tool provides a GitHub integration (not as good as first-party support, but much better than nothing). What if the organization providing your developer tooling shuts down? It will be extremely challenging to convince early adopters that the costs are worth it. The migration costs we discussed earlier also apply to _leaving_ such a system, except that users may find themselves _forced_ to leave such a system with little notice.

[Scott Kennedy notes in “It’s not just an IDE: building the developer cloud is hard”](https://www.scottkennedy.us/developer-cloud.html) that it’s possible to build a _piece_ of the vision successfully, but benefits remain limited without cooperation from the rest of the stack:

> Startups or open source historically focused on one piece of the puzzle. Sourcegraph has been working hard for a decade just to get the CodeSearch piece right. Bazel might be open source, but it has a “batteries not included” feel. The full experience requires putting many pieces together. It’s hard.

When (e.g.) code search and the build system are produced by different corporations, the profit motive discourages corporations from building tight integrations with other products in the same space.

The vertical integration, the glue code linking these different products together, really is the thing that creates the value here. And the glue code is inherently tied to the quirks of the infrastructure of the corporation that built it:

> We’ve also seen dozens of companies successfully take Google/Facebook’s internal tooling ideas and build billion dollar B2B SaaS companies. So where is my developer cloud?
> 
> It doesn’t exist because it’s really fucking hard.
> 
> Google can’t make theirs available because they can’t disentangle from their internal architecture without damaging their internal productivity. I know because I was there when they tried. It’s hard.

The value comes from the whole stack being tightly integrated. If you can’t ship the whole stack, you’re very limited in the features you can provide. Glue code is very challenging to sell. Vertical integration is the only thing that matters.

[[programming]]
[[CICD]]
[[tooldev]]