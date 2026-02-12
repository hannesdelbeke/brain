# Tailscale + Home Assistant
**Home Assistant + Tailscale (Android + HA Add‑on)**

I wanted easy remote access to my [[Home Assistant]] instance, and got it working:

## **1. Create your Tailscale account**

Use any identity provider (Google, Microsoft, GitHub).  
Install Tailscale on your **phone**, **PC**, and anything else you want in the tailnet.

---

# **2. Add Home Assistant to Tailscale**

Install the HA Tailscale add‑on.

> [!warning]
> The official Tailscale addon is for monitoring, not connecting to Tailscale.
> I use this one https://github.com/hassio-addons/app-tailscale/blob/main/tailscale/DOCS.md

### **Start the add‑on and authenticate**
1. Start the add‑on
2. Open the **Logs**
3. Scroll to the bottom — you’ll see a URL like:
```
https://login.tailscale.com/a/some-long-token
```

4. Copy/paste that URL into your browser
5. Authenticate the device named **homeassistant**

Once authenticated, your HA box appears in your tailnet with a 100.x.x.x address.

---

# **3. Configure the Home Assistant Android app**

### **Set the external URL to the Tailscale IP**
In the app:
- **Home Assistant URL** → `http://100.xx.xx.xx:8123`
- **Internal Connection URL** → `http://homeassistant.local:8123/`  
    
This gives you:
- Local mDNS access when on Wi‑Fi
- Tailscale access when remote
### **Ensure Tailscale is running on Android**

Open the Tailscale app → make sure the connection is **Active**.

Now the HA app will connect remotely through Tailscale.

---
# TODO
test the below step 4

# **4. The quirk you noticed: needing to disconnect Tailscale on home Wi‑Fi**

This is normal unless you enable one of the following:

### **Option A — Allow LAN access while Tailscale is active**

In the Android Tailscale app:

- Settings → **Route all traffic** → turn **off**
- Settings → **Exit node** → ensure **none** is selected

This allows local LAN traffic even when Tailscale is connected.

### **Option B — Force the HA app to use the internal URL on Wi‑Fi**

The HA app automatically switches between internal/external URLs **only if**:

- Internal URL resolves
- AND the network is considered “local”

If Tailscale is routing all traffic, HA never sees your LAN → it sticks to the external URL → which may not work if your router blocks hairpin NAT or if Tailscale is overriding DNS.

The workaround (disconnecting Tailscale) works, but a cleaner fix is disabling “route all traffic”.

---

# **5. Result**

- **Local access** via `homeassistant.local:8123`
- **Remote access** via `100.x.x.x:8123`
- No port forwarding
- No reverse proxies
- No Cloudflare tunnels
- End‑to‑end encrypted access everywhere

---

Next steps could be

- Make the HA app switch between internal/external URLs automatically
- Add MagicDNS so you can use a stable hostname instead of the 100.x.x.x address
- Use Tailscale for presence detection in Home Assistant
- Fix routing so you never need to disconnect Tailscale on Wi‑Fi again

