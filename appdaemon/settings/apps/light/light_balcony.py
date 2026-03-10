import appdaemon.plugins.hass.hassapi as hass
import datetime

#
# App to control balcony room light based on lux and door sensor
#
# Args:
#   door_sensor: door contact sensor
#   lux_sensor: xiaomi lux sensor
#   light: light entity_id
#   lux_min: min lux value to turn light on
#
# Release Notes
#
# Version 1.0:
#   Initial Version

class BalconyLightControl(hass.Hass):
    def initialize(self):
        self.door_sensor = self.args.get("door_sensor", "binary_sensor.door_balcony_contact")
        self.light = self.args.get("light", "light.light_balcony_spotlight")
        self.lux_sensor = self.args.get("lux_sensor", "sensor.brightness_balcony_illuminance")
        self.lux_min = self.args.get("lux_min", 100)

        self.log("Initializing balcony light control application")
        self.log(f"Door sensor: {self.door_sensor}")
        self.log(f"Lux sensor: {self.lux_sensor}")
        self.log(f"Lux min: {self.lux_min}")
        self.log(f"Light: {self.light}")
        
        # Listen for presence events
        self.listen_state(self.state_change, self.args['door_sensor'])
        self.log("Presence event handler registered")
        
    def state_change(self, entity, attribute, old, new, kwargs):        
        self.log(f"door entity: {entity}, attribute: {attribute}, old: {old}, new: {new}")
        lux = int(self.get_state(self.lux_sensor))
        if new == "on":
            self.log("Door is open, lux: {}, lux_min: {}".format(lux, self.lux_min))
            if lux < self.lux_min:
                self.turn_on(self.light)
            else:
                self.log("high lux value, skip turn light on")
        elif new == "off":
            self.log("Door is closed, lux: {}, lux_min: {}".format(lux, self.lux_min))
            self.turn_off(self.light)