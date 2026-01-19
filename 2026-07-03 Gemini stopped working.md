---
views: 2
---
[[Gemini CLI]] stopped working. Just noticed, as I've not used it for weeks

```
Failed to sign in. Message: This client is no longer supported for Gemini Code Assist for individuals. To continue │
│   using Gemini, please migrate to the Antigravity suite of products: https://antigravity.google
```

Google **shut it off for all individual‑tier users on June 18, 2026**.
Only Enterprise / Standard customers still have access

windows install new `agy` binary for antigravity. faster, async, multi-agent
```powershell
iwr https://antigravity.google/cli/install.ps1 -UseBasicParsing | iex
```

it works but i ran out of credit. it wasn't able to convert my .hyp files to .edf
[[OpenAI Codex]] managed to do it