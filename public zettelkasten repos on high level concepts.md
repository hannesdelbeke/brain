> 	find public zettelkast notes on github, active, discussing high level concepts. most usually are low level technical code things. aim for ones that discuss higher level like improving as human, or productivity, or explore creative concepts like using semantic search or vector embedding on a note vault. are there any older ones, that might even be dead repos, that we can learn similar or even more from, e.g. a genius that passed away.

searched github by topic (`zettelkasten`, `digital-garden`, `second-brain`, `obsidian-vault`) and by code search inside note folders for conceptual filenames. the topic searches are dominated by tools rather than note collections, so the code search over `content/thoughts/` and `notes/` paths is what surfaced the actual vaults.

sorted by what the notes are about rather than by whether anyone still writes them. staleness is not a disqualifier for a note collection, it is a disqualifier for a tool: a frozen vault still reads fine, a frozen plugin stops loading. the dead ones are better than the live ones on average, because the live ones are competing for stars and the dead ones were written for the author.

indexed from [[2026-08-20 domain masters hub]], which covers authoritative seeds across domains.

> [!info] Reference
> 🟢 pushed this quarter, 🟡 quiet for months, 🔴 finished, abandoned or the author is gone. ⭐ is stars as of 2026-08-20.

## Becoming a Better Human

