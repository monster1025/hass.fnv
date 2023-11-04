import appdaemon.plugins.hass.hassapi as hass
import os

#
# App to send notification when doorbell is ringing
#
# Args:
#
# notify = notification platform to send notifications to
# ringtone (optional) = ringtone to play
#
# None
#
# Release Notes
#
# Version 1.0:
#   Initial Version

class Doorbell(hass.Hass):
  ringtone = 10
  gw_mac = ''
  def initialize(self):
    if "notify" not in self.args or "sensor" not in self.args:
      self.error("Please provide notify, sensor in config!")
      return
    if "gw_mac" in self.args:
      self.gw_mac = self.args['gw_mac']

    if 'ringtone' in self.args:
      self.ringtone = self.args['ringtone']

    self.listen_state(self.sensor_trigger, self.args['sensor'])

  def sensor_trigger(self, entity, attribute, old, new, kwargs):
    if new == None or new == "None" or new == "" or new == "unknown":
      return
    self.log("doorbell call")
    self.log("old: {}, new: {}".format(old, new))
    self.call_service("xiaomi_aqara/play_ringtone", gw_mac=self.gw_mac, ringtone_id=self.ringtone, ringtone_vol=100)
    self.notify("Звонок в дверь!!!", name = self.args['notify'])
    # result = self.send_video()