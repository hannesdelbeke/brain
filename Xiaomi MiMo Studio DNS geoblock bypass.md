---
tags:
- ai
- networking
- dns
- troubleshooting
aliases:
- xiaomi mimo studio blocked
- aistudio.xiaomimimo.com unable to connect
- bypass xiaomi mimo dns sinkhole
---

Xiaomi MiMo Studio (`aistudio.xiaomimimo.com`) is the web interface to test Xiaomi's [[large language model]] family (like MiMo-V2.5-Pro). In the UK and EU, browsers fail with `Unable to connect` / `Connection refused`.

## Why it fails
The block is a regional DNS sinkhole configured on Xiaomi's authoritative nameservers (Tencent DNSPod), likely set up to avoid EU AI Act or GDPR compliance hurdles.

When querying from European resolvers, DNS returns `127.0.0.1` (localhost). The browser tries connecting to local port 443, finds no local web server listening, and immediately errors out.

When querying from the US, Singapore, or Japan, DNS resolves to Xiaomi's Alibaba Cloud edge (`mimo-pri-alisgp.alb.xiaomi.com`). The server firewall itself doesn't block European IP addresses; only the DNS query is poisoned.

## How to bypass

**Map domain in hosts file**
Bypasses the poisoned DNS lookup without routing traffic through a third party. Add Xiaomi's Singapore ALB IP to `/etc/hosts`:

```bash
echo "47.236.158.11 aistudio.xiaomimimo.com" | sudo tee -a /etc/hosts
```

Flush browser socket cache or restart the browser, then reload the page.

**Use a [[virtual private network|VPN]]**
Route traffic through a server in the US, Singapore, or Japan. Authoritative DNS returns the real edge IP automatically.

**Use the developer platform**
The API portal at `platform.xiaomimimo.com` and main site `mimo.xiaomi.com` aren't sinkholed and remain reachable worldwide without overrides.
