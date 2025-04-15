LSPosed lets you customize how your Android phone and apps work, by injecting code _into them as they run_—without modifying the apps or system files directly.

### How it works:
- Built on top of **Riru** (a [[Magisk]] module that allows injecting code into [[Android]] processes).
- LSPosed **hooks** into the [[Zygote process]] (the process that spawns all Android apps) to **inject modules** at runtime.
- It supports **Xposed modules**, so it's essentially a modern, safer, and more compatible alternative to the original **Xposed Framework**, which doesn't work on modern Android versions anymore.

https://github.com/JingMatrix/LSPosed