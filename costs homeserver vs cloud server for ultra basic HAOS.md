---
origin-sha: 22c983b0d
created: 2026-08-22
---
homeserver
- upfront: $50-$100 (raspberry pi, thin client, mini pc) + $20 ssd
- power: ~$15/year (5-10W average)
- access: optional $65/year nabu casa for remote & voice
- integrates local USB devices (zigbee) directly
- local network discovery works natively

cloud server (vps)
- monthly: ~$5/mo or $60/year for 2GB RAM vps (hetzner, etc)
- no upfront hardware cost
- remote access included
- needs network coordinator for local zigbee/z-wave
- breaks local network discovery without complex vpn

conclusion
homeserver breaks even in 1-2 years. cloud server makes local device discovery and usb dongles hard, defeating home assistant's main strength unless you only use cloud integrations.
