The redirect script transforms the custom `unityasset://` URI into a standard `http://localhost:5000/` URL, so it can be handled by the local server inside Unity.

---

### **How the Redirect Works**
When an external app (e.g., a web browser, another program, or even a script) tries to open a `unityasset://` link, Windows/macOS doesn’t know how to handle it by default. The script converts the `unityasset://` URI into an HTTP request and sends it to Unity’s local server.

1. **User clicks a link**  
   - Example: `unityasset://Assets/MyFolder/MyPrefab.prefab`
   
2. **OS invokes the redirect script**  
   - On Windows, the `.bat` script runs  
   - On macOS, the `.sh` script runs  

3. **Script modifies the URI**  
   - It replaces `unityasset://` with `http://localhost:5000/`  
   - Becomes: `http://localhost:5000/Assets/MyFolder/MyPrefab.prefab`

4. **Script opens the modified URL**  
   - The script launches the modified URL using `start` (Windows) or `open` (macOS), sending the request to Unity’s deep link server.

5. **Unity receives the request**  
   - The local HTTP server in Unity processes the request and opens the asset.

---

### **Windows Redirect Script (`redirect.bat`)**
```bat
@echo off
set URL=%1
set URL=%URL:unityasset://=http://localhost:5000/% 
start "" "%URL%"
```
#### **Explanation:**
- `%1` is the first argument (the full URI passed to the script).
- `set URL=%URL:unityasset://=http://localhost:5000/%` replaces `unityasset://` with `http://localhost:5000/`.
- `start "" "%URL%"` opens the modified URL in the browser, sending the request to Unity.

#### **How to Register the Protocol in Windows**
1. Open **Registry Editor (`regedit`)**.
2. Navigate to `HKEY_CLASSES_ROOT`.
3. Create a new key called `unityasset`.
4. Inside `unityasset`, create a `shell\open\command` subkey.
5. Set the **default value** of `command` to:
   ```
   "C:\Path\To\redirect.bat" "%1"
   ```

---

### **Mac Redirect Script (`redirect.sh`)**
```sh
#!/bin/bash
url="${1//unityasset:\/\//http://localhost:5000/}"
open "$url"
```
#### **Explanation:**
- `${1}` is the first argument (the full URI).
- `${1//unityasset:\/\//http://localhost:5000/}` replaces `unityasset://` with `http://localhost:5000/`.
- `open "$url"` sends the request to Unity via a browser.

#### **How to Register the Protocol on macOS**
1. Add the following to your app’s `Info.plist`:
   ```xml
   <key>CFBundleURLTypes</key>
   <array>
       <dict>
           <key>CFBundleURLName</key>
           <string>com.yourcompany.unityasset</string>
           <key>CFBundleURLSchemes</key>
           <array>
               <string>unityasset</string>
           </array>
       </dict>
   </array>
   ```
2. Associate `unityasset://` links with `redirect.sh` using `open` command.

---

### **Testing the Deep Link**
After setting up the script and registering the protocol:
- Run this in a browser or command line:
  ```
  unityasset://Assets/MyFolder/MyPrefab.prefab
  ```
- It should open the asset inside Unity.

Would you like help automating the registry setup or debugging any issues? �