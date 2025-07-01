Air can contain more water the hotter it is.
So when you heat air, the relative humidity (percentage of water in air) becomes lower.
## Example
If we heat air with 20°C & 77% [[humidity]], to 25°C, the new relative humidity is 58%

## Code
```python
import math


def saturation_vapor_pressure(temp_c):
    """Approximate saturation vapor pressure using the Magnus formula (in hPa)"""
    return 6.112 * math.exp((17.62 * temp_c) / (243.12 + temp_c))

def relative_humidity_after_heating(initial_temp, initial_rh, final_temp):
    # Calculate initial vapor pressure
    e_initial = saturation_vapor_pressure(initial_temp) * (initial_rh / 100.0)
    # Final saturation vapor pressure
    e_final_sat = saturation_vapor_pressure(final_temp)
    # New RH
    new_rh = (e_initial / e_final_sat) * 100
    return round(new_rh, 2)
```
### Code example
```python
t1 = 20  # initial temp °C
rh1 = 77  # initial RH %
t2 = 25  # final temp °C

new_rh = relative_humidity_after_heating(t1, rh1, t2)
print(f"After heating from {t1}°C to {t2}°C, RH drops to: {new_rh}%")
# After heating from 20°C to 25°C, RH drops to: 57.95%
```