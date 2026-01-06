An exercise to develop a bot that can edit the titles of [[Google Calendar]] events.
Goal is to auto run it on startup to edit certain google titles.
### Prerequisites
- A **Google Cloud project** with the Calendar API enabled
- OAuth 2.0 credentials (for user authorization)
- Python (or your preferred language) and `google-api-python-client` installed
### Step 1: Set Up Google Cloud & OAuth
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project
3. Enable the **Google Calendar API**
4. Go to **APIs & Services > Credentials**
5. Create **OAuth 2.0 Client ID** credentials
    - Choose "Desktop App" or "Web App" depending on your bot
6. Download the `credentials.json` file
### Step 2: Install Required Libraries
```bash
pip install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib
```
### 🔒Step 3: Authenticate and Access Calendar
```python
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/calendar']

def get_calendar_service():
    flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
    creds = flow.run_local_server(port=0)
    service = build('calendar', 'v3', credentials=creds)
    return service
```
> [!warning] 
> had to change path of `credentials.json` for it to be detected

> [!warning] 
> when auth in browser, I get the error
> `# Access blocked: Wellhub Calendar title editor has not completed the Google verification process`
> had to add myself as a test user in https://console.cloud.google.com/auth/audience
### ✏️ Step 4: Edit Event Titles
```python
def update_event_title(service, calendar_id='primary', event_id='', new_title='Updated Title'):
    event = service.events().get(calendarId=calendar_id, eventId=event_id).execute()
    event['summary'] = new_title
    updated_event = service.events().update(calendarId=calendar_id, eventId=event_id, body=event).execute()
    print(f"Updated event: {updated_event['summary']}")
```
### 🔍 Step 5: Find Events to Edit
You can list events and filter by date, keyword, etc.:
```python
def list_events(service, calendar_id='primary'):
    events_result = service.events().list(calendarId=calendar_id, maxResults=10, singleEvents=True,
                                          orderBy='startTime').execute()
    events = events_result.get('items', [])
    for event in events:
        print(f"{event['id']}: {event.get('summary')} at {event['start'].get('dateTime', event['start'].get('date'))}")
```
> [!warning] 
> had to add minTime so we don't start from very first calendar event
### Example Usage
```python
service = get_calendar_service()
list_events(service)
update_event_title(service, event_id='your_event_id_here', new_title='Team Sync Updated')
```

## Run on startup
```batch
Python D:\repos\wellhub-calendar\main.py
```
open [[Windows task scheduler]]
set app to full path of [[Python]]
add script path in arguments
add `input` to python script to keep console open for debugging
run task to test
when all works, I set to run on log on

repo https://github.com/hannesdelbeke/calendar-wellhub
[[public/automate]] editing calendar events created by [[wellhub]]

## other
someone else used similar tech to [auto set alarms](https://www.reddit.com/r/Android/comments/1gi8ux/remote_alarm_clock_ever_wanted_to_set_your_phones/) on your phone when it detects an event named "alarm" in your calendar. 
#### tags
[[Python snippet]]
[[Google calendar]]
