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

class BreaserControl(hass.Hass):
  away_fan_speed = 8 #1-14
  listen_event_handle_list = []
  mode = 'auto'
  heat_start_at = '23:00:00'
  heat_stop_at = '07:00:00'

  def initialize(self):
    if not globals.check_args(self, ["on_time", "off_time"]):
      return
    on_time = self.parse_time(self.args["on_time"])
    off_time = self.parse_time(self.args["off_time"])

    self.on_timer = self.run_daily(self.day_mode_timer_event, on_time)
    self.off_timer = self.run_daily(self.night_mode_timer_event, off_time)

    if 'heat_switch' in self.args:
      self.heat_on_timer = self.run_daily(self.heat_mode_on_timer_event, self.heat_start_at)
      self.heat_off_timer = self.run_daily(self.heat_mode_off_timer_event, self.heat_stop_at)
      self.heat_mode_by_time()

    self.listen_event_handle_list.append(self.listen_event(self.away_mode_event, "away_mode"))
    self.listen_event_handle_list.append(self.listen_event(self.return_home_mode_event, "return_home_mode"))
    if 'co2_sensor' in self.args:
      self.listen_event_handle_list.append(self.listen_state(self.state_change, self.args['co2_sensor']))

  def state_change(self, entity, attribute, old, new, kwargs):
    self.heat_mode_by_time()
    if 'constraint' in self.args and not self.constrain_input_boolean(self.args['constraint']):
      return

    presence_state = self.get_state(self.args['ha_panel'])
    if presence_state != "disarmed":
      self.log('Nobody home, ignoring co2 changes.')
      return
    if new == 'unknown':
      return
    self.log("{} changed from {} to {}".format(attribute, old, new))
    co2_level = int(new)
    #day
    if self.time_is_between(self.datetime(), self.args["on_time"], self.args["off_time"]):
      self.set_mode_by_co2(co2_level, False)
    #night
    elif not self.time_is_between(self.datetime(), self.args["on_time"], self.args["off_time"]):
      self.set_mode_by_co2(co2_level, True)

  def set_mode_by_co2(self, co2_level, is_night):
    self.heat_mode_by_time()
    
    # === Настраиваемые коэффициенты ===
    CFG = {
        'co2_auto_threshold': 600,      # Ниже этого значения — auto_mode
        'co2_min_control': 600,         # Начало плавного роста скорости
        'co2_max_control': 1000,        # Максимальная скорость достигается здесь
        'speed_min': 1,                 # Мин. скорость вентиляции
        'speed_max': 100,               # Макс. скорость вентиляции
        'night_speed_factor': 0.7,      # Коэффициент снижения скорости ночью
        'transition_smoothness': 0.3,   # Плавность перехода (0-1)
    }
    
    # === Плавная функция перехода от auto к ручной скорости ===
    def calculate_speed(co2, cfg, is_night):
        # Нормализация CO2 в диапазон [0, 1]
        t = (co2 - cfg['co2_min_control']) / (cfg['co2_max_control'] - cfg['co2_min_control'])
        t = max(0.0, min(1.0, t))
        
        # Плавная интерполяция (smoothstep для более мягкого старта)
        if cfg['transition_smoothness'] > 0:
            t = t * t * (3 - 2 * t)  # Cubic smoothstep
        
        # Базовая скорость
        base_speed = cfg['speed_min'] + t * (cfg['speed_max'] - cfg['speed_min'])
        
        # Ночной коэффициент
        day_factor = 1.0 if not is_night else cfg['night_speed_factor']
        final_speed = base_speed * day_factor
        
        return int(round(max(cfg['speed_min'], min(cfg['speed_max'], final_speed))))
    
    # === Автоматический режим при низком CO2 ===
    if co2_level <= CFG['co2_auto_threshold']:
        self.log('CO2 is excellent: {}. Set auto mode.'.format(co2_level))
        self.auto_mode()
        return
    
    # === Плавный расчёт скорости ===
    speed = calculate_speed(co2_level, CFG, is_night)
    
    period = 'Night' if is_night else 'Day'
    self.log('{}, CO2 is {}. Set speed to {}.'.format(
        period, co2_level, speed))
    
    self.set_speed(speed)

  def set_speed(self, speed):
    if 'constraint' in self.args and not self.constrain_input_boolean(self.args['constraint']):
      return
    self.log('Set purifier mode to favorite, speed: {}'.format(speed))
    self.call_service("fan/set_preset_mode", entity_id = self.args['entity'], preset_mode='Favorite')
    self.call_service("fan/set_percentage", entity_id = self.args['entity'], percentage=speed)

  def return_home_mode_event(self, event_id, event_args, kwargs):
    if 'constraint' in self.args and not self.constrain_input_boolean(self.args['constraint']):
      return
    self.auto_mode()

  def away_mode_event(self, event_id, event_args, kwargs):
    if 'constraint' in self.args and not self.constrain_input_boolean(self.args['constraint']):
      return
    self.turn_on(self.args['entity'])
    self.away_mode()

  def night_mode_timer_event(self, kwargs):
    if 'constraint' in self.args and not self.constrain_input_boolean(self.args['constraint']):
      return
    presence_state = self.get_state(self.args['ha_panel'])
    if presence_state != "disarmed":
      self.log('Nobody home, ignoring automations.')
      return
    self.night_mode()

  def day_mode_timer_event(self, kwargs):
    if 'constraint' in self.args and not self.constrain_input_boolean(self.args['constraint']):
      return
    presence_state = self.get_state(self.args['ha_panel'])
    if presence_state != "disarmed":
      self.log('Nobody home, ignoring automations.')
      return
    self.auto_mode()
  
  def away_mode(self):
    if 'constraint' in self.args and not self.constrain_input_boolean(self.args['constraint']):
      return
    self.mode='away'
    self.log('Set purifier mode to favorite, speed: {}'.format(self.away_fan_speed))
    if 'entity' in self.args:
      self.call_service("fan/set_preset_mode", entity_id = self.args['entity'], preset_mode='Favorite')
      self.call_service("fan/set_percentage", entity_id = self.args['entity'], percentage=100)
 
  def auto_mode(self):
    if 'constraint' in self.args and not self.constrain_input_boolean(self.args['constraint']):
      return
    self.mode='auto'
    self.log('Set purifier mode to auto.')
    if 'entity' in self.args:
      self.call_service("fan/set_preset_mode", entity_id = self.args['entity'], preset_mode='Auto')

  def night_mode(self):
    if 'constraint' in self.args and not self.constrain_input_boolean(self.args['constraint']):
      return
    self.mode='night'
    self.log('Set purifier mode to silent.')
    if 'entity' in self.args:
      self.call_service("fan/set_preset_mode", entity_id = self.args['entity'], preset_mode='Sleep')

  #heating control
  def heat_mode_by_time(self):
    if 'constraint' in self.args and not self.constrain_input_boolean(self.args['constraint_heat']):
      return
    if self.time_is_between(self.datetime(), self.heat_stop_at, self.heat_start_at):
      self.log('Expensive tariff. Set heat off.')
      self.heat_mode_off_timer_event(None)
    else:
      presence_state = self.get_state(self.args['ha_panel'])
      if presence_state != "disarmed":
        self.log('Nobody home, ignoring automations.')
        return
      self.log('Cheap tariff. Set heat on.')
      self.heat_mode_on_timer_event(None)

  def heat_mode_on_timer_event(self, kwargs):
    if 'constraint' in self.args and not self.constrain_input_boolean(self.args['constraint_heat']):
      return
    presence_state = self.get_state(self.args['ha_panel'])
    if presence_state != "disarmed":
      self.log('Nobody home, ignoring automations.')
      return
    self.turn_on(self.args['heat_switch'])

  def heat_mode_off_timer_event(self, kwargs):
    self.turn_off(self.args['heat_switch'])


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