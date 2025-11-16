Today I tested out Gemini 2.0 Flash in [[Obsidian]], with the [[obsidian-copilot|Copilot plugin]]


> [!warning] 
> Don't confuse this plugin [[obsidian-copilot]] with [[obsidian-github-copilot]]

- generated a API key in Google AI studios
- installed the Obsidian Copilot plugin
- tweak Copilot settings
	- setup API key
	- selected Gemini 2.0 Flash as the model (claims API is not setup)
	- rebuild index vectors with Gemini
- restart Obsidian, model now accepts the API key)
- tried a few queries, works well, it's like Agent mode in [[visual studio code]]

i can see my usage [here](https://aistudio.google.com/usage?project=gen-lang-client-0088023314) 
The limit is 15 free requests a day
## test vault QA mode
Vault QA mode seems poor. It auto attaches related notes, but they are not relevant.

> when was my last work weekly meeting?

> I am sorry, but I cannot answer your question with the information I have. The provided notes do not contain information about your work weekly meetings.
> **Sources:** (it links 3 random work notes)
## vectorize notes
this is supposed to be a support feature, so it can send related notes to the AI.
however I actually like this feature on it's own.
In the chat window, it lists related notes, which are either linked or semantically similar.
Semantically similar notes could be a great tool to [[discovery|discover]] new note connections.

[[large language model|LLM]]
[[retrieval augmented generation|RAG]]