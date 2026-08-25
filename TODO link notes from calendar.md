---
energy: 5
sentiment:
- 6
sentiment-hash: 3f0d0e66
sentiment-label:
- reflective
tags:
- journal
- planning
- self-reflection
- work
- health
---

14-10-2025
## Google calendar
[[Google calendar]] to visualize what I did on days. It's a great way to see quickly where my time went. Good for reviewing.

- [ ] I want to use links from events to notes, and from notes to events. e.g. see all events where I went to a certain place.

In the past I used rescue time, it would give me percentages that didn't mean much. I might see I wasted a lot of time, but it was trickier to see when I did, e.g. mornings, or in between meetings.
It was designed for software tracking only, it  didn't integrate with real life, e.g. travel, see friends, ...

[[public/link]]
[[use more links in life]]

## Plan

Both directions use features that already exist in Google Calendar and in core Obsidian. This vault has no community plugins installed, `.obsidian/` holds no `plugins` folder, so the plan assumes core only. No new software on day one.

Event to note: paste an [[Obsidian URI]] in the event description.
Format: `obsidian://open?vault=Brain&file=<note title, url encoded>`
Example: `obsidian://open?vault=Brain&file=TODO%20link%20notes%20from%20calendar`
Google Calendar makes URLs in the description clickable in the browser and in the Android app, and Obsidian registers the `obsidian://` scheme on both, so the link opens the note. Use the description, not the location field, because location gets rewritten by maps autocomplete.

Note to events: link to a Google Calendar search.
Format: `https://calendar.google.com/calendar/u/0/r/search?q=<term>`
This answers "all events where I went to a certain place" without copying any event into the vault, and it stays current as new events are added. For a single event or day, use the day and week URLs already collected in [[idea - open google calendar events from notes]].

Steps
1. Pick one place note and one project note. Add a calendar search link to each, using the term that actually appears in the event titles. This is the smallest step and it works today with no setup.
2. Pick five events from the last month that have a note. Paste the `obsidian://open` URI in each description. Check that clicking works on the phone as well as on the pc.
3. Settle on the search term. Events created by [[2025-10 link Strava to Google calendar|IFTTT from Strava]] have predictable titles, manual events do not. Where a term is too vague, add a short tag word to the event title, for example a place name, so the search stays sharp.
4. Automate direction one with the script from [[edit google calendar with Python]]. The OAuth credentials and the [[Windows task scheduler]] run already exist in that repo. Add a pass that lists events in a date range, matches the event title against note filenames, and patches the description with the URI when it is missing. Read plus a single field write, no new service.
5. Only if the live search link turns out to be too slow for the [[monthly review]], export events to the vault. One file per month, `calendar 2026-02.md`, one line per event with date, time, title and location. Core search finds the lines, and unlinked mentions surface them in the place note without any linking work.

Rejected
- The obsidian-google-calendar plugin, unmaintained, already noted in [[idea - auto link notes to calendar]].
- [[obsidian-dataview]], not installed, and it would only pay off with per event notes and frontmatter.
- One note per event. Contradicts the position in [[idea - open google calendar events from notes]] that an event without a note belongs in the calendar only, and it would add thousands of notes.
- A custom calendar view or a browser extension with a create note button. Own software to maintain for a link that a pasted URI already gives.
- An ICS feed read into the vault. Nothing in core Obsidian reads ICS, so it needs a plugin or a parser.
- The Advanced URI plugin. The core `obsidian://open` URI covers opening a note by name.

Related: [[sync URL shortcuts to obsidian vault]] covers the same wish from the other side, a file in the vault standing in for an external item so autocomplete and backlinks work.
