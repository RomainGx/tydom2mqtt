import json

from sensors import Sensor

COVER_COMMAND_TOPIC = "cover/tydom/{id}/set_positionCmd"
COVER_CONFIG_TOPIC = "homeassistant/cover/tydom/{id}/config"
COVER_POSITION_TOPIC = "cover/tydom/{id}/current_position"
COVER_SET_POSITION_TOPIC = "cover/tydom/{id}/set_position"
COVER_ATTRIBUTES_TOPIC = "cover/tydom/{id}/attributes"

class Cover:
    def __init__(self, tydom_attributes, set_position=None, mqtt=None):
        self.attributes = tydom_attributes
        self.device_id = self.attributes['device_id']
        self.endpoint_id = self.attributes['endpoint_id']
        self.id = self.attributes['id']
        self.name = self.attributes['cover_name']
        self.current_position = self.attributes['position']
        self.set_position = set_position
        self.mqtt = mqtt

    async def setup(self):
        self.device = {
            'manufacturer': 'Delta Dore',
            'model': 'Volet',
            'name': self.name,
            'identifiers': self.id
        }

        self.config_topic = COVER_CONFIG_TOPIC.format(id=self.id)
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
            'device': self.device
        }
        # self.config['attributes'] = self.attributes
        # print(self.config)

        if self.mqtt is not None:
            self.mqtt.mqtt_client.publish(self.config_topic, json.dumps(self.config), qos=0)
        # setup_pub = '(self.config_topic, json.dumps(self.config), qos=0)'
        # return(setup_pub)

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
            # self.mqtt.mqtt_client.publish('homeassistant/sensor/tydom/last_update', str(datetime.fromtimestamp(time.time())), qos=1, retain=True)
            self.mqtt.mqtt_client.publish(self.config['json_attributes_topic'], self.attributes, qos=0)
        print("Cover created / updated : ", self.name, self.id, self.current_position)

        # update_pub = '(self.position_topic, self.current_position, qos=0, retain=True)'
        # return(update_pub)

    async def update_sensors(self):
        for i, j in self.attributes.items():
            # sensor_name = "tydom_alarm_sensor_"+i
            # print("name "+sensor_name, "elem_name "+i, "attributes_topic_from_device ",self.config['json_attributes_topic'], "mqtt",self.mqtt)
            if not i == 'device_type' or not i == 'id':
                new_sensor = Sensor(elem_name=i, tydom_attributes_payload=self.attributes, attributes_topic_from_device=self.config['json_attributes_topic'], mqtt=self.mqtt)
                await new_sensor.update()

    async def put_position(tydom_client, device_id, cover_id, position):
        print(cover_id, 'position', position)
        if not (position == ''):
            await tydom_client.put_devices_data(device_id, cover_id, 'position', position)

    async def put_positionCmd(tydom_client, device_id, cover_id, positionCmd):
        print(cover_id, 'positionCmd', positionCmd)
        if not (positionCmd == ''):
            await tydom_client.put_devices_data(device_id, cover_id, 'positionCmd', positionCmd)
