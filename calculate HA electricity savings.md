**Summary** 
Using [[Home Assistant]] to control [[Home energy storage|home battery]] charging to maximize off peak usage, saves about 300-400£ per year on electricity bills.

Most savings come from taking advantage of cheaper electricity with [[Intelligent Octopus Go]] and charging my [[Home energy storage|home battery]] at the same time. And stop [[charging EV drains home battery|draining the home battery when EV charging]].
## Calculations
### Before
data before Home Assistant (Oct–Nov 2025)

| Week         | Cost   | kWh | Cost per kWh   |
| ------------ | ------ | --- | -------------- |
| 20–26 Oct    | £16.55 | 99  | £0.167/kWh |
| 13–19 Oct    | £16.50 | 112 | £0.147/kWh |
| 27 Oct–2 Nov | £14.55 | 82  | £0.177/kWh |
| 3–9 Nov      | £19.00 | 135 | £0.141/kWh |
Average before HA: **£0.158/kWh**
### After
Data after starting to use [[Home Assistant]] (Jan 2026)

| Week         | Cost   | kWh   | Cost per kWh   |
| ------------ | ------ | ----- | -------------- |
| 19–25 Jan    | £18.60 | 159   | £0.117/kWh |
| 12–18 Jan    | £13.46 | 124.7 | £0.108/kWh |
| 5–11 Jan     | £12.20 | 114   | £0.107/kWh |
| 29 Dec–4 Jan | £12.20 | 122   | £0.100/kWh |
Average after HA: **£0.108/kWh**
Reduced effective electricity cost per kWh by ~32%.
## Cost savings
A typical weekly usage is ~120–150 kWh:
- Before HA: ~£18–£24/week
- After HA: ~£12–£16/week

That’s:
- £6–£8 saved per week
- £25–£35 saved per month
- **£300–£400 saved per year**

## Overhead
Charging EV slowly in winter, wastes more energy keeping the EV on and the battery warm.
- Charge immediately when home, so battery is still warm from driving.
- Precondition battery before charging
- Use a higher kWh, less energy wasted.
- Charge less often, e.g. Instead of 20% → 60% every night, Do 20% → 80% every 2–3 nights.

But with [[off-peak]] cost 6p, and peak cost 28p / kWh, I could waste **367% extra energy** and _still_ be no worse than charging at peak. So overhead is negligible.

## Possible improvements
In the future, I might calculate total charge time needed per week, add a buffer, and then increase charge speed based on expected driving distance for the week. This would reduce wasted overhead. However, it adds more [[complexity]], dev [[time]], and there's a higher chance off using peak time if I don't drive for a week.

### Tags
[[electric vehicle|EV]]
[[home automation]]
[[calculations]]