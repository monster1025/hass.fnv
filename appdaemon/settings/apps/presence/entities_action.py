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
  def initialize(self):
    if 'away_entities' not in self.args or 'return_entities' not in self.args:
      self.error("Please provide away_entities and return_entities in config!")
      return
    self.listen_event(self.away_mode, "away_mode")
    self.listen_event(self.return_home_mode, "return_home_mode")

  def away_mode(self, event_id, event_args, kwargs):
    if 'constraint' in self.args and not self.constrain_input_boolean(self.args['constraint']):
      return
    for entity_id in self.args["away_entities"]:
      self.turn_off(entity_id)

  def return_home_mode(self, event_id, event_args, kwargs):
    if 'constraint' in self.args and not self.constrain_input_boolean(self.args['constraint']):
      return
    for entity_id in self.args["return_entities"]:
      self.turn_on(entity_id)
