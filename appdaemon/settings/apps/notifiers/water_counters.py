import appdaemon.plugins.hass.hassapi as hass
import datetime
import globals

#
# App to send notifications when counters state needs attention
#
# Args:
#
#
# None
#
# Release Notes
#
# Version 1.0:
#   Initial Version

class WaterCountersAlarm(hass.Hass):
  checkup_threasold = 31
  send_threasold = 31

  def initialize(self):
    if not globals.check_args(self, ['checkup_threasold', 'send_threasold']):
      return
    self.checkup_threasold = self.args['checkup_threasold']
    self.send_threasold = self.args['send_threasold']
    
    self.check_send_dates({"force": 1})
    self.run_daily(self.check_checkup_dates, datetime.time(10, 0, 0))
    self.run_daily(self.check_send_dates, datetime.time(10, 1, 0))
    #self.check_checkup_dates([])

  def check_send_dates(self, kwargs):
    if 'constraint' in self.args and not self.constrain_input_boolean(self.args['constraint']):
      return
    devices = self.get_state()
    if devices == None:
      return
    values = {}
    send_devices = []
    for deviceName in devices:
      device = devices[deviceName]
      if (device == None):
        continue
      send_date = None
      if "attributes" in device:
          if "date" in device["attributes"]:
            send_date = device["attributes"]["date"]
          if send_date != None:
            self.log('found device {} with send date {}'.format(deviceName, send_date))
            if send_date == "":
                send_devices.append(deviceName)
            else:
              send_date_date = None
              if '-' in send_date:
                send_date_date = datetime.datetime.strptime(send_date, '%Y-%m-%d')
              else:
                send_date_date = datetime.datetime.strptime(send_date, '%d.%m.%Y')
              if send_date_date < (datetime.datetime.now() - datetime.timedelta(days=self.send_threasold)):
                send_devices.append(deviceName)
            values[deviceName] = send_date

    message=""
    if send_devices:
      message += "ВНИМАНИЕ! У вас есть счетчики, показания по которым давно не передавались:\n"
      for device in send_devices:
        message += "- {}: {}\n".format(self.friendly_name(device), values[device])
      message += "\n\n"

    if send_devices or ("always_send" in self.args and self.args["always_send"] == 1) or ("force" in kwargs and kwargs["force"] == 1):
      if message != "":
        self.notify(message, name = "telegram")
    
  def check_checkup_dates(self, kwargs):
    if 'constraint' in self.args and not self.constrain_input_boolean(self.args['constraint']):
      return

    entities = self.get_state()
    if entities == None:
      return
      
    values = {}
    checkup_devices = []
    for entity_id in entities:
      entity = entities[entity_id]
      if entity == None:
        # self.log('not found {} in entities list.'.format(entity_id))
        continue
      checkup = None
      if "attributes" in entity:
          if "checkup" in entity["attributes"]:
            checkup = entity["attributes"]["checkup"]
          if checkup != None:
            self.log('found device {} with checkup date {}'.format(entity_id, checkup))
            checkup_date = datetime.datetime.strptime(checkup, '%Y-%m-%d')
            if (checkup_date - datetime.timedelta(days=self.checkup_threasold)) < datetime.datetime.now():
              checkup_devices.append(entity_id)
            values[entity_id] = checkup

    message=""
    if checkup_devices:
      message += "ВНИМАНИЕ! У вас есть счетчик, нуждающийся в поверке:\n"
      for device in checkup_devices:
        message += "- {}: {}\n".format(self.friendly_name(device), values[device])
      message += "\n\n"

    if checkup_devices or ("always_send" in self.args and self.args["always_send"] == 1) or ("force" in kwargs and kwargs["force"] == 1):
      if message != "":
        self.notify(message, name = "telegram")