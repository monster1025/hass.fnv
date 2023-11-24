import appdaemon.plugins.hass.hassapi as hass

#
# Cover control by presence events
# Listen for presence events and change light state
#
# Args:
# entities - entities to turn on and off when presence is changed.
# Release Notes
#
# Version 1.0:
#   Initial Version

class CoverByPresence(hass.Hass):
  def initialize(self):
    if 'covers' not in self.args:
      self.error("Please provide covers in config!")
      return
    self.listen_event(self.away_mode, "away_mode")
    self.listen_event(self.return_home_mode, "return_home_mode")

    sunrise_offset = int(self.args.get('sunrise_offset', '0'))
    self.run_at_sunrise(self.run_at_sunrise_func, offset=sunrise_offset)
    sunset_offset = int(self.args.get('sunset_offset', '0'))
    self.run_at_sunset(self.run_at_sunset_func, offset=sunset_offset)

  def run_at_sunrise_func(self, kwargs):
    if 'constraint' in self.args and not self.constrain_input_boolean(self.args['constraint']):
      self.log('execution is disabled.')
      return
    for entity_id in self.args["open_at_sunrise"]:
      self.log('opening cover {} at sunrise'.format(entity_id))
      self.turn_on_custom(entity_id)

  def run_at_sunset_func(self, kwargs):
    if 'constraint' in self.args and not self.constrain_input_boolean(self.args['constraint']):
      self.log('execution is disabled.')
      return
    for entity_id in self.args["close_at_sunset"]:
      self.log('closing cover {} at sunset'.format(entity_id))
      self.turn_off_custom(entity_id)
  
  def away_mode(self, event_id, event_args, kwargs):
    if 'constraint' in self.args and not self.constrain_input_boolean(self.args['constraint']):
      self.log('execution is disabled.')
      return
    for entity_id in self.args["covers"]:
      self.turn_off_custom(entity_id)

  def return_home_mode(self, event_id, event_args, kwargs):
    if 'constraint' in self.args and not self.constrain_input_boolean(self.args['constraint']):
      self.log('execution is disabled.')
      return
    if self.sun_down():
      self.log('Sun is down, skip opening covers.')
      return
    entities = self.args["covers"]
    for entity_id in entities:
      self.turn_on_custom(entity_id)

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
