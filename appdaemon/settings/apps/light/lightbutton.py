import appdaemon.plugins.hass.hassapi as hass
import globals
import datetime

class LightButton(hass.Hass):
  isLocked = False

  def initialize(self):
    if not globals.check_args(self,['entities', 'sensor']):
      return

    self.listen_event_handle_list = []
    self.listen_event_handle_list.append(self.listen_event(self.event_detected, "xiaomi_aqara.click"))
    self.listen_event_handle_list.append(self.listen_state(self.state_change, self.args['sensor'])) #, attribute='action'

  def state_change(self, entity, attribute, old, new, kwargs):
    if new == "single":
      self.log('button_click')
      self.make_action_by_mode("off")
    if new == "double":
      self.log('button_dblclick')
      self.make_action_by_mode("on")
    
  def event_detected(self, event_name, data, kwargs):
    if data["entity_id"] != self.args["sensor"] or self.isLocked:
      return
    self.isLocked = True
    if data["click_type"] == "single":
      self.log('button_click')
      self.make_action_by_mode("off")
    if data["click_type"] == "double":
      self.log('button_dblclick')
      self.make_action_by_mode("on")      
    
    self.run_in(self.clear_lock, 1)

  def clear_lock(self, kwargs):
    self.isLocked = False

  def make_action_by_mode(self, state):
    states = self.fill_states()
    control_entity = self.args.get('control_input', None)
    if (control_entity != None):
      entity_id = next(iter(states))
      state = self.get_state(entity_id)
      self.set_state(entity_id, self.invert_state(state))
      self.set_state(control_entity, state)
      return

    if len(self.args["entities"]) > 1:
      self.toggle_next_with_state(state, states)

  def toggle_next_with_state(self, state, states):
    for entity_id in states:
      entity_state = states[entity_id]
      if (entity_state == state):
        self.set_state(entity_id, self.invert_state(state))
        self.log('toggling {}'.format(entity_id))
        return

    for entity_id in states:
        self.log('toggling {}'.format(entity_id))
        self.toggle(entity_id)

  def set_state(self, entity_id, state):
    if (state == "off"):
      self.log('turn_off {}'.format(entity_id))
      self.set_off(entity_id)
    if (state == "on"):
      self.log('turn_on {}'.format(entity_id))
      self.set_on(entity_id)

  #light
  def set_on(self, entity_id):
    brightness = 1 #night mode
    if self.time_is_between(self.datetime(), '07:00:00', '23:00:00'):
      brightness=255 #day mode

    if entity_id.startswith("light") and 'color' in entity_id:
      self.call_service("homeassistant/turn_on", entity_id = entity_id, transition = 1, brightness = brightness, color_temp=204)
    elif entity_id.startswith("light"):
      self.call_service("homeassistant/turn_on", entity_id = entity_id, transition = 1, brightness = brightness)
    else:
      self.turn_on(entity_id)
  
  def set_off(self, entity_id):
    if entity_id.startswith("light"):
      self.call_service("homeassistant/turn_off", entity_id = entity_id, transition = 1)
    else:
      self.turn_off(entity_id)


  def invert_state(self, state):
    if (state == "off"):
      return "on"
    return "off"

  def fill_states(self):
    states = {}
    for entity_id in self.split_device_list(self.args["entities"]):
      state = self.get_state(entity_id)
      if (state == None):
        self.log("Warning! Device {} not found (state: {}).".format(entity_id, state))
        continue
      states[entity_id] = state
    return states

  def terminate(self):
    if self.listen_event_handle_list != None:
      for listen_event_handle in self.listen_event_handle_list:
        self.cancel_listen_event(listen_event_handle)

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