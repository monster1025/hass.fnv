import importlib
import subprocess
from typing import Any, Tuple, Union

#
# Global module
# contain global functions
#
# Args:
#
# None
#
# Release Notes
#
# Version 1.0:
#   Initial Version

"""Define various constants."""
CONF_PEOPLE = 'people'

def most_common(the_list: list) -> Any:
    """Return the most common element in a list."""
    return max(set(the_list), key=the_list.count)

def check_properties(self, args):
  missing = []
  for arg in args:
    if arg not in self.properties:
       missing.append(arg)
  if len(missing) > 0:
    self.error("Please provide {} in properties!".format(missing))
    return False
  return True

def check_args(self, args):
  missing = []
  for arg in args:
    if arg not in self.args:
       missing.append(arg)
  if len(missing) > 0:
    self.error("Please provide {} in config!".format(missing))
    return False
  return True

def check_constaint(self, name='constraint'):
  self.log('checking constaint: {}'.format(name))
  if name not in self.args:
  	self.log('script is not constrained')
  	return True;
  constaint_input = self.args[name]
  constaint_state = self.get_state(constaint_input)

def get_group_entities(self, group):
    attributes = self.get_state(group, attribute = "all")
    if (attributes == None):
      self.log('Warning: Possible invalid group: {}'.format(group))
      return []
    if 'attributes' in attributes:
      attributes = attributes['attributes']

    #group
    if "entity_id" in attributes:
      return attributes["entity_id"]

    #simple item
    return [group]

def turn_on(self, entity_id, state):
  if entity_id.startswith("light"):
    self.call_service("light/turn_off", entity_id = entity_id, transition = 1, brightness = 255)
  else:
    self.turn_off(entity_id, state)

def turn_off(self, entity_id, state):
  if entity_id.startswith("light"):
    self.call_service("light/turn_off", entity_id = entity_id, transition = 1)
  else:
    self.turn_off(entity_id, state)

def notification(self, to, message):
  self.notify(message, name = "telegram")
  

def get_arg(args, key):
    key = args[key]
    return key


def get_arg_list(args, key):
    arg_list = []
    if isinstance(args[key], list):
        arg = args[key]
    else:
        arg = (args[key]).split(",")
    for key in arg:
        arg_list.append(key)
    return arg_list