import appdaemon.plugins.hass.hassapi as hass
import os
import glob
import json
import time

"""
Monitor events and output changes to the verbose_log. Nice for debugging purposes.
Arguments:
 - events: List of events to monitor
"""
class TestAc(hass.Hass):
  notify = None

  def initialize(self) -> None:
    self.log('start')
    #for i in range(256):
    #  pkt = "AA AA AA {} 00 00 C8 87 1B 40 55".format(self.int_to_hex(i))
    #  self.log(pkt)
    #  self.call_service("esphome/coffee_philips_5400_send_custom_command_disp", command=pkt)
    #  time.sleep(2)
    
  #   for file in glob.glob("/conf/apps/test/ir/*.json"):
  #     f = open(file)
  #     data = json.load(f)
  #     if (data['supportedController'] != 'Broadlink'):
  #       continue
  #     manufacturer = data['manufacturer']
  #     supportedModels = data['supportedModels'][0]
  #     self.log('file: {}, manufacturer: {}, supportedModels: {}'.format(file, manufacturer, supportedModels))
  #     key1 = data['operationModes'][0]
  #     key2 = data['fanModes'][0]
  #     minTemp = data['minTemperature']+6
  #     off = data['commands']['fan_only'][key2]["{}".format(minTemp)]
  #     off = data['commands']['off']
  #     command = "b64:{}".format(off)
  #     self.call_service("remote/send_command", entity_id = "remote.rm_mini", command = command)
