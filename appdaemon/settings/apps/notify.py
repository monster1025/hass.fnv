import appdaemon.plugins.hass.hassapi as hass

#
# Notification system
#
# Args:
# 
# Release Notes
#
# Version 1.0:
#   Initial Version

class BaseNotifyTarget():
  def notify(self, hass, message, person='*'):
    hass.log('notifying person {} with message: {}'.format(person, message))

class AliceNotifyTarget(BaseNotifyTarget):
  alice = 'media_player.yandex_station'
  def notify(self, hass, message, person='*'):
    msg = message
    if person == 'danil':
      msg = "Данил, " + msg
    elif person == 'sveta':
      msg = "Света, " + msg
    hass.log('notifying over alice person {} with message: {}'.format(target, message))
    self.say(hass, msg)

  def say(self, hass, message):
    hass.log('message = {}'.format(message))
    hass.call_service('media_player/play_media', entity_id=self.alice, media_content_type='text', media_content_id=message)

class TelegramNotifyTarget(BaseNotifyTarget):
  target_default = 'telegram'
  target_sveta = 'telegram_sveta'
  target_danil = 'telegram_monster'

  def notify(self, hass, message, person='*'):
    target = self.target_default
    if person == 'danil':
      target = self.target_danil
    elif person == 'sveta':
      target = self.target_sveta

    hass.log('notifying over telegram person {} with message: {}'.format(target, message))
    hass.notify(message, name=target)

class Notification(hass.Hass):
  home_targets = [AliceNotifyTarget()]
  away_targets = [TelegramNotifyTarget()]

  def initialize(self):
    self.log('Init')

  def notify_person(self, message, target='*', repeat = 1, delay = 60, onEvent = '', at=None):
    notifyTarget = None
    away_mode = True
    if (away_mode):
      notifyTarget = self.away_targets[0]
    else:
      notifyTarget = self.home_targets[0]

    self.log('message: {}'.format(message))
    notifyTarget.notify(self, message, person=target)