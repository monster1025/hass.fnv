import appdaemon.plugins.hass.hassapi as hass
import globals
import datetime
from datetime import timedelta
#
# POwer theory
# Power theory tariff switch
#
# Args:
#
# None
#
# Release Notes
#
# Version 1.0:
#   Initial Version

class PowerTheory(hass.Hass):
  def initialize(self):
    self.run_daily(self.timer_tick, self.parse_time("07:00:00"))
    self.run_daily(self.timer_tick, self.parse_time("10:00:00"))
    self.run_daily(self.timer_tick, self.parse_time("17:00:00"))
    self.run_daily(self.timer_tick, self.parse_time("21:00:00"))
    self.run_daily(self.timer_tick, self.parse_time("23:00:00"))
    self.timer_tick(None)

  def timer_tick(self, kwargs):
    t1 = self.time_is_between(self.datetime(), '07:00:00', '09:59:59') or self.time_is_between(self.datetime(), '17:00:00', '20:59:59')
    t2 = self.time_is_between(self.datetime(), '23:00:00', '06:59:00')
    t3 = self.time_is_between(self.datetime(), '10:00:00', '16:59:59') or self.time_is_between(self.datetime(), '21:00:00', '22:59:59')
    if t1:
      self.switch_to_tariff('t1')
    if t2:
      self.switch_to_tariff('t2')
    if t3:
      self.switch_to_tariff('t3')

  def switch_to_tariff(self, tariff):
    self.log('switching to power tariff: {}'.format(tariff))
    self.call_service("select/select_option", entity_id='select.power_theory', option=tariff)
    

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