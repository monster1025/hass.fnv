import appdaemon.plugins.hass.hassapi as hass

#
# Listen for presence sensor change state and change alarm control panel state.
#
# Args:
# sensor - home presence 'sensor'
# ha_panel - alarm control panel entity (to arm and disarm).
# constraint - (optional, input_boolen), if turned off - alarm panel will be not armed\disarmed.
#
# Release Notes
#
# Version 1.0:
#   Initial Version

class AlarmPanelBySensor(hass.Hass):
  def initialize(self):
    if "sensor" not in self.args or "ha_panel" not in self.args:
      self.error("Please provide sensor and ha_panel in config!")
      return
    self.listen_state(self.sensor_trigger, self.args['sensor'])
    self.listen_event(self.ha_event, "ha_started")
  
  def ha_event(self, event_name, data, kwargs):
    self.log('Starting up!')
    state = self.get_state(self.args['sensor'])
    self.log('Updating alarm_control_panel state: {}'.format(state))
    if state == "off":
        self.away_mode()

  def sensor_trigger(self, entity, attribute, old, new, kwargs):
    self.log("{} turned {}".format(entity, new))
    if new == "off" and old == "on":
      self.away_mode()
    if new == "on" and old == "off":
      self.return_home_mode()
  
  def away_mode(self):
    if 'constraint' in self.args and not self.constrain_input_boolean(self.args['constraint']):
      return
    self.call_service("alarm_control_panel/alarm_arm_away", entity_id = self.args['ha_panel'])

  def return_home_mode(self):
    if 'constraint' in self.args and not self.constrain_input_boolean(self.args['constraint']):
      return
    self.call_service("alarm_control_panel/alarm_disarm", entity_id = self.args['ha_panel'])