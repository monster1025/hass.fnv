import appdaemon.plugins.hass.hassapi as hass
import os

"""
Monitor events and output changes to the verbose_log. Nice for debugging purposes.
Arguments:
 - events: List of events to monitor
"""
class Test(hass.Hass):
  notify = None

  def initialize(self) -> None:
    self.listen_state(self.sensor_trigger, 'sensor.0x00158d0003a361d8_action')
    self.listen_state(self.sensor_trigger, 'binary_sensor.0x00158d0003f26d61_occupancy')
    # self.listen_state(self.sensor_trigger, 'sensor.remote20_action')

  def sensor_trigger(self, entity, attribute, old, new, kwargs):
    if new != "" and new != "unknown":
      self.log("doorbell call")
      self.toggle("switch.0x00158d00020f3a29_switch")