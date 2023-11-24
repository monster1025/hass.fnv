import appdaemon.plugins.hass.hassapi as hass

#
# Light control by presence events
# Listen for presence events and change light state
#
# Args:
# entities - entities to turn on and off when presence is changed.
# Release Notes
#
# Version 1.0:
#   Initial Version

class EntitiesByPresence(hass.Hass):
  mode = None
  def initialize(self):
    if 'away_entities' not in self.args or 'return_entities' not in self.args:
      self.error("Please provide away_entities and return_entities in config!")
      return
    self.listen_event(self.away_mode, "away_mode")
    self.listen_event(self.return_home_mode, "return_home_mode")
    self.determine_current_mode()
    self.set_thermostat_by_mode(None)
    self.timer = self.run_every(self.set_thermostat_by_mode, 'now', 5*60)

  def determine_current_mode(self):
    state = self.get_state('input_select.presence_extended')
    if state == 'Home' or state == 'Just Arrived':
      self.mode = 'home'
    else:
      self.mode = 'away'

  def away_mode(self, event_id, event_args, kwargs):
    if 'constraint' in self.args and not self.constrain_input_boolean(self.args['constraint']):
      return
    self.mode = 'away'
    for entity_id in self.args["away_entities"]:
      self.turn_off_custom(entity_id)
    self.set_thermostat_by_mode(None)

  def return_home_mode(self, event_id, event_args, kwargs):
    if 'constraint' in self.args and not self.constrain_input_boolean(self.args['constraint']):
      return
    self.mode = 'home'
    entities = self.args["return_entities"]
    if entities == None:
      entities=[]
    for entity_id in entities:
      self.turn_on_custom(entity_id)
    self.set_thermostat_by_mode(None)

  def set_thermostat_by_mode(self, kwargs):
    if "thremostats" not in self.args:
      return
    preset = 'away'
    if self.mode == 'home':
      preset = 'manual'
    for entity_id in self.args["thremostats"]:
      state = self.get_state(entity_id, 'preset_mode')
      if state != preset:
        self.log('Set thermostat ({}), current state = {}, set mode to {}'.format(entity_id, state, preset))
        self.call_service("climate/set_preset_mode", entity_id=entity_id, preset_mode = preset)

  def turn_on_custom(self, entity_id):
    if 'cover.' in entity_id:
      self.call_service("cover/open_cover", entity_id=entity_id)
      return
    self.turn_on(entity_id)

  def turn_off_custom(self, entity_id):
    if 'cover.' in entity_id:
      self.call_service("cover/close_cover", entity_id=entity_id)
      return
    self.turn_off(entity_id)
