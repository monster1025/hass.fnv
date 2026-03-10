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

class AliceIntents(hass.Hass):
  entity_id = None

  def initialize(self):
    self.listen_event(self.yandex_intent, "yandex_intent")

  def yandex_intent(self, event_id, event_args, kwargs):
    self.log("{} {}".format(event_id, event_args))
    text = event_args['text']
    room = event_args['room']
    alice = event_args['entity_id']
    if text == 'Как дела':
      self.entity_id = alice
      self.run_in(self.run_in_say, 10, command="Кто здесь в {}?".format(room))

  def run_in_say(self, kwargs):
    if 'command' not in kwargs:
      return
    text = kwargs['command']
    self.say(text)

  def command(self, command):
    self.call_service('yandex_station/send_command', command='sendText', text=command)

  def say(self, command):
    self.log('command = {}'.format(command))
    self.call_service('media_player/play_media', entity_id=self.entity_id, media_content_type='text', media_content_id=command)