🔴 [busterbenson/public](https://github.com/busterbenson/public) ⭐871. the single best one. `book-of-beliefs.md` is a [codex vitae](https://busterbenson.com/piles/codex-vitae/), a versioned statement of everything he believes with confidence levels attached, rewritten each year, with git history as the record of how a person's mind changed. the repo also holds `cognitive-bias-cheat-sheet.json`, the source data behind the [cognitive bias codex](https://en.wikipedia.org/wiki/List_of_cognitive_biases). the idea spawned dozens of forks that are all abandoned after one or two commits ([dehowell](https://github.com/dehowell/codex-vitae), [ryanramage](https://github.com/ryanramage/codex-vitae) "a living and dying record of my beliefs", [rd825](https://github.com/rd825/codexvitae)), which is itself the finding: the format is easy to start and hard to keep, so the interesting question is what makes a belief worth restating a year later.

🔴 [joshleitzel/rawthought](https://github.com/joshleitzel/rawthought) ⭐248. aaron swartz died in 2013 and his writing is the closest match to improving as a human in this whole search. this is his blog converted to markdown, pdf and epub, and [jdjkelly/www.aaronsw.com](https://github.com/jdjkelly/www.aaronsw.com) is an archival copy of the site. the [raw nerve](http://www.aaronsw.com/weblog/rawnerve) series inside it is the part to read: lean into the pain, believe you can change, look at yourself objectively.

🔴 [mgp/book-notes](https://github.com/mgp/book-notes) ⭐4108. one long file per book, on never split the difference, being mortal, how to read a book, multipliers, managing humans, the knack, writing tools, choose yourself. negotiation, mortality, management and reading, and the files are detailed enough to be useful without having read the book.

🟢 [brennanbrown/enjoyment-work](https://github.com/brennanbrown/enjoyment-work) ⭐113. jekyll site split into `_notes`, `_journals` and `_posts`, so you can watch a raw journal entry turn into a permanent note. subjects are getting unstuck, humility and false pretension, and information hazards in what you choose to consume.

## Thinking About Thinking

🟢 [jackyzha0/jackyzha0.github.io](https://github.com/jackyzha0/jackyzha0.github.io) ⭐189. the closest match to the ask, and the [quartz](https://github.com/jackyzha0/quartz) author's own garden. note titles include chesterton's fence, hedonic treadmill, epistemic injustice, intentional arrangement, communities, play, craft, meditation, seeing like a state, the purpose of a system is what it does. his rhizome research log opens by saying research logs focus too much on what one did rather than what one felt, and sets out to mix both.

🟢 [MaggieAppleton/maggieappleton.com-V3](https://github.com/MaggieAppleton/maggieappleton.com-V3) ⭐163. split into notes, essays and patterns. digital gardening theory, metaphors as a thinking tool, anthropology of software, and what language models do to writing. an illustrator rather than an engineer, so the notes argue in pictures.

🟢 [jrgilbertson/networked-thinking](https://github.com/jrgilbertson/networked-thinking) ⭐148. the most disciplined zettelkasten here. atomic notes carry luhmann-style timestamp ids and state one claim in the filename: the stoic dichotomy of control divides reality into things we can control and things we cannot, the ebbinghaus forgetting curve is a model showing how memory retention declines exponentially. ships daily, weekly and quarterly review templates plus a decision template, and reference notes on [how to take smart notes](https://takesmartnotes.com).

🔴 [mnielsen/notes](https://github.com/mnielsen/notes) ⭐9. "rough working notes on a variety of subjects" by michael nielsen, who went on to co-write [how can we develop transformative tools for thought](https://numinous.productions/ttft/) with andy matuschak. the value is watching a careful thinker work in an untidy state, given the polished essay it eventually fed.

🟡 [bramses/bramses-highly-opinionated-vault-2023](https://github.com/bramses/bramses-highly-opinionated-vault-2023) ⭐1197. the year in the repo name is the point, it was published as a snapshot of one person's method rather than a thing to maintain. the readme argues why each rule exists rather than listing plugins, so it reads as an essay on capture and review.

🟡 [martijnaslander/luhmann-zettelkasten](https://github.com/martijnaslander/luhmann-zettelkasten) ⭐3. the original, all 73,715 cards of [niklas luhmann's](https://en.wikipedia.org/wiki/Niklas_Luhmann) physical slip box mapped as a network from the [digitised archive](https://niklas-luhmann-archiv.de). useful for seeing how sparse the real link graph is compared to what people claim to build. andy matuschak's [evergreen notes](https://notes.andymatuschak.org) have no official repo, only unofficial mirrors like 🟡 [XQZmeSIR/AndyNotes](https://github.com/XQZmeSIR/AndyNotes).

## One Life, Catalogued

the vibe here is not ideas but inventory. a person deciding their own taste is worth version control.

🟡 [kepano/kepano-obsidian](https://github.com/kepano/kepano-obsidian) ⭐4388. steph ango's own vault, and mostly a catalogue of things rather than thoughts: restaurants, recipes, apps, films, genres, real estate, each with its own template. daily notes and references like a kevin kelly interview and a brown butter nectarine tart. the method underneath is bottom-up organising and [file over app](https://stephango.com/file-over-app), which is the part that does not decay.

🟢 [joshbeckman/notes](https://github.com/joshbeckman/notes) ⭐3. a personal site-as-a-tool that logs almost everything: reading highlights, running, cycling and weight training sessions, letterboxd reviews, albums, hiking videos generated from gps data, plus a `canon.md` of the things he keeps returning to. the interesting bit is how far one person will push a jekyll site as a life database.

🔴 [rknightuk/intersect](https://github.com/rknightuk/intersect) ⭐44. "everything i know, mostly", organised as a practical reference wiki rather than a thinking space: fonts, food, hotels and airbnbs, gaming, browsers, the indieweb, and macos setup, alongside php and regex pages. the format is the lesson, opinions written down once so they stop being re-litigated.

🔴 [RichardLitt/knowledge](https://github.com/RichardLitt/knowledge) ⭐265. the least programmer-shaped vault in this list despite the author being a maintainer by trade. birds and bird quotes, an overnight birding checklist, plants, a cafe list, songs, game theory, and a fitness glossary sat next to github processes.

## Art, Politics and the Weird Internet

🟢 [XXIIVV/oscean](https://github.com/XXIIVV/oscean) ⭐559. devine lu linvega's lifelong wiki, written from a sailboat: art, philosophy, longtermism, conlangs, off-grid living and [permacomputing](https://permacomputing.net). the content sits in a custom uxntal format so the [rendered site](https://wiki.xxiivv.com) reads better than the repo. the strongest example of a knowledge base that is also an aesthetic.

🟢 [flancian/garden](https://github.com/flancian/garden) ⭐28. [the agora](https://anagora.org), daily notes running since 2020 plus concept notes like chasing moloch and bluesky and enshittification. the project is about federating personal knowledge graphs between people, so a note you write and a note someone else writes on the same term end up on one page.

🟡 [mislav/poignant-guide](https://github.com/mislav/poignant-guide) ⭐813. [_why the lucky stiff](https://en.wikipedia.org/wiki/Why_the_lucky_stiff) did not die, he deleted himself in 2009, and the community mirrors are all that is left. still being touched seventeen years later. a programming book written as absurdist fiction with cartoon foxes, and the strongest argument in this list that the format of a knowledge base is a creative choice rather than a technical one.

🔴 [joearms/joearms.github.io](https://github.com/joearms/joearms.github.io) ⭐67, and [joearms/old.blog](https://github.com/joearms/old.blog) ⭐72. joe armstrong died in 2019. erlang is the surface topic, but the posts underneath are about why software gets complicated, how to write so people understand you, and what it takes to stay on one idea for thirty years.

## Machines Reading Your Vault

tools rather than note collections, but they are the ones arguing the concept.

🟢 [matzalazar/rhizome](https://github.com/matzalazar/rhizome) ⭐71. embeds notes with a multilingual sentence transformer and writes a `## Related Notes` wikilink section back into the note itself, so the output is plain markdown rather than a search box. no cloud api, no database.

🟢 [sturlese/hippocampus](https://github.com/sturlese/hippocampus) ⭐24. the opposite position, stated as a design goal: no embeddings, no vector database, no mcp, no obsidian plugins, just markdown, one stdlib python script and a link graph. read alongside rhizome as the two ends of the argument.

🟢 [Zettelgarden/Zettelgarden](https://github.com/Zettelgarden/Zettelgarden) ⭐168. a zettelkasten where agents handle capture, processing and recall, so the vault is maintained by something other than the person who owns it.

## Technical Vaults with a High Level Half

🟢 [lyz-code/blue-book](https://github.com/lyz-code/blue-book) ⭐969. huge and mostly tooling, but `life_management.md`, `systems_thinking.md`, `knowledge_management.md`, `gardening.md` and the activism and feminism notes carry a serious non-technical side. one of the few where the author writes about politics and self-hosting in the same voice.

🟢 [aarnphm/aarnphm.github.io](https://github.com/aarnphm/aarnphm.github.io) ⭐22. half machine learning internals, half philosophy: wittgenstein, kant, nietzsche, freud, rationality, retrieval practice, value, negation, sitting next to attention kernels and quantisation. worth it for how casually the two halves link to each other.

🔴 [jethrokuan/braindump](https://github.com/jethrokuan/braindump) ⭐394. one of the first large public zettelkastens and the reason a lot of people tried org-roam. the bulk is machine learning, robotics and statistics reference notes, with a thin conceptual layer over it: occam's razor, progressive summarisation, storytelling. read it for the org-roam workflow rather than the ideas.

🔴 [past-nikiv/knowledge](https://github.com/past-nikiv/knowledge) ⭐38. the archived version of nikita voloboev's "everything i know", now continued at [wiki.nikiv.dev](https://wiki.nikiv.dev). mostly programming languages, unix and macos, but `looking-back/` holds monthly retrospectives going back to 2019 and `life/` holds memories, which is the part worth stealing.

🔴 [cedrickchee/knowledge](https://github.com/cedrickchee/knowledge) ⭐128. archived in 2023 and almost entirely fast.ai and coursera course notes, with `books/deep-work.md` as the lone exception. listed as the failure case: the "document everything" ambition collapsing into one course you took.

🟢 [lextoumbourou/notes](https://github.com/lextoumbourou/notes) ⭐63. advertises the zettelkasten method and pushes regularly, but the permanent notes are gram-schmidt, relu and nyquist-shannon. a clean example of the low level bucket this search was trying to get out of.

## Lists to Keep Digging Through

🟢 [lyz-code/best-of-digital-gardens](https://github.com/lyz-code/best-of-digital-gardens) ⭐590. a ranked list of 100 gardens with topic tags, so you can filter for productivity, health or philosophy over programming. it scores by github activity though, which sorts tools above vaults and ranks a maintained plugin over a finished body of thought.

🟢 [KasperZutterman/Second-Brain](https://github.com/KasperZutterman/Second-Brain) ⭐1831 and 🟢 [obsidian-pkm-vault/awesome-obsidian-vault](https://github.com/obsidian-pkm-vault/awesome-obsidian-vault) ⭐502. the two larger awesome lists, both mixing tools in with the vaults.
