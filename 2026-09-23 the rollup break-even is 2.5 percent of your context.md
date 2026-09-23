> [!summary] eli5
> reading just the headings of a note is cheaper than reading the whole thing, but only if the note is big enough to pay for the extra round trip you now need to fetch the one section you wanted.
> how big is "big enough" turns out not to be a fixed number of tokens. it is about 2.5% of whatever is already sitting in your conversation. at 40k of context, roll up anything over 1k tokens. at 800k of context, read anything under 20k tokens whole, even a huge one, because the round trip costs more than the note does.
> the thing everyone gets wrong: a second round trip does not re-charge you for the whole conversation. cached tokens re-read at a tenth of list price, so the penalty is 10% of your prefix, not 100%.
> **needs from you:** nothing, unless you want the gate enforced automatically rather than followed by hand.

> if we do a hierarchical rollup we can save tokens. imagine a file with 10 descriptive headers, each with 10k tokens under it. just reading headers and filename gives a clear picture. how do we know when it's worth doing this instead of reading the whole file? i assume it depends on if we already have 800k tokens in a session — asking just headers would be cheap, but it also sends 800k as cache, and if we then see 1 header is relevant and request more text, it'll resend that 800k again. can you come up with a calculation?

**why:** [[hierarchical map-reduce note rollup]]

## the break-even is 2.5% of your current context, not a fixed note size

Solving the cost model below for typical values gives a break-even note size of 2.50% of the conversation prefix, and it stays at 2.50% across two orders of magnitude of prefix size.

| context so far | roll up notes above |
| --- | --- |
| 20k | 500 tok |
| 50k | 1,251 tok |
| 100k | 2,503 tok |
| 200k | 5,007 tok |
| 400k | 10,015 tok |
| 800k | 20,031 tok |

The scale invariance is not a coincidence, it falls out of the algebra: the round-trip penalty is proportional to the prefix and nothing else in the expression is, so the prefix cancels out of the ratio.

The practical consequence is the counterintuitive half of the answer. A big session does not make rollup more attractive, it makes rollup *less* attractive, because every extra round trip is charged against a bigger prefix. Early in a session you should route almost everything through its outline; late in a session you should read most things whole and only roll up the genuine monsters.

## a second round trip re-sends the prefix at 10% of list price, not 100%

The worry that motivates the whole question — that drilling into a section "resends that 800k again" — is true but mispriced by a factor of ten.

Under prompt caching a token that is already in the cache is re-read at roughly 0.10× the base input price, not 1.00×. So the marginal cost of one additional API call at prefix P is 0.10·P, not P. On an 800k prefix that is 80k token-equivalents per extra round trip: expensive, and the reason the threshold climbs with context, but an order of magnitude short of catastrophic.

This is also why the penalty appears exactly once in the model rather than once per strategy. Both the whole-file read and the outline read pay for at least one call. Only the drill-down adds another.

## context is a recurring tax, and that is what pays for the round trip

The other half of the pricing is that admitting tokens to context is not a one-time charge.

A token written into the cache costs about 1.25× base input once, then about 0.10× on every subsequent call in the session. So the lifetime cost of admitting X tokens with T calls still to come is:

```
k = 1.25 + 0.10 * T
lifetime cost of X tokens = k * X
```

At T = 10 that multiplier is 2.25. At T = 30 it is 4.25. A 10k-token note dumped into a long session is not a 10k-token decision, it is a 42k-token decision.

This cuts in rollup's favour and directly opposes the prefix effect: the longer the admitted content will live, the more the outline saves, because the tokens you avoided are tokens you avoid paying for on every remaining turn. At a 60k prefix the threshold falls from 2,503 tokens (T = 1) to 795 tokens (T = 30).

## the formula

Let F be the full note in tokens, H the outline (filename plus every heading), N the number of sections, S = F/N the expected section size, p the probability the outline alone is not enough, and P the current prefix.

```
read the whole note        C_whole   = k * F
outline, then maybe drill  C_outline = k * H + p * (0.10 * P + k * S)
```

Rollup wins when the tokens it avoids beat the round trip it adds:

```
F - H - p*S  >  0.10 * p * P / k
```

Substituting S = F/N and H = h·F and solving for F gives the break-even note size:

```
F* = 0.10 * p * P / ( k * (1 - h - p/N) )
```

Every term is measurable. h is 4.7% at the median on a 4,856-note corpus. N you get from parsing the file. P you get from the last usage block in the transcript. p is the only judgement call, and it is a property of how good your headings are.

## heading quality moves the threshold further than anything else you control

