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

Xiaomi MiMo Studio (`aistudio.xiaomimimo.com`) is the web interface for Xiaomi's [[large language model]] family (like MiMo-V2.5-Pro). Access outside approved regions hits a multi-stage geoblock.

## Layer 1: DNS sinkhole
Authoritative nameservers (Tencent DNSPod) sinkhole queries from UK and EU resolvers to `127.0.0.1` (localhost). The browser tries port 443 locally, gets `Connection refused`, and displays `Unable to connect`.

Resolvers in US, Singapore, or Japan return Xiaomi's Alibaba Cloud Singapore edge (`mimo-pri-alisgp.alb.xiaomi.com`, e.g. `47.236.158.11`).

**Quick bypasses for layer 1:**
- map domain directly in `/etc/hosts` (`echo "47.236.158.11 aistudio.xiaomimimo.com" | sudo tee -a /etc/hosts`)
- use a [[virtual private network|VPN]] set to US, Singapore, or Japan
- developer portal (`platform.xiaomimimo.com`) and `mimo.xiaomi.com` aren't DNS-sinkholed

## Layer 2: Post-login geo-restriction
Bypassing layer 1 loads the site. Once logging in with Google OAuth, the web app errors with:
`This service is not available in your region yet.`

Likely triggers:
- browser-level VPN extension leaks the real IP via WebRTC or IPv6
- VPN exit node is detected as a datacenter IP or placed in an unsupported region
- Google OAuth callback returns an account country or locale flagged as EU/UK
- server-side session handshake checks the client IP against strict regional allowlists

## Agent investigation instructions
Next agent picking this up should test:

**Check browser IP leaks**
- verify if Firefox WebRTC leaks the host IP (`about:config` -> set `media.peerconnection.enabled` to `false`)
- disable IPv6 in Firefox (`network.dns.disableIPv6 = true`) or use a system-wide OS VPN rather than a browser proxy extension

**Test account & OAuth metadata**
- inspect OAuth callback network payload in devtools to see if account `locale` or country is sent to Xiaomi's auth endpoint
- test logging in with a non-Google method (e.g. phone/SMS or Xiaomi account if supported) or a non-EU Google account

**Test direct API access**
- verify whether the API cluster endpoints on `platform.xiaomimimo.com` enforce the same regional block
- check third-party model routers (e.g. OpenRouter, DeepInfra) that serve MiMo models without regional frontend restrictions
