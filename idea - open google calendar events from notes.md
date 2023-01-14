I want to easily [[link]] [[calendar entry|calendar events]] in my [[note taking|notes]]
And when I click them, it shows me the calendar week overview, so I see what's happening that day/week, and how it fits into the bigger planning picture.

## UX

### auto complete on tab
my current [[Obsidian]] note workflow is nice, because it has auto complete on tab.
I type `[[`, start typing the note title or alias, and auto complete.

How can I achieve something equally smooth for calendar events?

### examples
- i write about a hike, and want to auto link to the calendar event
- i write about a restaurant, or sports class, or anything that means something to me, and is in my calendar.

---

another flow i consider
1. i go to my calendar view, and click "create note" on an event.
2. it auto creates a note and links it

- either make my own calendar view, e.g. an app linked to google calendar.
- or create a browser extension to add the create note button to the google calendar experience in the browser
## why
when do I want to link to calendar events?

## spec
- On my pc, I use [[Google calendar]] in my [[browser]] 
- On my phone, I use the [[google calendar]] Android app.
Ideally I support both workflows, but I mostly use notes on my pc so focus on that. Later I can look into a more [[portable]] workflow. 

Bonus if it also works with other apps, not just [[Obsidian]]. I use Obsidian for now but maybe not in the future. Others might use Notion etc.

The `0` in the URL `u/0/r/` is the first logged-in account in google, change it if needed.

Show 
- current week https://calendar.google.com/calendar/u/0/r/week
- a specific week https://calendar.google.com/calendar/u/0/r/week/2025/11/3
- a day https://calendar.google.com/calendar/u/0/r/day/2025/11/3
- there's no way to link to a private event

- i don't care about making events searchable in obsidian. An event without note should only show in calendar
- i often go back to the [[2025-11-16 obsidian data lake|data lake idea]]. Data is data. a note, an event, a contact
### Related
Recently I wrote about [[2025-10-21 write more on location|a more portable note taking setup]]