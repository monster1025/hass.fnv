import appdaemon.plugins.hass.hassapi as hass

#
# Water leak detector
# close water valve and send a report
#
# Args:
#
# sensor = water leak sensor group
# valve = water valve - app will close it, when leak is detected
# notify = notify name to send notification
#
# None
#
# Release Notes
#
# Version 1.0:
#   Initial Version

class WaterLeak(hass.Hass):
  ringtone = 2
  gw_mac = ''
  sensors = []
  def initialize(self):
    if 'sensor' not in self.args or 'valve' not in self.args or 'notify' not in self.args:
      self.error("Please provide sensor, valve and notify in config!")
      return
    self.sensors = self.get_water_leak_sensors()
    self.log("leak sensors: {}".format(self.sensors))
    for sensor in self.sensors:
      self.listen_state(self.water_leak, sensor)

  def get_water_leak_sensors(self):
    sensors = []
    devices = self.get_state()
    for sensor in devices:
      if not sensor.startswith(self.args['sensor_prefix']):
        continue
      sensors.append(sensor)
    return sensors

  def water_leak(self, entity, attribute, old, new, kwargs):
    if new == "on":
      self.send_alarm(entity)

  def send_alarm(self, entity_id):
    self.log('water leak alarm triggered!')
    if 'constraint' in self.args and not self.constrain_input_boolean(self.args['constraint']):
      return

    #close water valve
    self.turn_off(self.args['valve'])
    ## to ensure that water is closed. It is important!!!
    self.call_service("mqtt/publish", topic = 'home/watercontrol/bath/valve/set', payload = 'close')
    self.call_service("xiaomi_aqara/play_ringtone", gw_mac=self.gw_mac, ringtone_id=self.ringtone, ringtone_vol=100)

    message = "ВНИМАНИЕ! В ваше отстутствие сработал датчик протечки воды ({})!!! Выключаю подачу воды.".format(self.friendly_name(entity_id))
    self.notify(message, name = self.args['notify'])

    message = "Состояние датчиков протечки:\n"
    for entity_id in self.sensors:
      message += '{} ({}) = {}\n'.format(self.friendly_name(entity_id), entity_id, self.get_state(entity_id))
    self.notify(message, name = self.args['notify'])