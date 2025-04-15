With HA I've managed to expose my router to it, as well as both my PlayStations, my Roku TV and my 3 Google Home Minis.
## detect who is home
With my Router exposed I can monitor what devices are connected to my WiFi and use that information for automation purposes (for presence detection). That, coupled with information from the HA app and the Life360 app means my presence detection is perfect for my wife's iPhone and my Android phone (Life360 has better [[Global Positioning System|GPS]] monitoring on my wife's iPhone, or at least it did when I set it up 6 months ago).
## tv
The Roku and PlayStations means I can have HA react to media playback. It can see when my Roku is "playing" "paused" "standby" and "off" as well as change channel and volume with HA. I can (now) control using Google Home too but that is a recent addition (UK) so I was using HA to control my TV Through Google Assistant before that worked.
## child approach alarm
This means I can do those cool things where the lights react to the state of the TV. It's also pushed me to integrate Motion Sensors in my hallway. When the kids go to bed these motion sensors don't just control the lights in the hallway, it toggles a lamp to warn us a kid is coming and pauses the TV so they don't see anything they shouldn't.

## monitor kids tv time
With Covid lock down my kids weren't going to school and I wasn't going to work. They're old enough to get themselves up and stick the TV on, and since I wasn't going to work I stated saying in bed, but I wanted to know when they got up, so I made an automation that triggered my bedroom (Tuya) light to increase in brightness over time from the first time the TV went on. This meant I could wake up, look at the light and get an idea of how long my kids had been awake before rolling over and going back to sleep.

## remote turn on/off PC
HA can [[Wake on LAN|WOL]] my PC and [[Message Queuing Telemetry Transport|MQTT]] it back off again, which means I can use Google to turn it on and off, or have my "Goodnight" routine switch it off.

## make lights dimmer at night
With the HA phone app I've managed to make a bed sensor for myself and my wife based upon whether our phones are charging between certain times, so as long as we go to bed before 4.30am and get up before 11am it'll know we are in bed, meaning light brightness can be low before we get up so we don't wake each other or the kids, and bright after so we can see the carpet when we're vacuuming. Also when I'm at work (I start at 6am) I get a notification when my wife wakes up so I don't text her before and wake her.
## Tuya lights
You can keep your Tuya lights in [[Smart Life|Tuya]] and still control them with HA, you don't HAVE to flash them with Tuya Convert. I have one that WON'T flash and works just the same as the 3 I have.

## summary
Not trying to convince you here, just saying that there's more to [[Home Assistant]] than just the smart devices you think you have. I wasn't expecting the PlayStations or my Router to be exposed, or my Printer for that matter (it just gives me ink levels but it's there). Before I got HA on my Pi I was doing a lot of stuff with [[Smart Life]], Google, IFTTT and Tasker, but it's just easier with a dedicated Pi doing it all for me.

Also adding the Pi meant I could get a £10 USB zigbee stick and buy Tradfri bulbs at £6 each and magnetic switches at £6 each instead of having to buy an expensive hub to add zigbee into the equation.

No more "Oh fuck my phone's died and I wanted to turn the lights off downstairs" anymore, I can see it on my PC and Tablet dashboard, and I know it'll turn off when I say Goodnight to Google, when I push the switch next to my bed or when I plug my phone in at bed time.

[source](https://www.reddit.com/r/homeautomation/comments/j5g125/comment/g7x0cj4/)