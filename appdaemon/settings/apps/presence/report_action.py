import appdaemon.plugins.hass.hassapi as hass
import globals

#
# Home and away report
# Send report about home state after presence_actions was done.
# 
# Args:
# entity - group of entities to send state report
# notify - notify entity to send message
# 
# Release Notes
#
# Version 1.0:
#   Initial Version

class ReportByPresence(hass.Hass):
  report_delay = 15
  def initialize(self):
    if 'entity' not in self.args or 'notify' not in self.args:
      self.error("Please provide entity and notify in config!")
      return
    self.listen_event(self.away_mode, "away_mode")
    self.listen_event(self.return_home_mode, "return_home_mode")

  def away_mode(self, event_id, event_args, kwargs):
    if 'constraint' in self.args and not self.constrain_input_boolean(self.args['constraint']):
      return
    #wait 15 seconds before all devices will change thair states.
    self.run_in(self.send_report, self.report_delay)

  def return_home_mode(self, event_id, event_args, kwargs):
    if 'constraint' in self.args and not self.constrain_input_boolean(self.args['constraint']):
      return
    self.notify("Добро пожаловать домой!", name = self.args['notify'])

############# AWAY REPORT ##########################
  def send_report(self, kwargs):
    any = False
    message = ""
    entities = globals.get_group_entities(self, self.args['entity'])
    for entity in entities:
      state = self.get_state(entity)
      if state == "on":
        any = True
        message += '{} ({}) = {}\n'.format(self.friendly_name(entity), entity, self.get_state(entity))
    if any:
      message = "В доме остались работать следующие устройства:\n" + message
      self.notify(message, name = self.args['notify'])
    else:
      self.notify("Все устройства в доме выключены.", name = self.args['notify'])
