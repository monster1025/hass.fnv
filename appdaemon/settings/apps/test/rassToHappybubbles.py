import appdaemon.plugins.hass.hassapi as hass
import appdaemon.plugins.mqtt.mqttapi as mqtt
import globals
import json
import random

"""
Monitor events and output changes to the verbose_log. Nice for debugging purposes.
Arguments:
 - events: List of events to monitor
"""

class RassToHappyBubbles(mqtt.Mqtt):
    base_topic = "home/presence"
    def initialize(self) -> None:
        self.log('Initialize RassToHappyBubbles')
        self.mqtt_subscribe('{}/#'.format(self.base_topic), namespace='mqtt')
        self.listen_event(self.event_listener, 'MQTT_MESSAGE', namespace='mqtt')
    
    def event_listener(self, event_name, data, kwargs):
        topic = data.get('topic', '')
        if self.base_topic	not in topic:
        	return
        #array = ['hall', 'balcony']
        #random.shuffle(array)
        #device=array[0]

        device = topic.replace('{}/'.format(self.base_topic), "")
        payload = json.loads(data['payload']) if data.get('payload') else {}
        id = payload.get('id', None)
        hb_topic="happy-bubbles/ble/{}/raw/{}".format(device,id)
        payload['hostname'] = device
        payload['mac'] = payload.get('id', '')

        payload_data = json.dumps(payload)
        self.mqtt_publish(hb_topic, payload_data, qos = 0, retain = False, namespace='mqtt')
        # self.log('publishing to: {}: {}'.format(hb_topic, payload_data))
