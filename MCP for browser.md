---
aliases:
  - AI browser access
---

I want [[Artificial intelligence|AI]] to control [[browser]].
The solution is Local Browser Control.

The official Claude Chrome extension can do this, but 
- you need to log in Claude. This is not always possible, e.g. when you don't have the app assigned in Okta, you can't log in (with SSO).
- it only works with Claude. [[vendor lock-in]]

[[AI browser access - zendesk example]]

## Local Browser Control.
- [[Playwright]] MCP (Best for Claude Desktop or [[Cursor - The AI Code Editor|Cursor]])
- browser-use (Best for [[Python]]/Standalone Automation)
	  you can configure browser-use to load your actual [[Chrome]] user profile (including your cookies and active sessions).  
## playwright
Ensure Chrome is fully shut down, don't just close the window

Launch Chrome with Debugging enabled
`"C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222`

---
i tested this.
asked [[Claude Code]] to install playwright mcp
close chrome, and run chrome with  --remote-debugging-port=9222`
restarted claude, it works and claude can access my [[Chrome]]

debug does launch a different [[Chrome|chrome]] profile.



