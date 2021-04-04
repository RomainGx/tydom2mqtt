import json

from sensors import Sensor

ALARM_TOPIC = "alarm_control_panel/tydom/#"
ALARM_CONFIG_TOPIC = "homeassistant/alarm_control_panel/tydom/{id}/config"
ALARM_STATE_TOPIC = "alarm_control_panel/tydom/{id}/state"
ALARM_COMMAND_TOPIC = "alarm_control_panel/tydom/{id}/set_alarm_state"
ALARM_ATTRIBUTES_TOPIC = "alarm_control_panel/tydom/{id}/attributes"

class Alarm:
    def __init__(self, current_state, tydom_attributes=None, mqtt=None):
        self.attributes = tydom_attributes
        self.device_id = self.attributes['device_id']
        self.endpoint_id = self.attributes['endpoint_id']
        self.id = self.attributes['id']
        self.name = self.attributes['name']
        self.current_state = current_state
        self.mqtt = mqtt
        self.device = {}
        self.config = {}
        self.config_alarm_topic = ''
        self.state_topic = ''

    async def setup(self):
        self.device = {
            'manufacturer': 'Delta Dore',
            'model': 'Tyxal',
            'name': self.name,
            'identifiers': self.id
        }

        self.config_alarm_topic = ALARM_CONFIG_TOPIC.format(id=self.id)

        self.config = {
            'name': self.name,
            'unique_id': self.id,
            'device': self.device,
            'command_topic': ALARM_COMMAND_TOPIC.format(id=self.id),
            'state_topic': ALARM_STATE_TOPIC.format(id=self.id),
            'code_arm_required': 'false',
            'json_attributes_topic': ALARM_ATTRIBUTES_TOPIC.format(id=self.id)
        }

        if self.mqtt is not None:
            self.mqtt.mqtt_client.publish(self.config_alarm_topic, json.dumps(self.config), qos=0)  # Alarm Config

    async def update(self):
        await self.setup()

        try:
            await self.update_sensors()
        except Exception as e:
            print("Alarm sensors Error :")
            print(e)

        self.state_topic = ALARM_STATE_TOPIC.format(id=self.id, state=self.current_state)
        if self.mqtt is not None:
            self.mqtt.mqtt_client.publish(self.state_topic, self.current_state, qos=0, retain=True)  # Alarm State
            self.mqtt.mqtt_client.publish(self.config['json_attributes_topic'], self.attributes, qos=0)
        print("Alarm created / updated : ", self.name, self.id, self.current_state)

    async def update_sensors(self):
        for i, j in self.attributes.items():
            # if j == 'ON' and not 'alarm' in i:
            #     j = True
            # elif j == 'OFF' and not 'alarm' in i:
            #     j == False
            # sensor_name = "tydom_alarm_sensor_"+i
            # print("name "+sensor_name, "elem_name "+i, "attributes_topic_from_device ",self.config['json_attributes_topic'], "mqtt",self.mqtt)
            if not i == 'device_type' or not i == 'id':
                new_sensor = Sensor(elem_name=i, tydom_attributes_payload=self.attributes, attributes_topic_from_device=self.config['json_attributes_topic'], mqtt=self.mqtt)
                await new_sensor.update()

    async def put_alarm_state(tydom_client, device_id, alarm_id, home_zone, night_zone, asked_state=None):
        value = None
        zone_id = None

        if asked_state == 'ARM_AWAY':
            value = 'ON'
            zone_id = None
        elif asked_state == 'ARM_HOME': #TODO : Separate both and let user specify with zone is what
            value = "ON"
            zone_id = home_zone
        elif asked_state == 'ARM_NIGHT': #TODO : Separate both and let user specify with zone is what
            value = "ON"
            zone_id = night_zone
        elif asked_state == 'DISARM':
            value = 'OFF'
            zone_id = None

        await tydom_client.put_alarm_cdata(device_id=device_id, alarm_id=alarm_id, value=value, zone_id=zone_id)
