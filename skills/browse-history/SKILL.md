---
name: browse-history
description: Query local ActivityWatch browser and search history across all aw-watcher-web-* buckets using the aw-history CLI.
---

## when to use

Use `aw-history` on demand when you need to recall what the user recently searched for, read, or visited in a browser (Chrome, Firefox, or synced mobile browsers) without asking the user to repeat links or queries.

Common triggers:
- Finding a doc, repo, or article the user looked at recently
- Checking recent web searches (`--searches`) to understand active context or research threads
- Scoping lookups to a specific site (`--domain`) or time window (`--today`, `--days N`, `--from`/`--to`)

## cli usage

`aw-history` is installed at `~/.local/bin/aw-history` (symlinked to `aw_history.py`, stdlib Python 3 only) and queries the local ActivityWatch REST API at `http://127.0.0.1:5600/api/0/`.

```sh
# Recent Google/DuckDuckGo/Bing searches (extracted q= parameter)
aw-history --searches --days 7 --limit 15

# Keyword match against URL, title, and extracted search query
aw-history "activitywatch" --days 14

# Filter by domain or today's activity
aw-history --domain github.com --today

# Date range and JSON output for downstream parsing
aw-history --from 2026-11-20 --to 2026-11-25 --json --limit 20

# Top visited domains over the last 7 days
aw-history --top-domains --days 7 --limit 15

# Per-day timeline clusters ("when did I research X?")
aw-history "activitywatch" --timeline --days 30
```

## behavior notes

- Queries every `aw-watcher-web-*` bucket exposed by `/api/0/buckets/`, so desktop browsers and future synced buckets are included automatically.
- Deduplicates rapid/consecutive `(url, title)` heartbeats within a 60-second window so output stays compact.
- Redacts common sensitive query parameters (`token`, `access_token`, `code`, `api_key`, `secret`, etc.) from URLs before printing.
- Override the API endpoint with `--base-url` or `AW_BASE_URL` if ActivityWatch runs on a non-default host or port.
