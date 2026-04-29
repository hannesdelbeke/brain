---
views: 6
created: 2026-04-23
---
I want to visualize [[Whatsapp]] calls on my [[Google calendar]], just how I [[2025-10 link Strava to Google calendar|visualize Strava activities on my Google calendar]].
- start time
- duration

main reason is to [[visualize time spent]]
expected impact: low - so don't spend a lot of time on this.

1. **Best effort, lowest friction**
   Detect WhatsApp call notifications and create events from what is available there.
   Risk: notification text/behavior may vary by device and Android version.

2. **Best effort + UI scrape**
   After a call, open WhatsApp Calls tab and read the latest call row with accessibility/UI automation.
   Risk: brittle if WhatsApp UI changes.

### Concrete Setup
1. Create a dedicated Google Calendar, e.g. `WhatsApp Calls`.
2. Deploy a [[Google Apps Script]] web app that accepts:
   - `contact`
   - `start`
   - `end`
   - `durationSeconds`
   - `direction`
3. Script creates an event like:
   - title: `WhatsApp call: Alice`
   - start: detected start time
   - end: detected end time
   - description: duration + source device
4. In Tasker:
   - grant Notification Access
   - grant Accessibility if using UI scraping
   - create a profile for WhatsApp call end detection
   - POST JSON to the Apps Script URL
5. If direct notification parsing is not enough on the device, add an AutoInput step that reads the newest entry from WhatsApp's Calls screen.

---

it seems quite hacky atm.

[[track time]]
