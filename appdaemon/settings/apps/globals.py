import importlib
import subprocess
from typing import Any, Tuple, Union

"""Define various constants."""
CONF_PEOPLE = 'people'

# --- Telegram notifications -------------------------------------------------
#
# HA 2026.2 deprecated the per-platform notify.telegram* services in favour
# of entity-based targeting (see repairs.issue_registry: telegram/migrate_notify).
# The generic notify.send_message service only supports message/title, so it
# can't carry parse_mode/photo/keyboard payloads our apps rely on - instead we
# target the telegram_bot integration's own (non-deprecated) domain services
# (telegram_bot.send_message / telegram_bot.send_photo) with entity_id, which
# is the current 1:1 replacement for the old chat_id-based notify.telegram*.
#
# Entity ids come from .storage/core.entity_registry (platform: telegram_bot),
# mapped from the friendly names ('telegram', 'telegram_monster',
# 'telegram_sveta') used throughout apps.yaml configs.
TELEGRAM_TARGETS = {
    'telegram': 'notify.home_assistant_fonvizina_fonvizina_18_1001567589226',
    'telegram_monster': 'notify.home_assistant_fonvizina_monster_123622180',
    'telegram_sveta': 'notify.home_assistant_fonvizina_svetlana_205225134',
}

def send_telegram(self, message, target='telegram', parse_mode='html', **kwargs):
    """Send a Telegram text message via telegram_bot.send_message.

    Replacement for the deprecated `self.notify(message, name=target)`.
    `target` is a friendly name from TELEGRAM_TARGETS (falls back to the
    default group chat if unknown). Extra kwargs (title, keyboard, etc.) are
    passed straight through to the service call.
    """
    entity_id = TELEGRAM_TARGETS.get(target, TELEGRAM_TARGETS['telegram'])
    service_data = {'entity_id': entity_id, 'message': message}
    if parse_mode:
        service_data['parse_mode'] = parse_mode
    service_data.update(kwargs)
    self.call_service('telegram_bot/send_message', **service_data)

def send_telegram_photo(self, url, target='telegram', caption=None, parse_mode='html', **kwargs):
    """Send a photo via telegram_bot.send_photo.

    Replacement for the deprecated `self.notify(msg, name=target,
    data={'photo': {'url': url}})`.
    """
    entity_id = TELEGRAM_TARGETS.get(target, TELEGRAM_TARGETS['telegram'])
    service_data = {'entity_id': entity_id, 'url': url}
    if caption:
        service_data['caption'] = caption
    if parse_mode:
        service_data['parse_mode'] = parse_mode
    service_data.update(kwargs)
    self.call_service('telegram_bot/send_photo', **service_data)
# -----------------------------------------------------------------------------

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
    if "entity_id" in attributes:
      return attributes["entity_id"]
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
  send_telegram(self, message, target = "telegram")

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
