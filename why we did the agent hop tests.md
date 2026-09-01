
## research inspiration
I read research that word positions in a sentence, affects how easy a human can understand it.
[[2026-08-30 readability and reading-speed research applied to note-taking vaults]]

## goal
word position and formatting can improve human read speed
So can we format text in an optimal way for AI? 
So AI can read text quicker & cheaper, do faster research, query notes more, leading to better results.
- [[Increase agent note retrieval speed]]

This [[2026-08-30 agent reading versus human reading, which formatting rules transfer]]
Claimed that lost in the middle transfers to agent
## formatting & position test on - no agent gains

tested word-position/formatting rules directly on an ai reader (bold text, list-chunking, lost-in-the-middle) — kept coming back null, no effect, at every scale tried, in [[2026-09-01 publish plan - readability and compression research as papers]].

the null turned out to be caused by the planted key: a unique serial number let the model find the answer by exact-match lookup instead of real position-sensitive search — see [[2026-09-01 why the u-curve disappeared in candidate 2's multi-document test]].

## test if full context makes a model dumber

heard an influencer claim that a model gets dumber the longer/fuller its context gets, more anchored to what's in front of it, less able to think broadly.

first wondered if a full, stuffed context makes a model dumber. tested single-shot, everything in one prompt, no dip at any position. so fullness alone isn't it.
- [[2026-09-01 pilot design - bringing the u-curve back with real notes and paraphrased questions]]

why it came back null: single-shot means the model can see every document at once, in one pass, regardless of where the target sits. there's no forced sequence of decisions to lose track across — it's not reading document 1, then forgetting it while reading document 2. a bigger context window just means it can hold the whole stack at once, so position stops being a real constraint at this scale. 
(this is an AI conclusion, unsure if i agree or understand it. however I am not exploring this bit deeper since it failed.)

## explore turn count rot instead of context rot

### ran various note hop tests

then wondered if it's turn count instead of token count.

tested on my vault notes, one note per turn, no memory between turns. found trouble at the middle hop, roughly 1 in 6.
- [[2026-09-01 hop-ceiling pilot - a u-curve shadow the token-ceiling test never found]]

did more repeats to pin the rate down, and tried a longer 13-hop chain to see if it's a coincidence. trouble moved to hop 1 instead of staying in the middle. so it's not a fixed unsafe seat, it moves with the chain.

old research showed a u curve on complex searches for agents.
- [Lost in the Middle: How Language Models Use Long Contexts](https://cs.stanford.edu/~nfliu/papers/lost-in-the-middle.arxiv2023.pdf) (Liu et al. 2023, arXiv:2307.03172) — the original paper the U-curve claim comes from
- [[2026-09-01 designing a true multi-document lost-in-the-middle test for candidate 2]] — this vault's own summary of what Liu et al. actually tested

since the research was done on old agents, which can hold fewer tokens in context, maybe newer agents can now hold all the complex docs in one pass. thought maybe we can emulate complexity with turns: pretend a note is so complex it can't be held in memory, therefore you forget all previous notes.

so setup a test with wikipedia data.
[[2026-09-01 wikipedia hop-ceiling test - setup and reproduction steps]]

despit closed book question at start to filter out prior knowledge, I then thought maybe the model is biased, since it had access to wikipedia during training. so made 2 synthetic vaults to test, without the same flaw as the first synthetic vault.

[[2026-09-01 synthetic hop-ceiling test - two fictional vaults, cross-model content, zero trouble found]]

### conclusion no findings
end result, this seems like a dead end. no findings.
IMO this hop testing was a side track with no clear goal or aim.
writing this overview puts things back in perspective.

---
## Conclusion

use [[map-reduce]] instead, specifically [[hierarchical map-reduce note rollup]], so the agent reads a summary/header first and only opens the full note if it needs to

- token thrift and token compression notes:
	- [[2026-08-31 research on compressing llm reasoning and notes without losing information]], 
	- [[2026-08-31 classifier-based compression with an adversarial fidelity gate]]