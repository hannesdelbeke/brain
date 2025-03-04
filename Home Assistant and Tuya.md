  

to integrate a tuya hub and all devices with [[Home Assistant]]. 

1. using official [tuya integration](https://www.home-assistant.io/integrations/tuya/) which relies on the internet and Tuya's servers to process  your requests. 
2. hacking your zigbee hub so that we can install a process to send all [[zigbee]] messages to home assistant (as your hub is a very basic [[Linux]] computer).
   We should install [[zigbee2mqtt]] software there,
   and enable MQTT broker on your home assistant instance. 
   Zigbee2mqtt sends messages to home assistant MQTT broker
   and MQTT broker processes them for home assistant, and you're good.
   [HACK GUIDE](https://paulbanks.org/projects/lidl-zigbee/ha/)
3. you can buy a usb stick (e.g. conbee 2 from deconz  advised) and you can install some other integration: [zha](https://www.home-assistant.io/integrations/zha/), or official [deconz](https://www.home-assistant.io/integrations/deconz/) integration) to listen your devices and you can ditch your tuya hub. this works for all zigbee devices, not [[WiFi]]. 