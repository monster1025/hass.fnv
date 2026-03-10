import appdaemon.plugins.hass.hassapi as hass
import datetime

#
# App to control main room light based on Aqara FP1 presence sensor
#
# Args:
#   presence_sensor: presence sensor entity_id (default: sensor.presence_aqara_mainroom_presence_event)
#   light: light entity_id (default: light.light_mainroom_pc_spotlight)
#
# Release Notes
#
# Version 1.0:
#   Initial Version

class MainRoomLightControl(hass.Hass):
    def initialize(self):
        self.presence_sensor = self.args.get("presence_sensor", "sensor.presence_aqara_mainroom_presence_event")
        self.light = self.args.get("light", "light.light_mainroom_pc_spotlight")
        
        self.log("Initializing light control application")
        self.log(f"Presence sensor: {self.presence_sensor}")
        self.log(f"Light: {self.light}")
        
        # Listen for presence events
        self.listen_state(self.state_change, self.args['presence_sensor'])
        self.log("Presence event handler registered")
        
    def state_change(self, entity, attribute, old, new, kwargs):        
        self.log(f"entity: {entity}, attribute: {attribute}, old: {old}, new: {new}")
        if new == "away":
            self.log("Status 'away' - turning off light")
            self.turn_off(self.light)
        else:
            self.log("Presence detected - turning on light")
            self.turn_on(self.light) 