import appdaemon.plugins.hass.hassapi as hass
from datetime import timedelta
import datetime
import globals

#
# App to send email report for devices running low on battery
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

class Teeth(hass.Hass):
  listen_event_handle_list = []

  def initialize(self):
    # Устанавливаем сброс в 10 утра
    reset_time = datetime.time(10, 0, 0)
    self.run_daily(self.reset_action, reset_time)

    # Запускаем проверку напоминаний
    self.timer = self.run_every(self.remind_if_needed, self.datetime()+timedelta(seconds=1), self.args['remind_interval'])

    # Слушаем изменения состояния кнопки
    self.listen_event_handle_list.append(self.listen_state(self.button_state_change, self.args['mute_button']))

  def button_state_change(self, entity, attribute, old, new, kwargs):
    self.log("event: {}={}".format(attribute,new))
    if attribute == 'state' and new == 'single':
      self.log('Muting notifications')
      self.set_state(self.args['mute_boolean'], state='on')
      self.say("Принято")

  def say(self, command):
    self.log('command = {}'.format(command))
    self.call_service('media_player/play_media', entity_id=self.args['alice'], media_content_type='text', media_content_id=command)

  def reset_action(self, kwargs):
    self.log('Resetting mute state')
    self.set_state(self.args['mute_boolean'], state='off')

  def remind_if_needed(self, kwargs):
    # Проверяем состояние input_boolean
    if self.get_state(self.args['mute_boolean']) == 'on':
      return

    if 'constraint' in self.args and not self.constrain_input_boolean(self.args['constraint']):
      self.log('disabled by constraint')
      return

    home_sensors = []
    if 'home_sensors' in self.args:
      home_sensors = self.args['home_sensors']

    at_home = False
    is_any = False
    for sensor in home_sensors:
      is_any = True
      state = self.get_state(sensor)
      if state != 'not_home':
        at_home = True
    if not is_any:
      at_home = True

    if not at_home:
      self.log('User is away, skipping notification')
      return

    notify = "telegram"
    if "notify" in self.args:
      notify = self.args["notify"]
    now = datetime.datetime.now()+timedelta(hours=3)
    message="Уже {}, а ты еще не почистил зубы. Самое время =)".format(now.strftime("%H:%M"))
    globals.send_telegram(self, message, target = notify)
