> [!tip] already handled by default
> tool search ships on by default in [[claude code]] 2.1.7 and defers mcp schemas automatically, so for most people the main fix is already live with no action. the rest of this note is the residual levers on top of that.

> mcp uses a lot of tokens, research options to save tokens with tool search and env vars, whether it can be automated for a non-technical user, and whether converting mcp to skills would save more

connecting a handful of mcp servers quietly burns a third to a half of the context window before anyone types a word, because every server's tool schemas load into the system prompt on session start and get paid for on every message. this note is the reusable version of how to cut that, what is already automatic, and where converting to [skills](https://docs.claude.com/en/docs/agents-and-tools/agent-skills/overview) actually helps.

the scope here is the per session context budget inside claude code. aggregate api spend across a team or an organisation is a different measurement with different levers, and nothing below moves it directly.

## two separate budgets

the cost splits in two and each has its own fix, so it helps to name them separately. tool definitions are the schemas for every connected tool, loaded once and cached in the system prefix, charged every turn. tool output is what a single call returns, a different dial entirely. a six server setup like clickup, google workspace, home assistant, notion, playwright and slack is 300 plus tools, roughly 60 to 120k tokens of definitions idle.

## tool search is the main fix and it is automatic

[tool search](https://platform.claude.com/docs/en/agents-and-tools/tool-use/tool-search-tool) defers the schemas: claude sees only a search tool plus your few non deferred tools, then pulls a full schema on demand when a task needs it. anthropic measured 77k down to 8.7k, an 85 percent cut, and accuracy went up not down because the model is not wading through hundreds of irrelevant tools. it shipped default on in claude code 2.1.7, so for most people this is already handled with no action.

control is the [`ENABLE_TOOL_SEARCH`](https://code.claude.com/docs/en/env-vars) env var. unset or `auto` defers once definitions pass ten percent of the window, `auto:5` lowers that to five percent, `true` forces it on behind vertex or a proxy, `false` is the old load everything behaviour. a [known bug](https://github.com/anthropics/claude-code/issues/40314) is that http transport servers may not defer and load their schemas upfront anyway, so check `/context` if the mcp line stays fat.

output is the second dial, `MAX_MCP_OUTPUT_TOKENS`, which caps one tool result and defaults to warning at 10k and truncating at 25k. it is distinct from `CLAUDE_CODE_MAX_OUTPUT_TOKENS`, which limits claude's own reply length.

## the lever a person controls is the server list

even deferred, a connected server adds tool names and reasoning surface, and most sessions touch one or two servers. disconnecting an unused server is the bluntest win, but do it at session start because toggling a server mid session wipes the whole prompt cache and costs more than it saves. scope servers per project in a repo `.mcp.json` rather than the global `~/.claude.json`, so a server only loads where it is used. prefer a cli over an mcp server where one exists, `gh` or `gcloud` through bash add zero schema overhead.

## making it just work for a non technical user

the answer for someone who does not know or care what mcp is: do not build an auto disable and re enable system, it fights the built in one. tool search already is the it just works layer, the user types plain english and claude pulls the tool, nothing to disable. dynamic disable and re enable is worse because toggling wipes the cache, claude cannot reliably predict when a server will be needed, and once schemas are deferred an idle server costs almost nothing anyway.

the real hands off deliverable is setting the defaults once, in whoever provisions the machine's hands, then never touched. a global settings.json env block with `"ENABLE_TOOL_SEARCH": "auto"` and `"MAX_MCP_OUTPUT_TOKENS": "25000"` covers every future session. going further, ship servers project scoped so tools appear by location, art tools in the art repo, and the user makes no decisions at all.

## converting mcp to skills

a skill's idle footprint is about 100 tokens, only its name and description, and the body loads on demand, so skills sidestep schema injection entirely. a [scalekit benchmark](https://www.morphllm.com/claude-code-skills-mcp-plugins) found mcp used 32 times more tokens than a cli plus skill on identical github tasks, and converters like [mcp2cli](https://github.com/myeolinmalchi/mcp2cli) and [ts-mcp-to-skill](https://github.com/larkinwc/ts-mcp-to-skill) claim 90 to 96 percent savings.

two things make bulk conversion the wrong move now. tool search already closed most of the gap, deferred mcp sits near the skill baseline for no effort. and a skill cannot replace what mcp does, mcp is the live connection and auth to an external system while a skill is procedure, so converting mcp to a skill really means rewriting the server as a cli the skill shells out to. that only fits stateless input to api to output servers, and it does not cover the oauth or multi tenant servers that matter most, google workspace, slack, clickup, which are exactly what mcp handles best. the rule of thumb: if an integration needs no live external system default to a skill, promote to mcp only when you must reach out. playwright already ships its own cli and skill.md as the model example, so it is the one obvious conversion candidate.

the measured side of the same question, how mcp and skills compare on latency and how it scales across subagents, is in [[mcp vs skill performance and subagent scaling]].

## the short recommendation

leave tool search on, set the two env vars once in a global config, keep the connected server list lean and per project, and convert to skills only for rarely used stateless servers rather than as a blanket policy.
