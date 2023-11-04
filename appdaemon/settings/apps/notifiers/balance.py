import datetime
from automation import Automation, Base  # type: ignore

#
# App to send email report for low balance
#
# Args:
#
# threshold = value below which battery levels are reported and email is sent
# always_send = set to 1 to override threshold and force send
#
# None
#
# Release Notes
#
# Version 1.0:
#   Initial Version

class Balance(Base):
  def initialize(self):
    super().initialize()
    self.check_balance({"force": 1})
    self.run_daily(self.check_balance, datetime.time(10, 0, 0))
    
  def check_balance(self, kwargs):
    if 'constraint' in self.args and not self.constrain_input_boolean(self.args['constraint']):
      return

    values = {}
    low = []
    for key in self.entity_ids:
      device = self.entity_ids[key]
      balance = self.get_state(device)
      if balance != None and self.is_number(balance):
        if float(balance) < self.args["threshold"]:
          low.append(device)
      values[device] = balance

    message=""
    name = "Алтуфьево"
    if 'name' in self.args:
    	name = self.args['name']
    if low:
      message += "Пожалуйста пополните баланс ({}): (< {}) \n".format(name, self.args["threshold"])
      for device in low:
        message += " - {}: {}\n".format(self.friendly_name(device), values[device])
      message += "\n\n"
          
    if low or ("always_send" in self.args and self.args["always_send"] == 1) or ("force" in kwargs and kwargs["force"] == 1):
      if message != "":
        self.notify(message, name = "telegram") #name = "telegram_monster"

  def is_number(self, s):
    try:
        float(s)
        return True
    except ValueError:
        return False