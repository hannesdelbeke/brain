## problem
When a Tuya [[smart socket]] stops reporting energy use data, [[Home Assistant]] reports incorrect energy usage. (Remotely toggling the plug on/off still works.)
## context
sometimes my smart plugs seem to stop reporting electricity data. and even when off are still reporting last reported data, in this case 100W
- stuck on 100W in smart life
- stuck on 100W in local tuya [[home assistant integration|integration]]
- not showing in tuya [[home assistant integration|integration]]
### Smart life wi-fi test fail
When I run a Wi-Fi test in [[Smart Life|SmartLife]], it fails on the last step
1. click on the ✏️ pencil in the top right corner
2. click `Check Device Network`, which shows:
	- Connect to Device ✅
	- Get Device's Wi-Fi Signal Strength ✅
	- Detect network connection status 🔃
This last step fails with message:
**Searched device Is Not nearby.**
*Make sure the mobile phone and smart device run over the same Wi-Fi network.
If so, check whether the port and UDP settings are correct. 
Low power Wi-Fi devices currently do not support network detection*

I wonder if this could be related to my new router setup, around 2026-01-14. 🤔
However, one socket stopped reporting only a few days ago 2026-01-29.
		
## Solution
We can't detect this condition directly, but we can infer it from power usage not changing for a while.

### 1. Corrected power helper
Create helper that reports 0 Power when the power usage hasn't changed for a while. 

Settings → Devices & Services → Helpers → Create Helper
Template → Sensor
Name: Power Corrected
Unit of measurement: W
State template: 
```jinja2
{% set last = states.sensor.my_socket_power.last_changed %}
{% set age = as_timestamp(now()) - as_timestamp(last) %}
{% set stale = age > 600 %}

{{ 0 if stale else states('sensor.my_socket_power') }}
```

#### Cons
This is a hacky workaround and doesn't fix the issue. 
- It might incorrectly report 0W.
- The plug reports the stuck power every x hours/days, so there are false positive spikes.
#### Pros
It won't over-report incorrect power in the energy dashboard, and should increase accuracy of uncategorized energy use. Setting power to 0W will move all the energy use to the "unknown" category, instead of mis-attributing it to the device.
### 2. Restart
The better solution is to restart the smart plug when this condition is detected. But this is a manual solution, and can't be automated.

Powering off the smart plug fixes the non reporting issue. But it needs to be powered off manually at the plug. Powering it off remotely keeps the communication channel open and isn't a full power cycle.

We can make an automation to send a notification when this condition is detected, so we can go and power cycle the plug.
#### Create automation

Settings → Automations → Create Automation → Start with an empty automation

When
	State
		Entity: sensor.socket_power
		Attribute, From, To: leave empty
		For: 10 minutes
		
And If:
	State
		Entity: sensor.socket_power
		Attribute: leave empty
		State: On
		For:: leave empty
		
Then do
	Send notification
		Title: Smart plug not reporting power
		Message:
```jinja2
Smart plug power stuck at {{ states('sensor.h_office_big_light_power_2') }}W. Please power cycle the plug.
```

## Other
- test what happens to plug on router restart
- could my mesh network mess with the plugs?

### Tags
[[my home assistant]]