The drill rate p — how often the outline fails to answer the question and you have to fetch a section anyway — swings the break-even by 5.6×.

| drill rate p | break-even at 60k context |
| --- | --- |
| 0.2 | 576 tok |
| 0.5 | 1,502 tok |
| 0.8 | 2,509 tok |
| 1.0 | 3,232 tok |

A note whose headings are labels (`## Background`, `## Notes`) forces a drill nearly every time, so it behaves like p ≈ 1 and almost never repays the round trip. A note whose headings are claims lets the reader stop at the outline, and rollup pays out at a quarter the size.

That is a much stronger argument for writing headings as sentences than "it reads nicely". It is the difference between a retrieval layer that works and one that costs more than not having it. See [[header extraction for token-efficient retrieval]].

## batching ten notes into one outline call divides the threshold by ten

The round trip is a per-call cost, not a per-note cost, so M notes outlined in a single call share one penalty between them.

| notes sharing the call | break-even each |
| --- | --- |
| 1 | 1,533 tok |
| 3 | 511 tok |
| 10 | 153 tok |

This is the largest single lever in the model and it is free. A search result set should *always* come back as outlines, never as whole notes, because the marginal note in a batch of ten pays a tenth of a round trip. Serving ten hits as outlines and letting the agent pull the one section it needs is close to strictly dominant.

It also means the batch is where the win lives. Rolling up one note at a time is a marginal optimisation; rolling up a result set is not.

## most notes in a real corpus are far too small to roll up

Measured across 4,856 markdown notes: the median note is 205 tokens, p90 is 1,646, p99 is 10,106, and the largest is 168,462. The median heading count is zero.

So the rule almost never fires, and that is the correct outcome rather than a disappointment. A 205-token note has no rollup worth doing — the outline would be a third of the file and the round trip costs five times the note.

The tokens are not where the notes are, though. 761 notes over 1k tokens hold 77% of all corpus tokens; 151 notes over 4k hold 46%; 25 notes over 16k hold 23%. The rule needs to fire on about 3% of notes to govern half the corpus. A gate that is silent 97% of the time and correct on the remaining 3% is exactly the right shape.

## the token model needs a latency floor bolted onto it

The arithmetic alone will recommend rollup for a 205-token note in a small session, where it computes a saving of 89 token-equivalents.

That verdict is wrong, and it is wrong because the model prices tokens and says nothing about wall-clock. A round trip costs a second or two whether the note is 200 tokens or 200k. Trading two seconds of latency for 89 tokens is a bad deal that the cost function cannot see.

A floor of ~800 tokens fixes it: below that, read the file. This is the one place where the implementation deliberately disobeys its own formula, and it is worth flagging as such rather than quietly tuning the constants until the formula produces the answer you wanted.

## the worked example, with the surprise intact

The original question: a 100k-token note, ten headers, 10k under each, in a session already holding 800k.

Rollup wins overwhelmingly. Whole-file costs 225,000 token-equivalents; outline-then-drill costs 42,750. It saves 182,250, about 81%.

But the break-even in that same session is 22,743 tokens. So in the very session where rollup pays out best in absolute terms, the rule is also at its most restrictive: anything under ~23k tokens should still be read whole. Both halves of the intuition were right, and they apply to different notes in the same breath.

## the rule of thumb, for when you do not want to run the numbers

Roll up when all of these hold:

- the note is bigger than 2.5% of your current context
- the note is bigger than ~800 tokens in absolute terms
- it has at least two headings, and they read as claims rather than labels
- you are handling several notes at once, or the note is very large

Read whole otherwise. Notably: a huge note with no headings gets read whole, because there is nothing to route on — the outline is empty and the round trip buys nothing. One 36k-token heading-less note in this corpus is exactly that case.

## the code

[[note_outline.py]] prices both paths and serves either. It parses markdown directly with no index, daemon or network, so it cannot go stale.

```
note_outline.py NOTE.md --context 120000     # verdict + outline with line ranges
note_outline.py NOTE.md --section-n 4        # just that section
note_outline.py NOTE.md --context 120000 --decide   # one word, for scripts
```

[[outline_gate.py]] is the PreToolUse hook that applies it automatically. It reads the true prefix size out of the transcript's last usage block rather than guessing, and when the verdict is OUTLINE it denies the Read and hands back the outline plus the command to fetch any section.

It fails open on every error path, passes through anything with an explicit offset or limit, ignores non-markdown and heading-less files, stays silent below a 20k prefix, and turns off with `PKM_OUTLINE_GATE=0`. A cost optimisation must never be able to block a file read, so every uncertain case resolves to "just read it".
