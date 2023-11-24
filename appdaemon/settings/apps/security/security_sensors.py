import appdaemon.plugins.hass.hassapi as hass

#
# Security sensors alarm notification
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

class SecuritySensorsReport(hass.Hass):
  def initialize(self):
    if 'sensor_parts' not in self.args or 'ha_panel' not in self.args or 'notify' not in self.args:
      self.error("Please provide sensor_parts, ha_panel and notify in config!")
      return
    
    sensor_parts = self.args['sensor_parts']

    all_sensors = self.get_state()
    for entity_id in all_sensors:
      for part in sensor_parts:
        if part in entity_id:
          self.log(' [+] listening for security sensor {}'.format(entity_id))
          self.listen_state(self.sensor_trigger, entity_id)  

  def sensor_trigger(self, entity, attribute, old, new, kwargs):
    if 'constraint' in self.args and not self.constrain_input_boolean(self.args['constraint']):
      return

    if old != new and new == "on":
      alarm_panel_state = self.get_state(self.args['ha_panel'])
      if alarm_panel_state != "armed_away":
        return

      vacuum_state = "docked"
      if "vacuum" in self.args:
        vacuum_state = self.get_state(self.args["vacuum"])
      #Если работает пылесос и сработал датчик движения
      if vacuum_state == 'cleaning' and 'binary_sensor.motion' in entity:
        self.log('Motion sensor is triggered, but vacuum is cleaning.')
        return
      self.alarm_triggered(entity, old, new)

  def alarm_triggered(self, entity, old, new):
    self.log('alarm triggered')
    self.call_service("alarm_control_panel/alarm_trigger", entity_id = self.args['ha_panel'])

    friendly_name = self.friendly_name(entity)
    entity = entity.replace('_', '-')
    message = "В ваше отсутствие сработал датчик безопастности {} ({}) = {}->{}!".format(friendly_name, entity, old, new)
    self.notify(message, name = self.args['notify'])