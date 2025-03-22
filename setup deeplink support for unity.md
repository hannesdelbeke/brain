
If Unity is already open, you need a way for it to receive and handle the deep link without restarting. The best approach is to use **a local server inside Unity** to listen for URI requests or use **IPC (Inter-Process Communication) techniques**.

---

## **Method 1: Local HTTP Server (Recommended)**
You can run a small HTTP server inside Unity using `HttpListener`, so external apps can send asset URIs to Unity.

### **1. Create a Deep Link Listener Script**
This script starts a local HTTP server inside Unity and listens for asset URIs.

```csharp
using UnityEngine;
using UnityEditor;
using System;
using System.Net;
using System.Threading;
using System.IO;
using System.Collections.Generic;

[InitializeOnLoad]
public class DeepLinkServer
{
    private static HttpListener listener;
    private static Thread serverThread;
    private static readonly int port = 5000;
    private static readonly Queue<string> assetQueue = new Queue<string>();
    private static readonly object lockObject = new object();

    static DeepLinkServer()
    {
        StartServer();
        EditorApplication.update += ProcessQueue;
    }

    private static void StartServer()
    {
        if (listener != null) return;

        listener = new HttpListener();
        listener.Prefixes.Add($"http://localhost:{port}/");
        listener.Start();

        serverThread = new Thread(() =>
        {
            while (listener.IsListening)
            {
                try
                {
                    HttpListenerContext context = listener.GetContext();
                    HttpListenerRequest request = context.Request;
                    string assetPath = request.RawUrl.TrimStart('/'); // Extract asset path
                    assetPath = Uri.UnescapeDataString(assetPath);

                    if (!string.IsNullOrEmpty(assetPath))
                    {
                        lock (lockObject)
                        {
                            assetQueue.Enqueue(assetPath); // Queue the operation for the main thread
                        }
                    }

                    // Send response
                    HttpListenerResponse response = context.Response;
                    string responseString = "Asset selection requested: " + assetPath;
                    byte[] buffer = System.Text.Encoding.UTF8.GetBytes(responseString);
                    response.ContentLength64 = buffer.Length;
                    Stream output = response.OutputStream;
                    output.Write(buffer, 0, buffer.Length);
                    output.Close();
                }
                catch (Exception ex)
                {
                    Debug.LogError("DeepLinkServer error: " + ex.Message);
                }
            }
        });

        serverThread.IsBackground = true;
        serverThread.Start();
        Debug.Log($"Deep Link Server running on http://localhost:{port}/");
    }

    private static void ProcessQueue()
    {
        lock (lockObject)
        {
            while (assetQueue.Count > 0)
            {
                string assetPath = assetQueue.Dequeue(); // Always dequeue the item

                if (string.IsNullOrEmpty(assetPath))
                    continue; // Skip empty requests

                SelectAsset(assetPath);
            }
        }
    }


    private static void SelectAsset(string assetPath)
    {
        UnityEngine.Object asset = AssetDatabase.LoadMainAssetAtPath(assetPath);
        if (asset != null)
        {
            Selection.activeObject = asset;
            EditorGUIUtility.PingObject(asset);
            Debug.Log($"Selected Asset: {assetPath}");
        }
        else
        {
            Debug.LogError($"Asset not found: {assetPath}");
        }
    }

    [MenuItem("Tools/Restart Deep Link Server")]
    public static void RestartServer()
    {
        StopServer();
        StartServer();
    }

    private static void StopServer()
    {
        if (listener != null)
        {
            listener.Stop();
            listener.Close();
            listener = null;
        }

        if (serverThread != null && serverThread.IsAlive)
        {
            serverThread.Abort();
        }
    }
}

```

---

### **2. Modify Your URI Handling**
Instead of a `unityasset://` scheme, use an HTTP request:
```
http://localhost:5000/Assets/MyFolder/MyPrefab.prefab
```
This will send a request to Unity, which will then open the asset inside the editor.

---

### **3. Automate External Calls**
If you still want to use `unityasset://` URIs, create a simple script that redirects them:

- **Windows (`.bat` script)**:
  ```bat
  @echo off
  set URL=%1
  set URL=%URL:unityasset://=http://localhost:5000/% 
  start "" "%URL%"
  ```

- **Mac (`.sh` script)**:
  ```sh
  #!/bin/bash
  url="${1//unityasset:\/\//http://localhost:5000/}"
  open "$url"
  ```

---

## **Method 2: Named Pipes (IPC)**
If you don’t want an HTTP server, another approach is using **Named Pipes** for communication between external apps and Unity. You can set up a named pipe server in Unity and send messages to it from an external script.

Would you like a named pipe example, or does the local server method work for you? �

--

## Redirect

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


## alternatives
- not maintained https://github.com/nicbarker/UnityEditorDeeplinking
- uses native unity asset store URI https://github.com/AdamCarballo/HookInterceptor
	- blogpost https://f10.dev/blog/using-a-stream-deck-in-unity/

[[unity deeplink - needle tools]]
