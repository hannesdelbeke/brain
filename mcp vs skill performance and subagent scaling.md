mcp vs skill performance and subagent scaling

## the cold boot problem
a **skill** is typically a terminal command or python script (e.g. `python search.py`). every time an agent uses it, it incurs a "cold boot" penalty: spinning up the python interpreter, loading databases, and pulling ml embedding models into ram. this can take 3-10 seconds per run.

an **mcp server** runs continuously in the background. the database and models stay "hot" in memory, dropping execution time to <50ms.

see [[autonomous agent tool use and memory]] for how this speed difference completely flips the value of "always search" rules.

## sharing mcp resources across subagents
subagents absolutely share the time savings of an mcp server. in fact, mcp architecture becomes critical when scaling up to multi-agent swarms.

if you spawn 10 subagents to research different parts of a codebase and they all use a **skill** (cli script) simultaneously:
- your computer has to cold-boot 10 separate python environments.
- it tries to load 10 separate copies of the embedding models into ram.
- this causes massive cpu spikes, hits memory limits (oom crashes), and slows down the entire system.

if those 10 subagents query an **mcp server** instead:
- there is only one "hot" server running in the background.
- all 10 subagents send fast, lightweight requests to the exact same server over a local socket.
- ram usage stays flat (only 1 model is loaded), and all queries return in milliseconds.

congratulations, your mcp just acted as a centralized, high-performance microservice for your entire ai swarm.
