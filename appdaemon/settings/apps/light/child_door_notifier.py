import appdaemon.plugins.hass.hassapi as hass
import globals
import datetime

class ChildDoorNotifier(hass.Hass):
  isLocked = False

  def initialize(self):
    if not globals.check_args(self,['entities', 'sensor']):
      return

    self.listen_event_handle_list = []
    self.listen_event_handle_list.append(self.listen_state(self.state_change, self.args['sensor'])) #, attribute='action'

  def state_change(self, entity, attribute, old, new, kwargs):
    self.log('state = {}'.format(new))
    if new == "on":
      self.log('open')
      for i in range(1, 7):
        self.run_in(self.switch_light, i)

  def switch_light(self, kwargs):
    for entity in self.args['entities']:
      self.toggle(entity)