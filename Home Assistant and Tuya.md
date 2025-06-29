
advice seems

buying:
- Prefer devices that support local [[Message Queuing Telemetry Transport|MQTT]] control (natively or via [[Zigbee2MQTT]]) over Tuya cloud-dependent ones. to not depend on tuya
- however most tuya zibgee devices will also work with a custom dongle.

using tuya zigbee devices with HA
- use the official HA addon for ease, but over internet so slower / less private
- use a local tuya HA addon, more maintenance & setup, less stable
- or buy a zigbee dongle and ditch tuya, use [[Zigbee Home Automation|ZHA]]


but if you have tuya, then:

Tuya devices default integrate with a [[Tuya hub]] and are meant to be used with their app. ([[Smart Life]], [[Tuya Smart]]). 

## official Tuya HA addon
To use them with [[Home Assistant]] using your [[Tuya hub]] the best way is to still go through the tuya servers:
- the official Tuya integration in Home Assistant, which requires an internet connection and Tuya's servers to process your requests. 

## zigbee dongle
to use them locally, you need to buy a zigbee dongle.
1. you can buy a usb stick (e.g. conbee 2 from deconz) and you can install some other integration: [zha](https://www.home-assistant.io/integrations/zha/), or official [deconz](https://www.home-assistant.io/integrations/deconz/) integration) to listen your devices and you can ditch your tuya hub. this works for all zigbee devices

## local tuya HA addons
There are a few local Tuya integrationa that will work after obtaining a local key for your device… Straightforward it is not. Getting the key can be complicated.
- local tuya HA extension
	- alternative to tuya-local: https://github.com/rospogrigio/localtuya/
	- https://github.com/make-all/tuya-local Home Assistant integration to support devices running Tuya firmware without going via the Tuya cloud. Devices are supported over WiFi,
	- another local  HA extension for tuya https://github.com/xZetsubou/hass-localtuya
advantage, no extra hardware (stick) to buy.
concerns:
- [reports](https://community.home-assistant.io/t/local-tuya-stopped-working-once-update-core-to-2025-1-0/821617/26) of HA breaking with the `local tuya` extension when updating HA to 2025. 
  but quickly fixed: [rospogrigio/localtuya](https://github.com/rospogrigio/localtuya/releases/v5.2.3)
  Tuya devices seem a bit more tricky to setup.
## outdated HA extensions & methods
- [[tuya-home-assist]] official HA extension by Tuya 1
- [[tuya-smart-life]] official HA extension by Tuya 2
- [[flash tuya devices]] outdated or complicated

