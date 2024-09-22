import appdaemon.plugins.hass.hassapi as hass
import globals
import datetime
import time

#
# This app will use motion sensors to turn on and off control_entity for 'timeout' time.
# It work with xiaomi motion sensors.
# main algorithm: when sensor turns on - turn on the light; when sensor is off - set timer for 'timeout'; 
# if sensor goes on - turn off the timer; when timer was hit - turn off the light.
#
# Args:
#
# sensor = motion sensor to use (will work with other sensor types too)
# timeout = timeout after sensor will turned off (keep in mind that xiaomi motion sensor has own timeout!)
# control_entity = entity, that will be controlled (example: group of light bulbs)
# constraint = you can define constraint (input_boolean), that will turn on and off this app.
#
# Release Notes
#
# Version 1.0:
#   Initial Version

class LightControlKitchenset(hass.Hass):
  timer = None
  def initialize(self):
    if "sensors" not in self.args or "timeout" not in self.args or "control_entity" not in self.args:
      self.error("Please provide sensor, control_entity and timeout in config!")
      return
    for sensor in self.args['sensors']:
      self.listen_state(self.sensor_trigger, sensor)
    if 'night_sensors' in self.args:
      for sensor in self.args['night_sensors']:
        self.listen_state(self.sensor_night_trigger, sensor)

  def sensor_trigger(self, entity, attribute, old, new, kwargs):
    #sensor is on
    if new == 'on' and old == 'off':
      #turnin on control entity and wait while sensor will be off, than run timer.
      self.log('motion detected: {}'.format(entity))
      self.control_entity_on()
      self.stop_timer()

    #sensor is off
    if new == 'off' and old == 'on':
      self.log('motion stop detected:{}'.format(entity))
      state = self.get_motion_state()
      if state == 'off':
        self.run_timer()

  def sensor_night_trigger(self, entity, attribute, old, new, kwargs):
    if new == 'on' and old == 'off':
      if self.is_night():
        self.log('night motion detected: {}'.format(entity))
        self.control_entity_on()
        self.stop_timer()

    if new == 'off' and old == 'on':
      self.log('night motion stop detected:{}'.format(entity))
      state = self.get_motion_state()
      if state == 'off':
        self.run_timer()

############ SENSOR GROUP ########################  
  def get_motion_state(self):
    sensors = self.args['sensors']
    night_sensors = []
    if 'night_sensors' in self.args and self.is_night():
      night_sensors = self.args['night_sensors']
    all_sensors = sensors + night_sensors
    
    self.log('all sensors: {}'.format(all_sensors))
    for sensor in all_sensors:
      state =  self.get_state(sensor)
      if state == 'on':
        return 'on'
    return 'off'

  def is_night(self):
    return not self.time_is_between(self.datetime(), '07:00:00', '23:00:00')

############ TIMER ########################  
  def control_entity_on(self):
    #if 'constraint' is off - we dont need to do anything
    if 'constraint' in self.args and not self.constrain_input_boolean(self.args['constraint']):
      return
    entity = self.args['control_entity']
    if self.get_state(entity) == 'off':
      self.turn_on(entity)
      self.log("Light on.")

  def control_entity_off(self, kwargs):
    #if 'constraint' is off - we dont need to do anything
    if 'constraint' in self.args and not self.constrain_input_boolean(self.args['constraint']):
      return

    entity = self.args['control_entity']

    if self.get_state(entity) == 'on':
      self.turn_off(entity)
      self.log("Light off.")
    self.stop_timer()

  def run_timer(self):
    if self.timer != None:
      self.stop_timer()

    timeout = self.args['timeout']
    if 'night_timeout' in self.args and self.is_night():
      timeout = self.args['night_timeout']
    self.log('Sensor is off - running timer for {}s'.format(timeout))
    self.timer = self.run_in(self.control_entity_off, timeout)

  def stop_timer(self):
    if (self.timer == None):
      return
    self.log('stopping timer.')
    self.cancel_timer(self.timer)
    self.timer = None

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