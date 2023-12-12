import appdaemon.plugins.hass.hassapi as hass
import fnmatch

#
# Fire sensors alarm notification
# Send notification if some movement is detecter or door any is open
# while nobody is home
#
# Args:
# sensor - gorup of sensors to listen
# ha_panel - alarm panel entity
# notify - notify entity to send message
# 
# Release Notes
#
# Version 1.0:
#   Initial Version

class FireSensorsReport(hass.Hass):
  def initialize(self):
    if 'sensor_parts' not in self.args or 'notify' not in self.args:
      self.error("Please provide sensor_parts, ha_panel and notify in config!")
      return
    
    sensor_parts = self.args['sensor_parts']

    all_sensors = self.get_state()
    for entity_id in all_sensors:
      for part in sensor_parts:
        if fnmatch.fnmatch(entity_id, part):
          self.log(' [+] listening for security sensor {}'.format(entity_id))
          self.listen_state(self.sensor_trigger, entity_id)  

  def sensor_trigger(self, entity, attribute, old, new, kwargs):
    if 'constraint' in self.args and not self.constrain_input_boolean(self.args['constraint']):
      return

    if old != new and new == "on":
      self.log('Fire sensor is triggered!!!')
      self.alarm_triggered(entity, old, new)

  def alarm_triggered(self, entity, old, new):
    self.log('alarm triggered')

    friendly_name = self.friendly_name(entity)
    entity = entity.replace('_', '-')
    message = "Сработал датчик пожарной сигнализации {} ({}) = {}->{}!".format(friendly_name, entity, old, new)
    self.notify(message, name = self.args['notify'])