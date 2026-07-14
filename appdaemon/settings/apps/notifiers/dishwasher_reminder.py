import appdaemon.plugins.hass.hassapi as hass
import random

#
# App to remind about dishwasher when someone enters the kitchen
#
# Args:
#
# state_extended = input_select with extended dishwasher state
# motion_sensors = list of motion sensors to watch
# alice = Yandex Station media_player entity
# cooldown (optional) = seconds between reminders, default 1800
# constraint (optional) = input_boolean to enable/disable the app
#
# Release Notes
#
# Version 1.0:
#   Initial Version
# Version 1.1:
#   Added "Ready to wash" reminders

class DishwasherReminder(hass.Hass):
  PHRASES_WASHED = [
    "Посудомойка готова! Пора разобрать посуду.",
    "Чистая посуда сидит в посудомойке как в Open Space — пора выпустить на волю.",
    "Посудомойка отработала, теперь твоя очередь — разгрузить.",
    "Тарелки уже высохли и скучают, спаси их из посудомойки.",
    "Посудомойка не склад для чистого, разгрузи уже.",
    "Грязной посуды нет, а чистая застряла внутри — спасательная операция!",
    "Посудомойка помыла всё, осталось только разобрать. Ну же!",
    "Чистые тарелки устроили вечеринку в посудомойке — пора их разогнать.",
    "Не забудь разобрать посудомойку, иначе завтра некуда будет класть грязное.",
    "Посудомойка ждёт разгрузки — всё помыто, высушено и нетерпеливо дребезжит.",
  ]

  PHRASES_READY_TO_WASH = [
    "Посудомойка скучает без работы — пора её запустить.",
    "Гора посуды накопилась, посудомойка просит смелости нажать пуск.",
    "Тарелки в посудомойке собрались на митинг — жми старт и отпусти их мыться.",
    "Посудомойка готова к бою, осталось только нажать кнопку.",
    "Хватит кормить посудомойку тарелками — пора включить и отдохнуть.",
    "Посудомойка смотрит на тебя с надеждой — запускай программу.",
    "Грязная посуда накопилась как снежный ком — время пустить посудомойку в ход.",
    "Твои тарелки ждут водных процедур — включай посудомойку!",
    "Посудомойка обидится, если её ещё раз оставят без дела — жми пуск.",
    "Посуда застряла в посудомойке без мытья — самое время нажать старт и уйти пить чай.",
  ]

  STATE_PHRASES = {
    "Washed": PHRASES_WASHED,
    "Ready to wash": PHRASES_READY_TO_WASH,
  }

  def initialize(self):
    if 'state_extended' not in self.args or 'motion_sensors' not in self.args or 'alice' not in self.args:
      self.log("Please define state_extended, motion_sensors and alice")
      return

    self.cooldown = self.args.get('cooldown', 1800)
    self.last_announced = {}

    for sensor in self.args['motion_sensors']:
      self.listen_state(self.motion_detected, sensor)

  def motion_detected(self, entity, attribute, old, new, kwargs):
    if new != "on" or old == "on":
      return

    # if 'constraint' in self.args and not self.constrain_input_boolean(self.args['constraint']):
    #   self.log('disabled by constraint')
    #   return

    state = self.get_state(self.args['state_extended'])
    phrases = self.STATE_PHRASES.get(state)
    if phrases is None:
      return

    last = self.last_announced.get(state)
    if last is not None:
      elapsed = (self.datetime() - last).total_seconds()
      if elapsed < self.cooldown:
        self.log('cooldown active for {}, skipping'.format(state))
        return

    self.say(random.choice(phrases))
    self.last_announced[state] = self.datetime()

  def say(self, command):
    self.log('command = {}'.format(command))
    self.call_service('media_player/play_media', entity_id=self.args['alice'], media_content_type='text', media_content_id=command)
