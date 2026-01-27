### Goal
Currently charge and discharge are set at 85A, could I lower this to increase battery life, and reduce charging [[noise (sound)|noise]]?

### Calculations
The [[Home energy storage|home battery]] is scheduled to charge when the off-peak energy starts, which is at 11.30pm, and ends at 530am. (see [[Intelligent Octopus Go]])
Currently the battery starts charging at 11.30pm, and is full by 2am, so we have 3.5 hours left where the battery just sits at full.

How much percent to decrease charging?
- Reduce charge current by ~60%.
- From 85 A → about 35 A.

> [!NOTE]- 
> `power` in [[SunSynk inverter]] time refers to [[Sunsynk L5.3 5.32kWh battery|battery]] discharge only - [docs](https://support.sunsynk.com/support/solutions/articles/103000244987-understanding-timer-settings)

### Outcome
Changed discharge to 50A, charge to 35A. Battery is now full by 5.30am.
Charging stress is now spread more evenly over the off-peak period, reducing stress on the battery and potentially extending its lifespan. 💪

[[home automation]]
[[calculations]]