import appdaemon.plugins.hass.hassapi as hass
import os
import globals

#
# App to send notification when doorbell is ringing
#
# Args:
#
# notify = notification platform to send notifications to
# ringtone (optional) = ringtone to play
#
# None
#
# Release Notes
#
# Version 1.0:
#   Initial Version

class Doorbell(hass.Hass):
  def initialize(self):
    if "notify" not in self.args:
      self.error("Please provide notify, sensor, camera in config!")
      return
    self.listen_event(self.ha_event, "doorbell_call")

  def ha_event(self, event_name, data, kwargs):
    self.log('{}:{}'.format(event_name, data))

    globals.send_telegram(self, "Звонок в дверь!!!", target = self.args['notify'])
    if 'doorbell_pic' in data:
      globals.send_telegram_photo(self, data['doorbell_pic'], target = self.args['notify'], caption = "Фото звонившего")

    self.say('Звонок в дверь')

  def command(self, command):
    self.call_service('yandex_station/send_command', command='sendText', text=command)

  def say(self, command):
    if 'alices' in self.args:
      for alice in self.args['alices']:
        self.log('command = {}'.format(command))
        self.call_service('media_player/play_media', entity_id=alice, media_content_type='text', media_content_id=command, extra={'volume_level': 0.8})
