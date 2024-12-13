
can be set in preferences/package manager

| cache name     | default location                                          | preferences tab |
| -------------- | --------------------------------------------------------- | --------------- |
| unity packages | `C:\\Users\\H\\AppData\\Local\\Unity\\cache`              | package manager |
| my assets      | `C:\\Users\\H\\AppData\\Roaming\\Unity`                   | package manager |
| GI Cache       | `C:\\Users\\H\\AppData\\LocalLow\\Unity\\Caches\\GICache` | GI Cache        |



---

# Unverified
some interesting notes from a forum post
these have not been verified.
## Package Cache

1. Move the complete '`C:\ProgramData\Package Cache`' directory to another place (the source directory 'Package Cache' must be deleted)
2. Create the junction: `mklink /J “C:\ProgramData\Package Cache” “D:\ProgramData\Package Cache”`

## Unity GI cache

1. Open Unity preferences
2. Open the ‘GI cache tab’
3. Clean the GI cache
4. Set a new place for the GI cache

## Unity AssetStore download

1. Move the '`C:\users\username\appdata\roaming\unity\asset store-5.x`' directory to the destination (the source directory 'asset store-5.x' must be deleted)
2. Create the junction: `mklink /J “C:\users\username\appdata\roaming\unity\asset store-5.x” “E:\users\username\appdata\roaming\unity\asset store-5.x”`

## Move other caches away

Step 1: Open the System properties (right-click on the ‘Computer’ icon, select ‘Properties’, then click on on ‘Advanced system properties’  
Step 2: Add the ‘`UPM_NPM_CACHE_PATH`’ variable with the destination directory (do not create the destination directory)  
Step 3: Add the ‘`UPM_CACHE_PATH`’ variable with the destination directory (do not create the destination directory)  
Step 4: Delete the ‘npm’ and ‘packages’ directories from '`C:\Users<USER_NAME>\AppData\Local\Unity\cache`'  
Step 5: Restart the computer

[[Unity]]
[[cache]]