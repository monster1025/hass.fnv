import appdaemon.plugins.hass.hassapi as hass
import globals
import datetime

#
# Purifier controller
# Turn on and off purifier by light sensor and timers
#
# Args:
#
# None
#
# Release Notes
#
# Version 1.0:
#   Initial Version

class Purifier(hass.Hass):
  away_fan_speed = 8 #1-14
  listen_event_handle_list = []
  mode = 'auto'

  def initialize(self):
    if not globals.check_args(self, ["on_time", "off_time"]):
      return
    on_time = self.parse_time(self.args["on_time"])
    off_time = self.parse_time(self.args["off_time"])

    self.on_timer = self.run_daily(self.day_mode_timer_event, on_time)
    self.off_timer = self.run_daily(self.night_mode_timer_event, off_time)

    self.listen_event_handle_list.append(self.listen_event(self.away_mode_event, "away_mode"))
    self.listen_event_handle_list.append(self.listen_event(self.return_home_mode_event, "return_home_mode"))
    self.listen_event_handle_list.append(self.listen_state(self.state_change, self.args['entity'], attribute='illuminance'))

  def state_change(self, entity, attribute, old, new, kwargs):
    presence_state = self.get_state(self.args['ha_panel'])
    if presence_state != "disarmed":
      # self.log('Nobody home, ignoring illuminance changes.')
      return
    self.log("{} changed from {} to {}".format(attribute, old, new))
    if old > 0 and new == 0 and self.time_is_between(self.datetime(), self.args["on_time"], self.args["off_time"]):
      self.night_mode()
    elif old == 0 and new > 0 and self.time_is_between(self.datetime(), self.args["on_time"], self.args["off_time"]):
      self.auto_mode()
    #self.auto_mode()

  def return_home_mode_event(self, event_id, event_args, kwargs):
    self.auto_mode()

  def away_mode_event(self, event_id, event_args, kwargs):
    self.away_mode()

  def night_mode_timer_event(self, kwargs):
    self.night_mode()

  def day_mode_timer_event(self, kwargs):
    self.auto_mode()
  

  def away_mode(self):
    self.mode='away'
    self.log('Set purifier mode to favorite, speed: {}'.format(self.away_fan_speed))
    if 'entity' in self.args:
      self.call_service("fan/set_speed", entity_id = self.args['entity'], speed='favorite')
      self.call_service("fan/xiaomi_miio_set_favorite_level", entity_id = self.args['entity'], level=self.away_fan_speed)
      self.call_service("fan/xiaomi_miio_set_led_on", entity_id = self.args['entity'])
      # self.call_service("fan/xiaomi_miio_set_buzzer_on", entity_id = self.args['entity'])
 
  def auto_mode(self):
    self.mode='auto'
    self.log('Set purifier mode to auto.')
    if 'entity' in self.args:
      self.call_service("fan/set_speed", entity_id = self.args['entity'], speed='auto')
      self.call_service("fan/xiaomi_miio_set_led_on", entity_id = self.args['entity'])
      # self.call_service("fan/xiaomi_miio_set_buzzer_on", entity_id = self.args['entity'])

  def night_mode(self):
    self.mode='night'
    self.log('Set purifier mode to silent.')
    if 'entity' in self.args:
      self.call_service("fan/xiaomi_miio_set_buzzer_off", entity_id = self.args['entity'])     
      self.call_service("fan/set_speed", entity_id = self.args['entity'], speed='silent')
      self.call_service("fan/xiaomi_miio_set_led_off", entity_id = self.args['entity'])


  def time_is_between(
          hass, target_dt: datetime, start_time: str,
          end_time: str) -> bool:
      """Generalization of AppDaemon's now_is_between method."""
      start_time_dt = hass.parse_time(start_time)  # type: datetime
      end_time_dt = hass.parse_time(end_time)  # type: datetime
      start_dt = target_dt.replace(
          hour=start_time_dt.hour,
          minute=start_time_dt.minute,
          second=start_time_dt.second)
      end_dt = target_dt.replace(
          hour=end_time_dt.hour,
          minute=end_time_dt.minute,
          second=end_time_dt.second)

      if end_dt < start_dt:
          # Spans midnight
          if target_dt < start_dt and target_dt < end_dt:
              target_dt = target_dt + timedelta(days=1)
          end_dt = end_dt + timedelta(days=1)
      return start_dt <= target_dt <= end_dt