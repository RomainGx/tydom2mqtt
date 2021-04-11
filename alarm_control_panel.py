import json

from sensors import Sensor
from devices.utils import get_device_info

ALARM_CONFIG_TOPIC = "homeassistant/alarm_control_panel/tydom/{id}/config"
ALARM_STATE_TOPIC = "homeassistant/alarm_control_panel/tydom/{id}/state"
ALARM_COMMAND_TOPIC = "homeassistant/alarm_control_panel/tydom/{id}/set_alarm_state"
ALARM_ATTRIBUTES_TOPIC = "homeassistant/alarm_control_panel/tydom/{id}/attributes"


class Alarm:
    def __init__(self, current_state, tydom_attributes=None, mqtt=None):
        self.attributes = tydom_attributes
        self.device_id = tydom_attributes['id']
        self.id = 'tyxal_alarm_' + self.device_id
        self.current_state = current_state
        self.mqtt = mqtt
        self.device = {}
        self.config = {}

    async def setup(self):
        self.config = {
            'name': self.attributes['name'],
            'unique_id': self.id,
            'device': get_device_info(self.attributes['name'], self.device_id, "Alarm"),
            'command_topic': ALARM_COMMAND_TOPIC.format(id=self.device_id),
            'state_topic': ALARM_STATE_TOPIC.format(id=self.device_id),
            'code_arm_required': 'false',
            'json_attributes_topic': ALARM_ATTRIBUTES_TOPIC.format(id=self.device_id)
        }

        if self.mqtt is not None:
            self.mqtt.mqtt_client.publish(ALARM_CONFIG_TOPIC.format(id=self.device_id), json.dumps(self.config), qos=0)

    async def update(self):
        await self.setup()

        try:
            await self.update_sensors()
        except Exception as e:
            print("Alarm sensors Error :")
            print(e)

        if self.mqtt is not None:
            state_topic = ALARM_STATE_TOPIC.format(id=self.device_id, state=self.current_state)
            self.mqtt.mqtt_client.publish(state_topic, self.current_state, qos=0, retain=True)
            self.mqtt.mqtt_client.publish(self.config['json_attributes_topic'], self.attributes, qos=0)
        print("Alarm created / updated : ", self.attributes['name'], self.device_id, self.current_state)

    async def update_sensors(self):
        for elem_name in self.attributes.keys():
            if not elem_name == 'device_type' or not elem_name == 'id':
                new_sensor = Sensor(elem_name, self.attributes, self.config['json_attributes_topic'], self.mqtt)
                await new_sensor.update()

    async def put_alarm_state(tydom_client, device_id, alarm_id, home_zone, night_zone, asked_state=None):
        value = None
        zone_id = None

        if asked_state == 'ARM_AWAY':
            value = 'ON'
            zone_id = None
        elif asked_state == 'ARM_HOME':  # TODO : Separate both and let user specify with zone is what
            value = "ON"
            zone_id = home_zone
        elif asked_state == 'ARM_NIGHT':  # TODO : Separate both and let user specify with zone is what
            value = "ON"
            zone_id = night_zone
        elif asked_state == 'DISARM':
            value = 'OFF'
            zone_id = None

        await tydom_client.put_alarm_cdata(device_id=device_id, alarm_id=alarm_id, value=value, zone_id=zone_id)
