---
name: style-audit
description: Measure verbal tics in past claude code output by building an n-gram database from the local transcripts
created: 2026-08-27
---

[[tics.py]] walks `~/.claude/projects/**/*.jsonl`, keeps only assistant `text` blocks, strips code and urls and paths, and writes an sqlite database of one to five word n-grams with both a total count and a sentence-opening count.

```
python tics.py --out tics.db                 # whole corpus, a few minutes
python tics.py --since 2026-08-01 --out aug.db
python tics.py --limit 20 --out smoke.db     # smoke test
```

The `opens` column is the one that matters. Tics live at the start of a sentence, so a phrase with a high `opens` relative to its total count is a reflex rather than vocabulary.

```sql
SELECT text, count, opens FROM ngram WHERE n=3 ORDER BY opens DESC LIMIT 30;
SELECT text, opens FROM ngram WHERE n=2 AND text LIKE 'let %' ORDER BY opens DESC;
```

Two parse details are load-bearing. Claude Code writes one jsonl line per content block and repeats the same `message.id` on each, so deduping on `message.id` alone silently drops every block after the first and undercounts prose by about 5x; dedupe on the pair of id and block text. And `thinking` blocks are excluded on purpose, since the target is the voice the reader sees, not the internal one.

The database is regenerable and is not committed. Rerun with a `--since` window and compare `per_million` against a full-corpus run to see whether a tic is fading.

Cost measurement for the same transcripts is a separate skill, `token-audit`.
