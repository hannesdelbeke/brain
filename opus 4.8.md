> [!summary] eli5
> anthropic's opus 4.8 is the previous opus generation, the baseline fable 5 is measured against, and still widely deployed as a default in august 2026.
> done: records its benchmark position and its cache threshold.
>
> **needs from you:** nothing

> create a note for each model in the august 2026 landscape scan, then wikilink mentions of them in existing notes

**why:** [[AI model comparison august 2026]]

## what it is

the generation before [[opus 5]], and the baseline [[fable 5]] is measured against: 88.6% SWE-bench verified and 69.2% SWE-bench pro, where fable 5 reaches 95.0% and 80.3%.

## cost behaviour

a 1024-token minimum cacheable prefix, the same tier as sonnet 5, double opus 5's 512. the threshold is not monotonic across generations, so an older model is not reliably the more forgiving one: opus 4.7 needs 2048 and opus 4.6 needs 4096. a prompt sized for one model can therefore stop caching entirely when the model id changes, silently and with no error.

that is the reason a superseded model keeps carrying traffic long after it is beaten on both benchmarks: the default is stickier than the leaderboard, and the switch has to be made deliberately rather than assumed.
