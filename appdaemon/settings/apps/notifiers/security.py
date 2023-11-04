import appdaemon.plugins.hass.hassapi as hass
import datetime

#
# App to send reports about unsuccessfull auths
#
# Args:
#
# threshold = value below which battery levels are reported and email is sent
# always_send = set to 1 to override threshold and force send
#
# None
#
# Release Notes
#
# Version 1.0:
#   Initial Version

class Security(hass.Hass):
  def initialize(self):
    self.log('---------------------')
    self.listen_event_handle_list = []
    self.listen_event_handle_list.append(self.listen_state(self.state_change, 'persistent_notification.http_login', attribute='message'))

  def state_change(self, entity, attribute, old, new, kwargs):
    notifier = self.args.get('notify', 'telegram')
    self.notify(new, name = notifier)
    self.log(new)