import appdaemon.plugins.hass.hassapi as hass
import datetime

#
# Water control application.
# Controls water valve when all leave and no water needed devices is working.
# 
# Args:
# water_valve = water valve entity
# notify - notify entity to send message
# constraint (optional) = input_boolean to enable\disable this automation
# 
# Release Notes
#
# Version 1.0:
#   Initial Version

class WaterValveControl(hass.Hass):
  standby_power_limit = 15
  current_wait_cycle = 0
  wait_cycles = 2
  timer = None
  listen_event_handle_list = []
  timers = []

  def initialize(self):
    if 'water_valve' not in self.args or 'water_devices' not in self.args or 'notify' not in self.args:
      self.error("Please provide water_valve, water_devices and notify in config!")
      return

    self.listen_event_handle_list.append(self.listen_event(self.away_mode, "away_mode"))
    self.listen_event_handle_list.append(self.listen_event(self.return_home_mode, "return_home_mode"))
    self.log(self.get_turned_on_devices())

  def return_home_mode(self, event_id, event_args, kwargs):
    self.timer = None
    if 'constraint' in self.args and not self.constrain_input_boolean(self.args['constraint']):
      return
    self.turn_on(self.args['water_valve'])
    for device in self.args['water_devices']:
      self.turn_on(device)
    self.cancel_current_timer()

  def away_mode(self, event_id, event_args, kwargs):
    self.timer = None
    if 'constraint' in self.args and not self.constrain_input_boolean(self.args['constraint']):
      return
    powered_on = self.get_turned_on_devices()
    self.log('away entities: {}'.format(powered_on))
    if (len(powered_on) > 0):
      device_names = ""
      for device in powered_on:
        if device_names != '':
          device_names += ", "
        name = self.friendly_name(device)
        if name is None:
          name = device
        device_names += name
      self.notify('В доме остались требующие воды устройства ({}), подача воды не будет отключена.'.format(device_names), name = self.args['notify'])
      self.cancel_current_timer()
      self.timers.append(self.run_every(self.wait_when_device_is_done, self.datetime()+datetime.timedelta(seconds=5), 5*60))
    else:
      self.notify('Отключаю подачу воды.', name = self.args['notify'])
      self.turn_off(self.args['water_valve'])
      # for device in self.args['water_devices']:
      #   self.turn_off(device)

  def wait_when_device_is_done(self, kwargs):
    if 'constraint' in self.args and not self.constrain_input_boolean(self.args['constraint']):
      return
    powered_on = self.get_turned_on_devices()
    self.log('still powered on: {}'.format(powered_on))
    if len(powered_on) == 1:
      self.current_wait_cycle = 0
    elif len(powered_on) == 0 and self.current_wait_cycle<self.wait_cycles:
      self.log("Current wait cycle: {}".format(self.current_wait_cycle))
      self.current_wait_cycle = self.current_wait_cycle+1
    elif len(powered_on) == 0 and self.current_wait_cycle>=self.wait_cycles:
      self.current_wait_cycle = 0
      self.notify('Устройства требующие воды закончили свою работу, отключаю подачу воды.', name = self.args['notify'])
      self.turn_off_water_devices()
      self.cancel_current_timer()

  def turn_off_water_devices(self):
    self.log("Turning off water devices.")
    self.turn_off(self.args['water_valve'])
    for device in self.args['water_devices']:
      if 'switch' in device:
        self.log('switching off: {}'.format(device))
        self.turn_off(device)

  def get_turned_on_devices(self):
    powered_on_devices = []
    devices = self.args['water_devices']
    for device in devices:
      state = self.get_state(device)
      self.log('{} state: {}'.format(device, state))
      if state == 'off' or state == None:
        continue
      powered_on_devices.append(device)
    return powered_on_devices

  def cancel_current_timer(self):
    for timer in self.timers:
      self.log('canceling timer')
      self.cancel_timer(timer)
    self.timers = []
