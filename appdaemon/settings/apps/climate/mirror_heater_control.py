import hassapi as hass
import datetime
import adbase as ad


#
#  entity: sensor.temperature_bath_humidity
#  control_entity: switch.switch_mirror_bath_heater
#  constraint: input_boolean.bath_mirror_heat
#  threshold: 75


class MirrorHeater(hass.Hass):
  timer = None
  entity = None
  threshold = 75
  blocked = False

  def initialize(self):
    self.log('starting initialize')

    sensor = self.args['entity']
    self.log('listen [{0}] state'.format(sensor))
    self.listen_state(self.humidity_changed, sensor, duration=10)

    if 'threshold' in self.args:
      self.threshold = self.args['threshold']
      self.log('setting threshold to: {}'.format(self.threshold))

  def humidity_changed(self, entity, attribute, old_state, new_state, kwargs):
    if 'constraint' in self.args and not self.constrain_input_boolean(self.args['constraint']):
      return

    self.log('[{0}] [humidity changed] : {1}, isnumeric: {2}, type: {3}'.format(entity, new_state, new_state.isnumeric(), type(new_state)))
    if float(new_state) > self.threshold:
      self.log('Control Entity On and running timer...')
      self.control_entity_on()
      self.run_timer()
    else:
      self.log('Control Entity Off and stopping timer...')
      self.control_entity_off(None)

############ TIMER ########################
  def run_timer(self):
    if self.timer != None:
      self.stop_timer()
    self.timer = self.run_in(self.control_entity_off, self.args['timeout'])
  
  def control_entity_on(self):
    if 'constraint' in self.args and not self.constrain_input_boolean(self.args['constraint']):
      return
    for entity in self.args['control_entities']:
      state = self.get_state(entity)
      if state == 'off':
        self.turn_on(entity)
        self.log("Turn on ({}).".format(entity))

  def control_entity_off(self, kwargs):
    if 'constraint' in self.args and not self.constrain_input_boolean(self.args['constraint']):
      return
    for entity in self.args['control_entities']:
      state = self.get_state(entity)
      if state == 'on':
        self.turn_off(entity)
        self.log("Turn off ({}).".format(entity))
    self.stop_timer()

  def stop_timer(self):
    if (self.timer == None):
      return
    self.log('stopping timer.')
    self.cancel_timer(self.timer)
    self.timer = None