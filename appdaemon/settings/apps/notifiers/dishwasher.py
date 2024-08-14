import appdaemon.plugins.hass.hassapi as hass
from datetime import timedelta
import datetime

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
  run_state = ""

  def initialize(self):
    if 'run_state' not in self.args or 'door_sensor' not in self.args or 'counter' not in self.args:
      self.log("Please define all args")
      return

    self.listen_event_handle_list.append(self.listen_state(self.door_state_change, self.args['door_sensor'])) #, attribute='action'
    self.listen_event_handle_list.append(self.listen_state(self.run_state_change, self.args['run_state'])) #, attribute='action'


  def door_state_change(self, entity, attribute, old, new, kwargs):
    if (new == "on"):
      self.call_service("counter/increment", entity_id = self.args['counter'])
      if (self.run_state == "finished"):
        self.run_state = "collecting"
      self.set_light_state_by_counter()

  def run_state_change(self, entity, attribute, old, new, kwargs):
    self.log("event: {}: {}->{}".format(attribute,old,new))
    if (new == "Run"):
      self.log('resetting counter')
      self.call_service("counter/reset", entity_id = self.args['counter'])
      self.run_state = "washing"
    if (new == "Finished"):
      self.log('resetting counter')
      self.call_service("counter/reset", entity_id = self.args['counter'])
      self.run_state = "finished"

    self.log('Current state is: {}'.format(self.run_state))
    self.set_light_state_by_counter()

  def set_light_state_by_counter(self):
    state = self.get_state(self.args['counter'])
    open_count = int(state)
    self.log('counter state={}, machine state = {}'.format(state, self.run_state))

    if (self.run_state == "finished"):
      # Есть посуда, которую нужно разобрать
      # red color
      self.log('Time to take dishes out.')
      if 'lamp' in self.args:
        self.call_service("light/turn_on", entity_id = self.args['lamp'], rgb_color=[255, 0, 0]) #red

    elif (self.run_state == "washing"):
      self.log('washing in progress')
      self.call_service("light/turn_off", entity_id = self.args['lamp'])      

    elif (open_count > 10):
      self.log('Time to run dishwasher.')
      if 'lamp' in self.args:
        self.call_service("light/turn_on", entity_id = self.args['lamp'], rgb_color=[245, 236, 0]) #yellow

    else:
      self.call_service("light/turn_off", entity_id = self.args['lamp'])