import appdaemon.plugins.hass.hassapi as hass

#
# Listen for Alarm panel state change and fire an events ('away_mode' and 'return_home_mode')
#
# Args:
# ha_panel - alarm control panel entity.
# Release Notes
#
# Version 1.0:
#   Initial Version

class AlarmPanelAction(hass.Hass):
  extended_timeout = 5*60
  timers = []

  def initialize(self):
    if "ha_panel" not in self.args:
      self.error("Please provide ha_panel in config!")
      return
    self.listen_state(self.ha_panel_trigger, self.args['ha_panel'])
    extended_timeout = self.args.get('extended_timeout', self.extended_timeout)
    self.log('extended_timeout: {}'.format(self.extended_timeout))

  def ha_panel_trigger(self, entity, attribute, old, new, kwargs):
    # не срабатываем на triggered.
    if new == "armed_away" and old != "triggered":
      self.away_mode()
    if new == "disarmed" and old == "armed_away":
      self.return_home_mode()
  
  def away_mode(self):
    self.log('away_mode')
    self.fire_event('away_mode')

    if 'presence_extended' in self.args:
      self.fire_event('presence_extended_just_left')
      self.set_mode('Just Left')
      self.cancel_current_timer()
      self.timers.append(self.run_in(self.run_in_set_mode, self.extended_timeout, mode='Away'))


  def return_home_mode(self):
    self.log('return_home_mode')
    self.fire_event('return_home_mode')
    if 'presence_extended' in self.args:
      self.set_mode('Just Arrived')
      self.fire_event('presence_extended_just_arrived')
      self.cancel_current_timer()
      self.timers.append(self.run_in(self.run_in_set_mode, self.extended_timeout, mode='Home'))


  def set_mode(self, mode):
    if 'presence_extended' not in self.args:
      return
    entity_id = self.args['presence_extended']
    self.log('setting mode direct: {}={}'.format(entity_id, mode))
    self.call_service("input_select/select_option", entity_id = entity_id, option = mode)


  def run_in_set_mode(self, kwargs):
    if not 'mode' in kwargs:
      return
    mode = kwargs['mode']
    entity_id = self.args['presence_extended']
    event = 'presence_extended_{}'.format(mode.lower())
    self.log('firing event: {}'.format(event))
    self.fire_event(event)
    
    self.log('setting mode by timer: {}={}'.format(entity_id, mode))
    self.call_service("input_select/select_option", entity_id = entity_id, option = mode)

  def cancel_current_timer(self):
    for timer in self.timers:
      self.log('canceling timer')
      self.cancel_timer(timer)
    self.timers = []
