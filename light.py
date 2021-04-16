import json

import devices.devicesKeywords
from devices.utils import get_device_info
from devices.utils2 import create_and_update_sensor

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
        self.config = {}
        self.config_topic = LIGHT_CONFIG_TOPIC.format(id=self.id)

        try:
            self.current_level = tydom_attributes['level']
        except Exception as e:
            print(e)
            self.current_level = None

        self.set_level = set_level
        self.level_topic = LIGHT_LEVEL_TOPIC.format(id=self.id, current_level=self.current_level)
        self.mqtt = mqtt

    async def setup(self):
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
            'device': get_device_info(self.name, self.device_id, "Lumiere")
        }

        if self.mqtt is not None:
            self.mqtt.mqtt_client.publish(self.config_topic, json.dumps(self.config), qos=0)

    async def update(self):
        await self.setup()

        try:
            await self.update_sensors()
        except Exception as e:
            print("light sensors Error :")
            print(e)
        
        if self.mqtt is not None:
            self.mqtt.mqtt_client.publish(self.level_topic, self.current_level, qos=0, retain=True)
            self.mqtt.mqtt_client.publish(self.config['json_attributes_topic'], self.attributes, qos=0)
        print("light created / updated : ", self.name, self.id, self.current_level)

    async def update_sensors(self):
        await create_and_update_sensor(self.mqtt, self.device_id, self.endpoint_id, self.name, self.attributes, devices.devicesKeywords.LIGHT)

    async def put_level(tydom_client, device_id, light_id, level):
        print(light_id, 'put_level', level)
        if not (level == ''):
            await tydom_client.put_devices_data(device_id, light_id, 'level', level)

    async def put_level_cmd(tydom_client, device_id, light_id, level_cmd):
        print(light_id, 'levelCmd', level_cmd)
        if not (level_cmd == ''):
            await tydom_client.put_devices_data(device_id, light_id, 'levelCmd', level_cmd)
