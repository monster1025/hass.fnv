import appdaemon.plugins.hass.hassapi as hass
import re
#
# This app will create groups in runtime by user defined params
# Based on Rene Tode groups plugin ( hass@reot.org )
#
# Args:
#  device_type: sensor # or any devicetype                                                
#  entity_part: "any_part"                                                                
#  entities: # list of entities                                                           
#    - sensor.any_entity                                                                  
#  hidden: False # or True                                                                
#  view: True # or False                                                                  
#  assumed_state: False # or True                                                         
#  friendly_name: Your Friendly Name                                                      
#  nested_view: True # or False 
#
# Release Notes
#
# Version 1.0:
#   Initial Version

class Groups(hass.Hass):
  def initialize(self):
    self.run_in(self.create_groups_timer, 10)

  def create_groups_timer(self, kwargs):
    entitylist = []

    expand_group = self.args.get("expand_group", False)
    device_type = self.args.get("device_type", None)
    all_entities = self.get_state(device_type)

    if "entities" in self.args:
      for entity in self.args["entities"]:
        found = False
        for real_entity in all_entities:
          if real_entity.lower() == entity.lower():
            self.append_entity(entitylist, entity, expand_group)
            found = True
        if not found:
          for real_entity in all_entities:
            if re.match(entity.lower(), real_entity.lower()):
              self.append_entity(entitylist, real_entity, expand_group)

    if 'entity_part' in self.args:
      for entity in all_entities:
        if self.args["entity_part"] in entity and entity.lower() not in entitylist:
          self.append_entity(entitylist, entity, expand_group)

    hidden = self.args.get("hidden", False)
    view = self.args.get("view", False)
    assumed_state = self.args.get("assumed_state",False)
    friendly_name = self.args.get("friendly_name","")
    name = "group." + self.name
    
    if self.args.get('orderby', None) == 'friendly_name':
      entitylist.sort(key=self.sortByFriendlyName)

    self.log("Creating group {} with entities: {}".format(name, entitylist))
    self.set_state(name,state="on",attributes={"view": view,"hidden": hidden,"assumed_state": assumed_state,"friendly_name": friendly_name,"entity_id": entitylist, 'description': 'Created and updated from appdaemon ({})'.format(__name__)})
  
  def sortByFriendlyName(self, entity):
    return self.get_state(entity, attribute='friendly_name')

  def append_entity(self, entitylist, entity, expand_group):
    entity = entity.lower()
    if (('group.' not in entity and expand_group) or not expand_group) and entity not in entitylist:
      entitylist.append(entity)
      return
    if expand_group and 'group.' in entity:
      group_entities = self.get_group_entities(entity)
      for group_entity in group_entities:
        if group_entity not in entitylist:
          entitylist.append(group_entity)

  def get_group_entities(self, group):
    group = self.get_state(group, attribute = "all")
    return group["attributes"]["entity_id"]