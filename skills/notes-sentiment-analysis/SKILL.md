---
name: notes-sentiment-analysis
description: Automated analysis of vault notes using Gemini/Groq LLM to extract sentiment, energy, and tags into YAML frontmatter.
aliases:
  - notes sentiment analysis
  - notes-sentiment-analysis
origin-sha: 424f673f
created: 2026-08-24
tags:
  - technical
  - pkm
  - skill
---

Automated analysis of vault notes using Gemini Flash / Groq API.  
Extracts sentiment, energy, and tags — stored as YAML frontmatter.

## What it does
- Reads Markdown notes across the vault
- Sends note content in parallel batches to Gemini Flash or Groq (Llama 3.3 70B)
- Writes extracted mood and taxonomy metadata to YAML frontmatter
- Skips unchanged notes via body content MD5 hashing
- Auto-detects factual/technical documents to avoid noisy tagging
- Merges new tags with existing frontmatter without dropping user tags

## How to run
```bash
python public/skills/notes-sentiment-analysis/analyze_sentiment.py
```

### Options
- `--workers 5` — number of parallel worker threads (default: 5)
- `--batch-size 20` — notes per API request (default: 20)
- `--model gemini-3.6-flash` or `llama-3.3-70b-versatile` — specify target model
- `--dry-run` — preview without writing anything
- `--sample 10` — process N random notes (for testing)
- `--force` — re-analyze all notes, ignoring content hash
- `--folder projects/` — process a specific folder or single file

### Setup & Providers

#### 1. Groq API (Recommended Free Provider)
- **Setup:** Get a free API key at [console.groq.com](https://console.groq.com/).
- **Model:** `llama-3.3-70b-versatile` (automatically selected when `GROQ_API` / `GROQ_API_KEY` is detected).
- **Run:**
  ```powershell
  $env:GROQ_API="your-groq-api-key"
  python public/skills/notes-sentiment-analysis/analyze_sentiment.py --workers 3 --batch-size 10
  ```

#### 2. Gemini API (Pay-As-You-Go / Free Tier)
- **Setup:** Get API key in [Google AI Studio](https://aistudio.google.com/apikey).
- **Model:** `gemini-3.6-flash` or `gemini-2.5-flash`.
- **Run:**
  ```powershell
  $env:GEMINI_API_KEY="your-gemini-api-key"
  python public/skills/notes-sentiment-analysis/analyze_sentiment.py --workers 5 --batch-size 20
  ```

---

## Fields

All fields added/updated by the script:

| Field | Type | Example | Purpose |
| :--- | :--- | :--- | :--- |
| `sentiment` | list of ints | `[3]` or `[4, 7]` | Mood scores (1-10 scale). First = dominant mood. |
| `sentiment-label` | list of strings | `[lonely]` or `[frustrated, content]` | Concise mood descriptors matching each sentiment score. |
| `energy` | int or null | `3` | Activation level: 1 (drained/numb) to 10 (wired/restless). Null for purely factual notes. |
| `tags` | list | `[journal, relationship, social]` | Taxonomy categories merged with existing frontmatter. |
| `sentiment-hash` | string | `8f3a2b1c` | Truncated MD5 hash of note body for incremental cache skipping. |

### Tag Taxonomy

| Category | Tags |
| :--- | :--- |
| **Note type** | `journal`, `medical`, `technical`, `planning`, `memory`, `social`, `creative`, `financial` |
| **Topic** | `relationship`, `loneliness`, `procrastination`, `outdoors`, `communication`, `self-reflection` |
| **Life area** | `work`, `health`, `hobby`, `finance`, `home`, `travel` |

---

## Frontmatter Examples

> [!EXAMPLE]- Journal entry — clear negative sentiment
> **Before:**
> ```markdown
> Last week I was feeling stuck and a bit down with project progress.
> ```
> **After:**
> ```yaml
> ---
> sentiment:
>   - 3
> sentiment-label:
>   - discouraged
> energy: 3
> tags:
>   - journal
>   - procrastination
>   - self-reflection
> sentiment-hash: 8f3a2b1c
> ---
> Last week I was feeling stuck and a bit down with project progress.
> ```

> [!EXAMPLE]- Mixed mood — challenging hike with rewarding finish
> **Before:**
> ```markdown
> Heavy rain and wind on the ascent, but the summit view was stunning.
> ```
> **After:**
> ```yaml
> ---
> sentiment:
>   - 4
>   - 8
> sentiment-label:
>   - exhausted
>   - content
> energy: 7
> tags:
>   - journal
>   - outdoors
>   - hobby
> sentiment-hash: c4d5e6f7
> ---
> Heavy rain and wind on the ascent, but the summit view was stunning.
> ```

> [!EXAMPLE]- Technical / Medical report — auto-detected as factual
> **Before:**
> ```markdown
> | Parameter | Result | Reference |
> | :--- | :--- | :--- |
> | Resting HR | 58 bpm | 50–70 |
> ```
> **After:**
> ```yaml
> ---
> sentiment:
>   - 5
> sentiment-label:
>   - factual
> tags:
>   - medical
>   - health
> sentiment-hash: e5f6a7b8
> ---
> | Parameter | Result | Reference |
> | :--- | :--- | :--- |
> | Resting HR | 58 bpm | 50–70 |
> ```

---

## Energy Tracking

`energy` captures physical/cognitive **activation level**, distinct from emotional valence:

| Valence / Energy | Low Energy (1–3) | High Energy (8–10) |
| :--- | :--- | :--- |
| **Negative** | Drained, numb, defeated | Anxious, agitated, restless |
| **Neutral** | Zoned out, sleepy | Busy, rushed |
| **Positive** | Calm, peaceful, relaxed | Excited, wired, hyperfocused |

---

## Design Decisions
- **Frontmatter Storage:** Dataview and Obsidian query frontmatter natively; avoiding central JSON index files prevents multi-device sync collisions.
- **Content Hashing:** MD5 hashes allow re-running across 10,000+ notes in seconds without making redundant LLM API calls.
- **Factual Auto-Detection:** Automatically prevents sentiment pollution on pure API docs, recipes, logs, and tables.
