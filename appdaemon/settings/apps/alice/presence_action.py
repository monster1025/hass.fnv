import appdaemon.plugins.hass.hassapi as hass
import globals
import time

#
# Home and away report
# Send report about home state after presence_actions was done.
# 
# Args:
# entity - group of entities to send state report
# notify - notify entity to send message
# 
# Release Notes
#
# Version 1.0:
#   Initial Version

class PresenceAction(hass.Hass):
  report_delay = 15
  def initialize(self):
    if 'alice' not in self.args:
      self.error("Please provide alice in config!")
      return
    self.listen_event(self.away_mode, "away_mode")
    self.listen_event(self.return_home_mode, "return_home_mode")

  def away_mode(self, event_id, event_args, kwargs):
    if 'constraint' in self.args and not self.constrain_input_boolean(self.args['constraint']):
      return
    self.command('стоп')

  def return_home_mode(self, event_id, event_args, kwargs):
    if 'constraint' in self.args and not self.constrain_input_boolean(self.args['constraint']):
      return
    command = 'Добро пожаловать домой.'
    self.run_in(self.run_in_say, 59, command=command)

  def run_in_say(self, kwargs):
    if 'command' not in kwargs:
      return
    text = kwargs['command']
    self.say(text)

  def command(self, command):
    self.call_service('yandex_station/send_command', command='sendText', text=command)

  def say(self, command):
    self.log('command = {}'.format(command))
    self.call_service('media_player/play_media', entity_id=self.args['alice'], media_content_type='text', media_content_id=command)