---
date: 2026-08-31
created: 2026-08-31
tags:
  - pkm
  - sentiment
  - spaced-repetition
  - idea
---

> [!summary] eli5
> two notes saying "upset at John" a day apart are one event, not two data points, the second one is just the first one still going. two notes saying it a year apart are independent confirmations that the pattern is real. this note proposes weighting sentiment mentions by the gap since the last mention of the same entity, so a trait that survives spacing counts more than one that is just recent venting.
> nothing is built. this is the idea as written, unweighted by any test against real notes yet.
> **needs from you:** say whether this is worth building into [[notes-sentiment-analysis]], recommend yes, the mechanism is cheap, a per-entity last-seen timestamp and a log-scaled weight, and the vault already has the timestamps.

> notes written in short span off each other are biased. e.g. if i write i was upset at john today. i m likely to still be upset at john tomorrow. but if i write i am upset at john a year later. the pattern is stronger. kinda reminds me of spaced repetition learning. can we extrapolate this to notes

**why:** root

## the spaced repetition parallel

spaced repetition scheduling works because a fact recalled after a long gap without help proves the memory is durable, where a fact recalled a minute after it was shown proves nothing beyond short-term retention. the same split applies to a recorded feeling: a sentiment repeated after a long gap is evidence of a durable trait, where a sentiment repeated an hour later is the same feeling, counted twice.

put another way, two mentions close together are correlated samples of one underlying event. two mentions far apart are closer to independent samples of the same underlying disposition. the far-apart pair carries more information per mention, exactly the way spaced practice carries more information per repetition than massed practice does.

## what it would change

today, a plain count of "upset at John" mentions treats every mention as one vote, so a single bad week outweighs a mild but longstanding pattern spread over months.

the fix has two parts.

first, cluster mentions of the same entity that fall inside a short window, a day or so, into one event, since they are one incident being written about more than once.

second, weight the remaining, one-per-cluster mentions by the gap since the last one, on a log scale so the difference between one day and one week matters more than the difference between one year and thirteen months.

a pattern that only shows up as a burst of close mentions stays flagged as an incident. a pattern that keeps reappearing across widening gaps gets flagged as a trait.

## the risk

a real, worsening conflict is also close-spaced, someone can genuinely be angry at the same person every day for a month. gap-weighting alone would underrate that case relative to a milder pattern that happens to recur once a year.

the mitigation is not to drop the close-together signal, it is to keep both: cluster density says how hot right now, gap-weighted recurrence says how enduring. the two numbers answer different questions and neither should be collapsed into the other.

## what building it costs

[[notes-sentiment-analysis]] already extracts sentiment and tags per note with timestamps. the addition is per-entity: last-seen timestamp, a clustering pass on mentions inside a short window, and a log-scaled weight on the gap to the previous cluster. no new data collection, the vault already has every timestamp this needs.
