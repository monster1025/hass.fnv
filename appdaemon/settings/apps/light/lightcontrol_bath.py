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

class LightControlBath(hass.Hass):
  timer = None
  door_state_changed = None
  def initialize(self):
    if "sensor" not in self.args or 'door_sensor' not in self.args or "timeout" not in self.args or "control_entity" not in self.args:
      self.error("Please provide sensor, door_sensor, control_entity and timeout in config!")
      return
    self.listen_state(self.sensor_trigger, self.args['sensor'])
    self.listen_state(self.door_sensor_trigger, self.args['door_sensor'])

  def sensor_trigger(self, entity, attribute, old, new, kwargs):
    #sensor is off
    if new == 'off' and old == 'on':
      self.log('door_state_changed:{}'.format(self.door_state_changed))
      if self.door_state_changed == False:
        return
      self.log('Sensor is off - running timer for {}s.'.format(self.args['timeout']))
      self.run_timer()
    #sensor is on

    if new == 'on' and old == 'off':
      #turnin on control entity and wait while sensor will be off, than run timer.
      self.control_entity_on()
      self.stop_timer()
      door_state = self.get_state(self.args['door_sensor'])
      if door_state == "off":
        self.door_state_changed = False
      else :
        self.door_state_changed = None


  def door_sensor_trigger(self, entity, attribute, old, new, kwargs):
    #door is open
    sensor_state = self.get_state(self.args['sensor'])
    if new == 'on' and old == 'off' and sensor_state == 'off':
      self.log('door is opened now, runnig the timer')
      if self.timer == None:
        self.run_timer()
    if self.door_state_changed == False:
      self.door_state_changed = True
      self.log('door_state_changed:{}'.format(self.door_state_changed))

############ TIMER ########################  
  def control_entity_on(self):
    #if 'constraint' is off - we dont need to do anything
    if 'constraint' in self.args and not self.constrain_input_boolean(self.args['constraint']):
      return
    entity = self.args['control_entity']
    if not self.time_is_between(self.datetime(), '07:00:00', '23:00:00') and 'control_night_entity' in self.args:
      entity=self.args['control_night_entity'] #day mode

    if self.get_state(entity) == 'off':
      self.turn_on(entity)
      self.log("Light on.")
    if 'control_mini_light_entity' in self.args:
      self.turn_on(self.args['control_mini_light_entity'])

  def control_entity_off(self, kwargs):
    #if 'constraint' is off - we dont need to do anything
    if 'constraint' in self.args and not self.constrain_input_boolean(self.args['constraint']):
      return
    if self.door_state_changed == False:
      self.log('Motion is detected inside and door is still closed - dont turn off the light')
      return

    entity = self.args['control_entity']
    if not self.time_is_between(self.datetime(), '07:00:00', '23:00:00') and 'control_night_entity' in self.args:
      entity=self.args['control_night_entity'] #day mode

    if self.get_state(entity) == 'on':
      self.turn_off(entity)
      self.log("Light off.")
    if 'control_mini_light_entity' in self.args:
      self.turn_off(self.args['control_mini_light_entity'])
    self.stop_timer()

  def run_timer(self):
    if self.timer != None:
      self.stop_timer()
    self.timer = self.run_in(self.control_entity_off, self.args['timeout'])

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