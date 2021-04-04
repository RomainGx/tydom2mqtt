import json

from sensors import Sensor

LIGHT_COMMAND_TOPIC = "light/tydom/{id}/set_levelCmd"
LIGHT_CONFIG_TOPIC = "homeassistant/light/tydom/{id}/config"
LIGHT_LEVEL_TOPIC = "light/tydom/{id}/current_level"
LIGHT_SET_LEVEL_TOPIC = "light/tydom/{id}/set_level"
LIGHT_ATTRIBUTES_TOPIC = "light/tydom/{id}/attributes"


class Light:
    def __init__(self, tydom_attributes, set_level=None, mqtt=None):
        self.attributes = tydom_attributes
        self.device_id = self.attributes['device_id']
        self.endpoint_id = self.attributes['endpoint_id']
        self.id = self.attributes['id']
        self.name = self.attributes['light_name']
        try:
            self.current_level = self.attributes['level']
        except Exception as e:
            print(e)
            self.current_level = None
        self.set_level = set_level
        self.mqtt = mqtt

    async def setup(self):
        self.device = {
            'manufacturer': 'Delta Dore',
            'model': 'Lumiere',
            'name': self.name,
            'identifiers': self.id
        }

        self.config_topic = LIGHT_CONFIG_TOPIC.format(id=self.id)
        self.config = {
            'name': self.name,
            'brightness_scale': 100,
            'unique_id': self.id,
            'optimistic': True,
            'brightness_state_topic': LIGHT_LEVEL_TOPIC.format(id=self.id),
            'brightness_command_topic': LIGHT_SET_LEVEL_TOPIC.format(id=self.id),
            'command_topic': LIGHT_COMMAND_TOPIC.format(id=self.id),
            'state_topic': LIGHT_LEVEL_TOPIC.format(id=self.id),
            'json_attributes_topic': LIGHT_ATTRIBUTES_TOPIC.format(id=self.id),
            'payload_on': "ON",
            'on_command_type': "brightness",
            'retain': 'false',
            'device': self.device
        }
        # self.config['set_level_topic'] = light_set_level_topic.format(id=self.id)
        # print(self.config)

        if (self.mqtt != None):
            self.mqtt.mqtt_client.publish(self.config_topic, json.dumps(self.config), qos=0)
        # setup_pub = '(self.config_topic, json.dumps(self.config), qos=0)'
        # return(setup_pub)

    async def update(self):
        await self.setup()

        try:
            await self.update_sensors()
        except Exception as e:
            print("light sensors Error :")
            print(e)

        self.level_topic = LIGHT_LEVEL_TOPIC.format(id=self.id, current_level=self.current_level)
        
        if (self.mqtt != None):
            self.mqtt.mqtt_client.publish(self.level_topic, self.current_level, qos=0, retain=True)
            # self.mqtt.mqtt_client.publish('homeassistant/sensor/tydom/last_update', str(datetime.fromtimestamp(time.time())), qos=1, retain=True)
            self.mqtt.mqtt_client.publish(self.config['json_attributes_topic'], self.attributes, qos=0)
        print("light created / updated : ", self.name, self.id, self.current_level)

        # update_pub = '(self.level_topic, self.current_level, qos=0, retain=True)'
        # return(update_pub)

    async def update_sensors(self):
        for i, j in self.attributes.items():
            # sensor_name = "tydom_alarm_sensor_"+i
            # print("name "+sensor_name, "elem_name "+i, "attributes_topic_from_device ",self.config['json_attributes_topic'], "mqtt",self.mqtt)
            if not i == 'device_type' or not i == 'id':
                new_sensor = Sensor(elem_name=i, tydom_attributes_payload=self.attributes, attributes_topic_from_device=self.config['json_attributes_topic'], mqtt=self.mqtt)
                await new_sensor.update()

    async def put_level(tydom_client, device_id, light_id, level):
        print(light_id, 'level', level)
        if not (level == ''):
            await tydom_client.put_devices_data(device_id, light_id, 'level', level)

    async def put_levelCmd(tydom_client, device_id, light_id, levelCmd):
        print(light_id, 'levelCmd', levelCmd)
        if not (levelCmd == ''):
            await tydom_client.put_devices_data(device_id, light_id, 'levelCmd', levelCmd)
