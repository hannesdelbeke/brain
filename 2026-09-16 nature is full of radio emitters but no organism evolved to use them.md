---
date: 2026-09-16
created: 2026-09-16
tags:
  - physics
  - biology
  - wireless
aliases:
  - natural radio sources
  - does nature produce wifi-like signals
---

> [!summary] eli5
> lightning, the sun, jupiter, the aurora and anything warm all broadcast radio waves, the same physics as [[WiFi]] but a hundred thousand times slower than visible [[light waves]], so nature is noisy across the exact band a router uses.
> no living thing emits or receives radio though, because water absorbs microwaves, a useful antenna would have to be around 12 cm, and neurons top out near a kilohertz when a carrier needs gigahertz.
> the note is complete as an answer, nothing is pending on it.
> **needs from you:** decide whether to also add a bare-term `radio waves.md` stub next to the existing [[light waves]] and [[sound waves]] stubs so the term resolves on its own, recommend yes, it costs one line and the rest of the wave family already has one.

> does anything in nature produce signals similar to wifi. like there is light waves, warmth, infrared, radioactive, ...

**why:** root

## wifi is not a different kind of thing from light

**radio is the same electromagnetic radiation as visible [[light waves]] and [[infrared]]**, only much lazier. 2.4 GHz is a wave about 12 cm long, roughly a hundred thousand times lower in frequency than the light your eyes use. so the question is not whether nature makes radio, it is which natural things are bright in that band.

**warmth is the trivial case.** [blackbody radiation](https://en.wikipedia.org/wiki/Black-body_radiation) does not stop at infrared, it continues down through microwaves forever, just faintly. weather satellites read sea surface temperature and soil moisture by listening at 1.4, 6.9 and 23.8 GHz, and your own body is emitting at router frequencies right now at something like a trillionth of the power.

## the loud natural emitters

**lightning** is the big terrestrial one. a single flash is a broadband radio burst, most of its energy down at a few kilohertz as a [sferic](https://en.wikipedia.org/wiki/Radio_atmospheric_signal), with a tail running up into the gigahertz. that is the crackle on AM radio during a storm, and with roughly forty flashes a second worldwide it never stops.

**the sun** is measured in radio by convention. the standard index of solar activity is the [F10.7 cm flux](https://en.wikipedia.org/wiki/Solar_flux_unit), which is 2,800 MHz, next door to a 2.4 GHz router. a strong flare can matter on the ground, a [december 2006 burst](https://en.wikipedia.org/wiki/Solar_radio_burst) degraded GPS receivers across the sunlit hemisphere.

**earth's magnetosphere** sings. charged particles spiralling along field lines produce [whistlers and chorus](https://en.wikipedia.org/wiki/Chorus_(radio_wave)), very low frequency emissions that sound like birdsong and falling bombs once shifted into audio. seen from space earth is a radio-loud planet thanks to auroral kilometric radiation.

**jupiter** is the best amateur target, its interaction with the moon io drives bursts around 20 MHz through the [io flux tube](https://en.wikipedia.org/wiki/Io_(moon)) that a shortwave radio and a wire in the garden can pick up.

**the big bang** is still audible. the [cosmic microwave background](https://en.wikipedia.org/wiki/Cosmic_microwave_background) peaks near 160 GHz and spreads across the microwave band, and a small share of the static on an old untuned analogue TV was photons from 380,000 years after the big bang.

## the two that look like an actual signal

natural emission is almost all broadband noise, where wifi is narrowband, coherent and modulated. two natural things get close on the first two counts.

**cosmic masers** are the coherence case. clouds of water vapour, methanol or hydroxyl in star-forming regions act as natural microwave [[laser]]s, emitting one narrow bright line, water at 22.2 GHz and [methanol at 6.7 GHz](https://en.wikipedia.org/wiki/Astrophysical_maser), which lands inside the [[WiFi 6E]] band.

**pulsars** are the regularity case, a beam sweeping past with metronome timing, usually observed near 1.4 GHz. the first one found was nicknamed LGM-1 for little green men because nothing known could be that periodic. what both lack is modulation, they are steady or steadily repeating and carry no information.

## why biology never used radio

**no known organism emits or senses radio waves.** life invented light detection, infrared pit organs in vipers, ultraviolet vision in bees, magnetic sensing in birds and turtles, and bioluminescence, but skipped the radio band entirely.

**electric fish are the closest thing.** eels, knifefish and elephantnose fish generate electric fields and read the distortions, and signal to each other with them, different species holding distinct frequencies and shifting to avoid jamming. but [electroreception](https://en.wikipedia.org/wiki/Electroreception) is a near-field electric field at a few hundred hertz, not a radiating wave, and it works over centimetres.

three reasons the band stayed empty.

- **water absorbs microwaves**, which is why a microwave oven runs at 2.45 GHz through [dielectric heating](https://en.wikipedia.org/wiki/Dielectric_heating). a wet salty organism is close to the worst available material for making or receiving gigahertz radio.
- **the wavelength is too long.** an efficient antenna wants to be a decent fraction of 12 cm, a large rigid dry structure to grow for a weak link.
- **neurons are too slow.** they switch at kilohertz at best, and a gigahertz carrier needs electronics rather than ion channels.

so radioactivity, warmth, infrared and light are all on the natural list, and radio belongs there with them. it is the one band where biology never showed up, which is part of why [[wifi human detection]] works at all, the channel is quiet apart from what we put in it.
