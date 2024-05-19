  
[[Unreal]] [[color model]]

In Unreal Engine, the hue value in the color adjustment property is clamped between 0 and 359 rather than 0 and 255 due to the representation of colors in the HSV (Hue, Saturation, Value) color model. 

Here’s why 359 is used:

1. **Hue Range in Degrees**:
    
    - Hue in the HSV color model is typically represented in degrees, ranging from 0 to 360. However, since the hue wraps around (360 degrees is the same as 0 degrees), the range is often represented as 0 to 359 to avoid redundancy.
2. **Human Perception of Color**:
    
    - The HSV model is designed to align more closely with human perception of color than the RGB model. It separates the chromatic content (hue) from the intensity (value) and purity (saturation). This makes adjustments like hue shifts more intuitive.
    - Hue represents the type of color and varies from 0 to 359 degrees, covering the full spectrum of colors. For example, 0 degrees is red, 120 degrees is green, and 240 degrees is blue.
3. **Avoiding Redundancy**:
    
    - Using 359 ensures that each degree value represents a unique color. Allowing 360 would be redundant since 360 degrees is effectively the same as 0 degrees (both represent red in the color wheel).
4. **Consistency in Color Models**:
    
    - Most graphic applications and color pickers that use HSV or HSL (Hue, Saturation, Lightness) models follow the convention of using a hue range from 0 to 359 degrees.
5. **Ease of Interpolation and Calculation**:
    
    - When performing color transitions and interpolations, it is easier to work within a 0 to 359 range for calculations involving circular rotations.

Using 255 or 256 would align more with the RGB color model, where each color channel (Red, Green, Blue) typically has 256 possible values (0-255). However, this does not map as intuitively to the concept of hue, which is inherently a circular property best represented in degrees.

Therefore, in the context of adjusting the hue in Unreal Engine, using a range of 0.0 to 359.0 makes the most sense both mathematically and perceptually.