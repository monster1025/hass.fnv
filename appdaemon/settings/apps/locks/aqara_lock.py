import appdaemon.plugins.hass.hassapi as hass
import globals

#
# Aqara lock notifications
# Send notification to telegram of lock state
#
# Args:
# lock_state_entity - entity of aqara lock state
# notify - notify entity to send message
#
# Release Notes
#
# Version 1.0:
#   Initial Version

class AqaraLock(hass.Hass):
  def initialize(self):
    if 'lock_state_entity' not in self.args or 'notify' not in self.args:
      self.error("Please provide lock_state_entity and notify in config!")
      return

    lock_state_entity = self.args['lock_state_entity']

    self.log(' [+] listening for lock_state_entity sensor {}'.format(lock_state_entity))
    self.listen_state(self.sensor_trigger, lock_state_entity)

  def sensor_trigger(self, entity, attribute, old, new, kwargs):
    if 'constraint' in self.args and not self.constrain_input_boolean(self.args['constraint']):
     return

    #(old != "" and old != "unknown") or
    if new == "unknown" or new == "" or new == "unavailable":
      self.log('skiping event. {} changed from {} to {}'.format(entity, old, new))
      return
    self.log('{} changed from {} to {}'.format(entity, old, new))

    action = new
    self.process_event(action)

  def process_event(self, eventname):
    if eventname == "ring_bell":
      self.fire_event('doorbell_call')
    elif eventname == 'lock_opened_outside':
      self.log("Дверь открыта снаружи, событие: {}.".format(eventname))
    elif 'finger_open_' in eventname:
      self.fire_event('door_opened')
      self.log("Дверь открыта отпечатком пальца, событие: {}.".format(eventname))
      self.notify_tg("Дверь открыта отпечатком пальца, событие: {}.".format(eventname))
    else:
      self.log("Неизвестное событие замка: {}.".format(eventname))
      self.notify_tg("Неизвестное событие замка: {}".format(eventname))

  def notify_tg(self, msg):
    globals.send_telegram(self, msg, target = self.args['notify'])
