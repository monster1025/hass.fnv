import appdaemon.plugins.hass.hassapi as hass
import globals
import datetime

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
# after_sundown (optionally) - whether to only trigger after sundown. example: True
# Release Notes
#
# Version 1.0:
#   Initial Version

class LightControl(hass.Hass):
  timer = None
  def initialize(self):
    if not globals.check_args(self, ["sensor", "timeout", "control_entity"]):
      return
    self.listen_event_handle_list = []
    self.listen_event_handle_list.append(self.listen_state(self.sensor_trigger, self.args['sensor']))

  def sensor_trigger(self, entity, attribute, old, new, kwargs):
    if 'constraint' in self.args and not self.constrain_input_boolean(self.args['constraint']):
      return
    if 'after_sundown' in self.args and self.args['after_sundown'] and not self.sun_down():
      # self.log('Sun is up, and we will turn it only after sundown.')
      return

    vacuum_state = "docked"
    ha_panel_state = ""
    if "vacuum" in self.args:
        vacuum_state = self.get_state(self.args["vacuum"])
    if "ha_panel" in self.args:
    	ha_panel_state = self.get_state(self.args["ha_panel"])
    #Если работает пылесос и сработал датчик движения
    if ha_panel_state == "armed_away" and vacuum_state == 'cleaning':
      self.log('Motion sensor is triggered, but vacuum is cleaning.')
      return

    #sensor is off
    if new == 'off' and old == 'on':
      self.log('Sensor is off - running timer for {}s.'.format(self.args['timeout']))
      self.run_timer()
    #sensor is on
    if new == 'on' and old == 'off':
      #turnin on control entity and wait while sensor will be off, than run timer.
      self.control_entity_on()
      self.stop_timer()


  def terminate(self):
    if self.listen_event_handle_list != None:
      for listen_event_handle in self.listen_event_handle_list:
        self.cancel_listen_event(listen_event_handle)

############ TIMER ########################
  def run_timer(self):
    if self.timer != None:
      self.stop_timer()
    self.timer = self.run_in(self.control_entity_off, self.args['timeout'])
  
  def control_entity_on(self):
    #if 'constraint' is off - we dont need to do anything
    if 'constraint' in self.args and not self.constrain_input_boolean(self.args['constraint']):
      return
    entity = self.args['control_entity']
    if not self.time_is_between(self.datetime(), '07:00:00', '23:00:00') and 'control_night_entity' in self.args:
      entity=self.args['control_night_entity'] #day mode

    if self.get_state(entity) == 'off':
      self.turn_on(entity)
      self.log("Light on ({}).".format(entity))

  def control_entity_off(self, kwargs):
    #if 'constraint' is off - we dont need to do anything
    if 'constraint' in self.args and not self.constrain_input_boolean(self.args['constraint']):
      return
    entity = self.args['control_entity']
    if not self.time_is_between(self.datetime(), '07:00:00', '23:00:00') and 'control_night_entity' in self.args:
      entity=self.args['control_night_entity'] #day mode

    if self.get_state(entity) == 'on':
      self.turn_off(entity)
      self.log("Light off.")
    self.stop_timer()

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