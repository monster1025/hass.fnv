import appdaemon.plugins.hass.hassapi as hass
import appdaemon.plugins.mqtt.mqttapi as mqtt
import globals
import json
import random
import time
import datetime

class HappyBubblesToDeviceTracker(mqtt.Mqtt, hass.Hass):
    base_topic = "happy-bubbles/presence/ha"
    tag_timers = {}

    def initialize(self) -> None:
        self.log('Initialize HappyBubblesToDeviceTracker')
        self.mqtt_subscribe('{}/#'.format(self.base_topic), namespace='mqtt')
        self.listen_event(self.event_listener, 'MQTT_MESSAGE', namespace='mqtt')
    
    def event_listener(self, event_name, data, kwargs):
        topic = data.get('topic', '')
        if self.base_topic    not in topic:
            return
        location = topic.replace('{}/'.format(self.base_topic), "")

        payload = json.loads(data['payload']) if data.get('payload') else {}
        # self.log('[{}] topic: {}, payload: {}'.format(event_name, topic, payload))
        id = payload.get('id', None)
        name = payload.get('name', None)
        distance = payload.get('distance', None)

        # devices = self.get_state()
        # device_name = "device_tracker.tag_ble_{}".format(id)
        # if device_name in devices:
        #     self.log('tag found in devices')
        
        self.move_tag(id, isHome=True)
        self.restart_timer(id)
        
        self.log('Beacon {} ({}) moved to {} (distance: {}).'.format(name, id, location, distance))
    
    def restart_timer(self, id):
        if id in self.tag_timers:
            self.cancel_timer(self.tag_timers[id])
        self.tag_timers[id] = self.run_in(self.tag_away_timer_callback, 60, id=id)
    
    def tag_away_timer_callback(self, kwargs):
        id = kwargs.get('id', None)
        if id == None:
            self.log('id is forgotten')
            return

        self.log('awaying tag:{}'.format(id))
        self.move_tag(id, isHome=False)

    def move_tag(self, id, isHome = False):
        hb_topic = "owntracks/tag/ble_{}".format(id)
        tst = int(round(time.time(),0))
        payload = '{"_type":"location","acc":18,"alt":0,"batt":100,"lat":55.7899036,"lon":37.6595347,"tst":1579857481}'
        jsobj = json.loads(payload)
        jsobj['tst'] = tst
        if isHome:
            jsobj['lat'] = self.args['home_lat']
            jsobj['lon'] = self.args['home_lon']
        else:
            jsobj['lat'] = 0
            jsobj['lon'] = 0
        payload = json.dumps(jsobj)
        self.mqtt_publish(hb_topic, payload, qos = 0, retain = False, namespace='mqtt')        
