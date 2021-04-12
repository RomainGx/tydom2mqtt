import json

from sensors import Sensor
from devices.utils import get_device_info

COVER_COMMAND_TOPIC = "homeassistant/cover/tydom/{id}/set_positionCmd"
COVER_CONFIG_TOPIC = "homeassistant/cover/tydom/{id}/config"
COVER_POSITION_TOPIC = "homeassistant/cover/tydom/{id}/current_position"
COVER_SET_POSITION_TOPIC = "homeassistant/cover/tydom/{id}/set_position"
COVER_ATTRIBUTES_TOPIC = "homeassistant/cover/tydom/{id}/attributes"


class Cover:
    def __init__(self, tydom_attributes, device_id, endpoint_id, friendly_name, set_position=None, mqtt=None):
        self.attributes = tydom_attributes
        self.device_id = device_id
        self.endpoint_id = endpoint_id
        self.device_id = str(device_id) + '_' + str(endpoint_id)
        self.id = 'cover_tydom_' + self.device_id
        self.name = friendly_name
        self.current_position = tydom_attributes['position']
        self.set_position = set_position
        self.config = {}
        self.config_topic = COVER_CONFIG_TOPIC.format(id=self.id)
        self.mqtt = mqtt

    async def setup(self):
        self.config = {
            'name': self.name,
            'unique_id': self.id,
            'command_topic': COVER_COMMAND_TOPIC.format(id=self.id),
            'set_position_topic': COVER_SET_POSITION_TOPIC.format(id=self.id),
            'position_topic': COVER_POSITION_TOPIC.format(id=self.id),
            'json_attributes_topic': COVER_ATTRIBUTES_TOPIC.format(id=self.id),
            'payload_open': "UP",
            'payload_close': "DOWN",
            'payload_stop': "STOP",
            'retain': 'false',
            'device': get_device_info(self.name, self.id, "Volet")
        }

        if self.mqtt is not None:
            self.mqtt.mqtt_client.publish(self.config_topic, json.dumps(self.config), qos=0)

    async def update(self):
        await self.setup()

        try:
            await self.update_sensors()
        except Exception as e:
            print("Cover sensors Error :")
            print(e)

        self.position_topic = COVER_POSITION_TOPIC.format(id=self.id, current_position=self.current_position)

        if self.mqtt is not None:
            self.mqtt.mqtt_client.publish(self.position_topic, self.current_position, qos=0, retain=True)
            self.mqtt.mqtt_client.publish(self.config['json_attributes_topic'], self.attributes, qos=0)
        print("Cover created / updated : ", self.name, self.id, self.current_position)

    async def update_sensors(self):
        for attribute_name in self.attributes.keys():
            tydom_attributes_payload = {
                'device_id': self.device_id,
                'endpoint_id': self.endpoint_id,
                'id': self.id,
                'name': self.name,
                attribute_name: self.attributes[attribute_name]
            }
            new_sensor = Sensor(attribute_name, tydom_attributes_payload, self.config['json_attributes_topic'], self.mqtt)
            await new_sensor.update()

    async def put_position(tydom_client, device_id, cover_id, position):
        print(cover_id, 'position', position)
        if not (position == ''):
            await tydom_client.put_devices_data(device_id, cover_id, 'position', position)

    async def put_positionCmd(tydom_client, device_id, cover_id, positionCmd):
        print(cover_id, 'positionCmd', positionCmd)
        if not (positionCmd == ''):
            await tydom_client.put_devices_data(device_id, cover_id, 'positionCmd', positionCmd)
