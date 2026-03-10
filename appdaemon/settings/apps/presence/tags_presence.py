import appdaemon.plugins.hass.hassapi as hass

#
# Tags counter
# This app count 'at home' BLE tags and set home presence state.
# tag names must start from 'tag_'. Room presence sensors will be generated. 
# 
# Args:
# tag_prefix = tag prefix to search (in my case 'sensor.tag_')
# sensor_prefix = sensor prefix for room presence sensor (ex: if prefix 'sensor.presence_', than sensor name will be 'sensor.presence_hall')
# rooms = rooms list, where tags will be discovered (sensor will be created for each room)
# constraint_prefix (input_boolean) = constraint for tag  (ex: input_boolean.tag_monster)
# 
# Release Notes
#
# Version 1.0:
#   Initial Version
class TagsPresence(hass.Hass):
  tags = []
  constraint_list = []
  tag_by_room_cache = {}
  def initialize(self):
    if 'tag_prefix' not in self.args or 'sensor_prefix' not in self.args or 'rooms' not in self.args or 'constraint_prefix' not in self.args:
      self.error("Please provide tag_prefix, sensor_prefix, constraint_prefix and rooms in config!")
      return
    self.listen_tags()
    # self.listen_event(self.ha_event, "plugin_started")
    self.refresh_presence_state()

  # def ha_event(self, event_name, data, kwargs):
  #   self.run_in(self.refresh_presence_state_timer, 10)

  def refresh_presence_state_timer(self, kwargs):
    self.refresh_presence_state()

  def sensor_trigger(self, entity, attribute, old, new, kwargs):
    self.refresh_presence_state()

  def constraint_trigger(self, entity, attribute, old, new, kwargs):
    self.refresh_presence_state()

  def listen_tags(self):
    self.fill_tags_and_constraints()
    for tag in self.tags:
      self.listen_state(self.sensor_trigger, tag)
    for constraint in self.constraint_list:
      self.listen_state(self.constraint_trigger, constraint)

  def refresh_presence_state(self):
    tags_by_room = self.get_tags_state_by_room(self.tags, self.constraint_list)
    tags_by_person = self.get_tags_state_by_person(self.tags, self.constraint_list)
    homePresence = 'off'
    for room in self.args['rooms']:
      sensor = '{}{}'.format(self.args['sensor_prefix'],room)
      if room in tags_by_room and len(tags_by_room[room]) > 0:
        self.create_sensor(sensor, 'on')
        homePresence = 'on'
      else:
        self.create_sensor(sensor, 'off')
    
    for person in tags_by_person:
      if len(tags_by_person[person])>0 and tags_by_person[person] != 'not home':
        attr = self.get_state(person, attribute='all').get('attributes', None)
        # self.log(attr)
        # attr['state'] = tags_by_person[person][0]

        # disable set person state
        # self.set_state(person, state = tags_by_person[person][0], attributes = attr)

    homeSensor = '{}{}'.format(self.args['sensor_prefix'],'home')
    self.create_sensor(homeSensor, homePresence)

  def get_tags_state_by_room(self, tags, constraint_list):
    tags_by_room = {}
    for tag in tags:
      constraint = '{}{}'.format(self.args['constraint_prefix'],tag.replace(self.args['tag_prefix'],''))
      if constraint in constraint_list and not self.constrain_input_boolean(constraint):
        continue
      room = self.get_state(tag)
      if room not in tags_by_room:
          tags_by_room[room] = []
      tags_by_room[room].append(tag)
    return tags_by_room          

  def get_tags_state_by_person(self, tags, constraint_list):
    tags_by_person = {}
    for tag in tags:
      constraint = '{}{}'.format(self.args['constraint_prefix'],tag.replace(self.args['tag_prefix'],''))
      if constraint in constraint_list and not self.constrain_input_boolean(constraint):
        continue
      tagName = tag.replace(self.args['tag_prefix'],'')
      if '_' in tagName:
        tagName = tagName.split('_')[0]
      person = '{}{}'.format(self.args['person_prefix'], tagName)
      person_state = self.get_state(person)
      if person_state != None:
        # self.log('{}: {}'.format(person, person_state))
        if person not in tags_by_person:
            tags_by_person[person] = []
        tags_by_person[person].append(self.get_state(tag))
    return tags_by_person  

      # if person_state in self.get_state('person'):
      #   self.log('{} found'.format(person))
      # else:
      #   self.log('{} not found'.format(person))

      # self.log('{}: {}'.format(person, person_state))
    #   tag_state = self.get_state(tag)
    #   if room not in tags_by_room:
    #       tags_by_room[room] = []
    #   tags_by_room[room].append(tag)
    # return tags_by_room   

  def fill_tags_and_constraints(self):
    self.tags = []
    self.constraint_list = []
    devices = self.get_state()
    for tag in devices:
      if not tag.startswith(self.args['tag_prefix']):
        continue
      self.tags.append(tag)

      constraint = '{}{}'.format(self.args['constraint_prefix'],tag.replace(self.args['tag_prefix'],''))
      if constraint in devices and constraint not in self.constraint_list:
        self.constraint_list.append(constraint)

  def create_sensor(self, entity_id, state, attributes = None):
    current_state = self.get_state(entity_id)
    if (current_state == state):
      return
    # self.log('Updating {} state ({}->{})'.format(entity_id, current_state, state))
    if attributes == None:
      attributes = {}
    attributes['description'] = 'Created and updated from appdaemon (tags_presence)'
    self.set_state(entity_id, state = state, attributes = attributes)