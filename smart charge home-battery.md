**problem**
The main problem is that [[charging EV drains home battery|charging my EV drains my home battery]]

**solution**
I mostly want to prevent draining my battery. (e.g. disable battery?)
But it'd be great if I could [[automate sunsynk inverter - dynamic charge battery|recharge my battery during day off peak hours]].

ways to get more off peak hours:
- [[Intelligent Octopus Go - automate EV charger - get off peak hours in day|auto control EV charger]]
- manually plug in car at lunch time

## Details
[[Intelligent Octopus Go - 2026 EV charge 6h cap]]

Since a 5kwh battery lasts half a day, mid day off peak time could fully charge the battery

## Implementation

> [!NOTE]- Implementation plan
> service to run and auto handle optimal
> 
> - start smart charge
> - auto detect when cheap time is provided by [[octopus energy]]
> - ensure charge speed in tesla is 5A or lower. maybe we can lower it on the charger?
> - stop charge at 11pm, when cheap time kicks in, and enable at 6am
> 
> - if cheap time, tell [[SunSynk inverter]] to charge [[Sunsynk L5.3 5.32kWh battery]]
> 
> API needs
> - tesla control
> - [[SunSynk]] control
> - octopus read and likely control (enable smart)
> 	- might be able to stop charger through monta or ev sync app

I implemented this Jan 2026
- disable battery when charging EV
- I wasn't able to access my tesla battery level, but the octopus can access it, so i just set the percentage in the app. And then enable disable smart charging from HA. This lets octopus create the smart schedule, and initiate the charge instead.

[[Home Assistant examples]]