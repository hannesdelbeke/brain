apply preset in same, or recursive parent folder.
This is a decentralized approach. with the presets living in the folder where they apply too.
https://docs.unity3d.com/Manual/DefaultPresetsByFolder.html
- [x] does this work on reset?
- [ ] more intuitive
- [ ] create a UPM package for this

The project settings / preset manager build in unity, is a centralized solution.
You enter paths, and set presets to apply on assets in those paths.
All presets are controlled from 1 location
- this also works on a reset
https://docs.unity3d.com/Manual/class-PresetManager.html
- can be overwhelming with lots of presets
- more flexibility on where to apply the presets (and more chance to go wrong)
- ships with unity

The definition where the presets are applied is [[centralized]]. Since the presets don't live where they are applied.

