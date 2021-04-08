import json

from sensors import Sensor

LIGHT_COMMAND_TOPIC = "homeassistant/light/tydom/{id}/set_levelCmd"
LIGHT_CONFIG_TOPIC = "homeassistant/light/tydom/{id}/config"
LIGHT_LEVEL_TOPIC = "homeassistant/light/tydom/{id}/current_level"
LIGHT_SET_LEVEL_TOPIC = "homeassistant/light/tydom/{id}/set_level"
LIGHT_ATTRIBUTES_TOPIC = "homeassistant/light/tydom/{id}/attributes"


class Light:
    def __init__(self, tydom_attributes, device_id, endpoint_id, friendly_name, set_level=None, mqtt=None):
        self.attributes = tydom_attributes
        self.device_id = device_id
        self.endpoint_id = endpoint_id
        self.id = str(device_id) + '_' + str(endpoint_id)
        self.name = friendly_name

        try:
            self.current_level = tydom_attributes['level']
        except Exception as e:
            print(e)
            self.current_level = None

        self.set_level = set_level
        self.mqtt = mqtt

    async def setup(self):
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
            'on_command_type': "brightness",
            'retain': 'false',
            'device': {
                'manufacturer': 'Delta Dore',
                'model': 'Lumiere',
                'name': self.name,
                'identifiers': self.device_id
            }
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
        for attribute in self.attributes:
            tydom_attributes_payload = {
                'device_id': self.device_id,
                'endpoint_id': self.endpoint_id,
                'id': self.id,
                'name': self.name,
                attribute['name']: attribute['value']
            }
            new_sensor = Sensor(elem_name=attribute['name'], tydom_attributes_payload=tydom_attributes_payload, attributes_topic_from_device=self.config['json_attributes_topic'], mqtt=self.mqtt)
            await new_sensor.update()

    async def put_level(tydom_client, device_id, light_id, level):
        print(light_id, 'put_level', level)
        if not (level == ''):
            await tydom_client.put_devices_data(device_id, light_id, 'level', level)

    async def put_levelCmd(tydom_client, device_id, light_id, level_cmd):
        print(light_id, 'levelCmd', level_cmd)
        if not (level_cmd == ''):
            await tydom_client.put_devices_data(device_id, light_id, 'levelCmd', level_cmd)
