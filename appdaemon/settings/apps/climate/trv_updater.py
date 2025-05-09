import hassapi as hass
import datetime
import adbase as ad


class TRVUpdater(hass.Hass):
    entities = []

    def initialize(self):
        self.log('starting initialize')
        self.entities = self.args['entities']

        for sensor in self.entities.keys():
            self.log('listen [{0}] state'.format(sensor))
            self.listen_state(self.temperature_changed, sensor, duration=10)
            current_temperature = self.get_state(sensor)
            self.temperature_changed(sensor, 'temperature', '20.0', current_temperature, None)

    def temperature_changed(self, entity, attribute, old_state, new_state, kwargs):
        self.log('[{0}] [temperature changed] : {1}, isnumeric: {2}, type: {3}'.format(entity, new_state, new_state.isnumeric(), type(new_state)))
        topic = self.entities[entity].get('topic_prefix', None)
        if topic is not None:
            sensor_topic = topic.replace('/sensor_temp', '')
            sensor_payload = '{"sensor":"external"}'
            self.log('[mqtt publish] topic: "{0}" value: {1}'.format(sensor_topic, sensor_payload))
            self.call_service("mqtt/publish", topic=sensor_topic, payload=sensor_payload)

            temperature_payload = '{"external_temperature_input":"' + new_state + '"}'
            self.log('[mqtt publish] topic: "{0}" value: {1}'.format(sensor_topic, temperature_payload))
            self.call_service("mqtt/publish", topic=sensor_topic, payload=temperature_payload)
        
        topics = self.entities[entity].get('topic_prefixes', None)
        if topics is not None:
            for topic in topics:
                sensor_topic = topic.replace('/sensor_temp', '')
                sensor_payload = '{"sensor":"external"}'
                self.log('[mqtt publish] topic: "{0}" value: {1}'.format(sensor_topic, sensor_payload))
                self.call_service("mqtt/publish", topic=sensor_topic, payload=sensor_payload)

                temperature_payload = '{"external_temperature_input":' + new_state + '}'
                self.log('[mqtt publish] topic: "{0}" value: {1}'.format(sensor_topic, temperature_payload))
                self.call_service("mqtt/publish", topic=sensor_topic, payload=temperature_payload)
