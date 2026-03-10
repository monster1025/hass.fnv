import appdaemon.plugins.hass.hassapi as hass
import datetime

#
# App to send email report for devices running low on battery
#
# Args:
#
# threshold = value below which battery levels are reported and email is sent
# always_send = set to 1 to override threshold and force send
#
# None
#
# Release Notes
#
# Version 1.0:
#   Initial Version

class Battery(hass.Hass):

  def initialize(self):
    #self.check_batteries({"force": 1})
    time = datetime.time(10, 0, 0)
    self.run_daily(self.check_batteries, time)
    self.check_batteries(None)
    
  def check_batteries(self, kwargs):
    if 'constraint' in self.args and not self.constrain_input_boolean(self.args['constraint']):
      return

    devices = self.get_state()
    values = {}
    low = []
    for deviceName in devices:
      device = devices[deviceName]
      if device == None:
        continue
      battery = None
      if "attributes" in device:
          if "battery" in device["attributes"]:
            battery = device["attributes"]["battery"]
          elif "battery_level" in device["attributes"]:
            battery = device["attributes"]["battery_level"]
          elif '_battery' in device['entity_id']:
            battery = self.get_state(device['entity_id'])
            if not battery.isdigit():
              continue
            battery = int(battery)
            print('{} = {}'.format(device['entity_id'], battery))
          if battery != None:
            print('{} = {}'.format(device['entity_id'], battery))
            if battery < self.args["threshold"] and battery != 0:
              low.append(deviceName)
            values[deviceName] = battery

    message=""
    if low:
      message += "У следующих датчиков садится батарея: (< {}) \n".format(self.args["threshold"])
      for device in low:
        message += "{}: {}%\n".format(self.friendly_name(device), values[device])
      message += "\n\n"
          
    if low: # or ("always_send" in self.args and self.args["always_send"] == 1) or ("force" in kwargs and kwargs["force"] == 1):
      if message != "":
        self.notify(message, name = "telegram")
