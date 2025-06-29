
- In the past you could flash Tuya devices with custom firmware like Tasmota or ESPHome, but now Tuya has made it harder to do so. Hardware (e.g. chip) can also be unpredictable

- hacking your Tuya hub to run custom software like [[zigbee2mqtt]], which allows you to send Zigbee messages directly to Home Assistant via MQTT.
	- easier to instead buy a non-tuya zigbee dongle


hacking your zigbee hub so that we can install a process to send all [[ZigBee]] messages to home assistant (as your hub is a very basic [[Linux]] computer).
   We should install [[zigbee2mqtt]] software there,
   and enable MQTT broker on your home assistant instance. 
   Zigbee2mqtt sends messages to home assistant MQTT broker
   and MQTT broker processes them for home assistant, and you're good.
   [HACK GUIDE](https://paulbanks.org/projects/lidl-zigbee/ha/)