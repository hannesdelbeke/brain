---
aliases:
- HAOS setup mcp
- home assistant mcp
tags:
- technical
---

the [Model Context Protocol Server](https://www.home-assistant.io/integrations/mcp_server/) integration exposes [[Home Assistant]]'s Assist api as [[MCP server|MCP]] tools, so an [[AI agent]] can read state and control devices in the house. it is a core integration, nothing to install from the add-on store.

**the two integrations point in opposite directions** and are easy to mix up, because the names differ by one word:

- **`mcp_server`** makes home assistant the server, so claude or another agent drives the house. this note.
- **[`mcp`](https://www.home-assistant.io/integrations/mcp/)** makes home assistant the client, so home assistant's own conversation agent can call out to external tools like web search or memory. different integration, different setup.

## expose the entities first

the integration serves the Assist api, which means it can only see entities that are [exposed to voice assistants](https://my.home-assistant.io/redirect/voice_assistants). an agent that connects successfully and then reports an empty house has almost always hit this rather than an auth problem, so check it before debugging anything else.

## add the integration

**Settings > Devices & services > Add Integration > Model Context Protocol Server**, then choose the *Control Home Assistant* option if the agent should be able to act rather than only read.

## the endpoint

the current endpoint is **`/api/mcp`**, speaking streamable http, stateless. a specific llm api can be addressed directly as `/api/mcp/<api_id>`, so the built-in Assist api is `/api/mcp/assist`. **non-admin users are limited to `/api/mcp/assist`** regardless of what they request.

older write-ups point at an sse endpoint at `/mcp_server/sse`. that is the shape the integration shipped with and not what the current docs give, so a guide using it is a sign the rest of it is stale too.

**the external url has to match** what is configured under Settings > System > Network, or the handshake fails in a way that does not obviously name the url as the cause.

## authentication

**OAuth is the recommended path.** the client id is the *client application's* base url — `https://claude.ai`, `https://chatgpt.com` — and home assistant implements IndieAuth rather than RFC 7591 dynamic client registration, so there is no registration step. the client secret is unused; enter any text where one is required. **never put your own home assistant url in the client id field.**

**a long-lived access token** is the alternative, made under User profile > Security > Long-lived access tokens, and sent as `Authorization: Bearer <token>`. worth knowing that the supervisor rest proxy at `/api/hassio/*` refuses these same tokens even for an owner account, so a 401 there is not evidence that the token is bad.

## connecting claude code

```bash
claude mcp add-json "HA" '{
  "type": "http",
  "url": "https://<your_home_assistant_url>/api/mcp",
  "oauth": {
    "clientId": "http://localhost:12345",
    "callbackPort": 12345
  }
}' --client-secret
```

that is close to the one command wanted in [[HA AI connection goal]] — it still needs the integration added and the entities exposed first, but the client half is a single line and is per-project or `--scope user` for all of them.

## connecting a stdio-only client

a client that speaks only stdio needs [`mcp-proxy`](https://github.com/sparfenyuk/mcp-proxy) in front, which is the documented path for local network access without a public url:

```json
{
  "mcpServers": {
    "Home Assistant": {
      "command": "mcp-proxy",
      "args": [
        "--transport=streamablehttp",
        "--stateless",
        "http://<local_ip>:8123/api/mcp"
      ],
      "env": { "API_ACCESS_TOKEN": "<your_access_token_here>" }
    }
  }
}
```

use the **ipv4 literal rather than `homeassistant.local`** here, for the mdns reason in [[HAOS setup ssh]]: the hostname can resolve to a link-local ipv6 address that the published port is not listening on, and the connection is reset rather than refused.

for remote access, [Home Assistant Cloud](https://www.nabucasa.com/) at `https://<your-id>.ui.nabu.casa` is the recommended way to get a url that works from outside without exposing the box.

## what it exposes

**tools** are the actions of the configured llm api, **prompts** are the usage instructions that come with them, and there is one **resource**, `homeassistant://assist/context-snapshot`, a read-only state snapshot available when the `GetLiveContext` tool is.
