import appdaemon.plugins.hass.hassapi as hass

#
# App to show dishwasher state
#
# Args:
#
# door_sensor = dishwasher door sensor
#
# None
#
# Release Notes
#
# Version 1.0:
#   Initial Version

class Dishwasher(hass.Hass):
  listen_event_handle_list = []

  def initialize(self):
    if 'run_state' not in self.args or 'door_sensor' not in self.args or 'counter' not in self.args or 'state_extended' not in self.args:
      self.log("Please define all args")
      return

    self.listen_event_handle_list.append(self.listen_state(self.door_state_change, self.args['door_sensor']))
    self.listen_event_handle_list.append(self.listen_state(self.run_state_change, self.args['run_state']))


  def get_extended_state(self):
    return self.get_state(self.args['state_extended'])

  def set_extended_state(self, state):
    self.call_service("input_select/select_option", entity_id = self.args['state_extended'], option = state)

  def door_state_change(self, entity, attribute, old, new, kwargs):
    if new != "on":
      return

    self.call_service("counter/increment", entity_id = self.args['counter'])
    extended_state = self.get_extended_state()
    open_count = int(self.get_state(self.args['counter']))

    if extended_state == "Washed":
      self.set_extended_state("Empty")
    elif extended_state == "Empty":
      if open_count < 10:
        self.set_extended_state("Collecting Dishes")
      elif open_count > 10:
        self.set_extended_state("Ready to wash")
    elif extended_state == "Collecting Dishes" and open_count > 10:
      self.set_extended_state("Ready to wash")

    self.set_light_state_by_counter()

  def run_state_change(self, entity, attribute, old, new, kwargs):
    self.log("event: {}: {}->{}".format(attribute, old, new))
    if new == "Run":
      self.log('resetting counter')
      self.call_service("counter/reset", entity_id = self.args['counter'])
      self.set_extended_state("Washing")
    elif new == "Finished":
      self.log('resetting counter')
      self.call_service("counter/reset", entity_id = self.args['counter'])
      self.set_extended_state("Washed")

    self.log('Current state is: {}'.format(self.get_extended_state()))
    self.set_light_state_by_counter()

  def set_light_state_by_counter(self):
    open_count = self.get_state(self.args['counter'])
    extended_state = self.get_extended_state()
    self.log('counter state={}, machine state = {}'.format(open_count, extended_state))

    if extended_state == "Washed":
      self.log('Time to take dishes out.')
      if 'lamp' in self.args:
        self.call_service("light/turn_on", entity_id = self.args['lamp'], rgb_color=[255, 0, 0])

    elif extended_state == "Washing":
      self.log('washing in progress')
      if 'lamp' in self.args:
        self.call_service("light/turn_off", entity_id = self.args['lamp'])

    elif extended_state == "Ready to wash":
      self.log('Time to run dishwasher.')
      if 'lamp' in self.args:
        self.call_service("light/turn_on", entity_id = self.args['lamp'], rgb_color=[245, 236, 0])

    elif 'lamp' in self.args:
      self.call_service("light/turn_off", entity_id = self.args['lamp'])
