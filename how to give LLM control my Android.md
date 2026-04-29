---
views: 8
created: 2026-04-23
---

I want to let AI figure out how to do this and set it all up on my Android device.
- [[sync whatsapp calls to calendar]]

i use [[OpenAI Codex]] (fast, smart, but limited free usage) 
or [[gemini]] (free, slow) atm

---

- consider skills or MVC

 To let [[Artificial intelligence|AI]] set up your [[Android]] device directly, I need a control path from this machine to the phone. The practical options
  are:

  1. **[[ADB]] over [[USB]]**
     Best default.
     You connect the phone by USB, enable Developer options and USB debugging, approve the computer fingerprint, and
     then I can drive a lot from adb on the command line.
     What I can do:
      - inspect device state
      - install APKs
      - grant some permissions
      - push/pull files
      - launch apps/activities
      - capture logs
      - run taps/text input/screen automation with adb shell input
        Limitation:
      - some UI flows still need your confirmation on-device
      - accessibility-heavy automation app setup is partly manual
  2. **[[ADB]] over [[WiFi|Wi-Fi]]**
     Good once USB pairing is done.
     Initial pairing is usually easiest via USB, then I switch the device to TCP/IP and control it over local network.
     What I can do:
      - same class of adb operations without cable
        Limitation:
      - setup is more fragile than USB
      - both devices must stay on same network
  3. **[[control android from Windows|scrcpy]] + [[ADB]]**
     Best if you want me to guide or semi-directly operate the phone from desktop.
     scrcpy mirrors the Android screen to the PC and uses adb underneath. If you run it on this machine, I can tell you
     exactly what to click and use the mirrored output as the working surface if your environment supports it.
     What it adds:
      - much faster UI setup
