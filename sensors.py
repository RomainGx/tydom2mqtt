import json

SENSOR_TOPIC = "homeassistant/sensor/tydom/#"
SENSOR_CONFIG_TOPIC = "homeassistant/sensor/tydom/{id}/config"
SENSOR_JSON_ATTRIBUTES_TOPIC = "homeassistant/sensor/tydom/{id}/state"

BINARY_SENSOR_TOPIC = "homeassistant/binary_sensor/tydom/#"
BINARY_SENSOR_CONFIG_TOPIC = "homeassistant/binary_sensor/tydom/{id}/config"
BINARY_SENSOR_JSON_ATTRIBUTES_TOPIC = "homeassistant/binary_sensor/tydom/{id}/state"

# State topic can be the same as the original device attributes topic !
class Sensor:
    def __init__(self, elem_name, tydom_attributes_payload, attributes_topic_from_device, mqtt=None):
        self.elem_name = elem_name
        self.elem_value = tydom_attributes_payload[self.elem_name]

        # init a state json
        state_dict = {elem_name: self.elem_value}
        self.attributes = state_dict

        # self.json_attributes_topic = attributes_topic_from_device #State extracted from json, but it will make sensor not in payload to be considerd offline....
        self.parent_device_id = str(tydom_attributes_payload['id'])
        self.id = elem_name + '_tydom_' + str(tydom_attributes_payload['id'])
        self.device_name = tydom_attributes_payload['name']
        self.name = elem_name + '_tydom_' + '_' + self.device_name.replace(" ", "_")
        if 'device_class' in tydom_attributes_payload.keys():
            self.device_class = tydom_attributes_payload['device_class']

        if 'unit_of_measurement' in tydom_attributes_payload.keys():
            self.unit_of_measurement = tydom_attributes_payload['unit_of_measurement']

        self.mqtt = mqtt

        self.binary = False
        # self.device_class = None
        self.config_topic = SENSOR_CONFIG_TOPIC.format(id=self.id)

        if self.elem_value == False or self.elem_value == True:
            self.binary = True
            self.json_attributes_topic = BINARY_SENSOR_JSON_ATTRIBUTES_TOPIC.format(id=self.id)
            self.config_topic = BINARY_SENSOR_CONFIG_TOPIC.format(id=self.id)
            # if 'efect' in self.elem_name:
            #     self.device_class = 'problem'
            # elif 'ntrusion' in self.elem_name or 'zone' in self.elem_name or 'alarm' in self.elem_name:
            #     self.device_class = 'safety'
            # elif 'gsm' in self.elem_name:
            #     self.device_class = 'signal_strength'
        else:
            self.json_attributes_topic = SENSOR_JSON_ATTRIBUTES_TOPIC.format(id=self.id)
            self.config_topic = SENSOR_CONFIG_TOPIC.format(id=self.id)
            # if 'emperature' in self.elem_name:
            #     self.device_class = 'temperature'
       


    # SENSOR:
    # None: Generic sensor. This is the default and doesn’t need to be set.
    # battery: Percentage of battery that is left.
    # humidity: Percentage of humidity in the air.
    # illuminance: The current light level in lx or lm.
    # signal_strength: Signal strength in dB or dBm.
    # temperature: Temperature in °C or °F.
    # power: Power in W or kW.
    # pressure: Pressure in hPa or mbar.
    # timestamp: Datetime object or timestamp string.        
    # BINARY :
    # None: Generic on/off. This is the default and doesn’t need to be set.
    # battery: on means low, off means normal
    # cold: on means cold, off means normal
    # connectivity: on means connected, off means disconnected
    # door: on means open, off means closed
    # garage_door: on means open, off means closed
    # gas: on means gas detected, off means no gas (clear)
    # heat: on means hot, off means normal
    # light: on means light detected, off means no light
    # lock: on means open (unlocked), off means closed (locked)
    # moisture: on means moisture detected (wet), off means no moisture (dry)
    # motion: on means motion detected, off means no motion (clear)
    # moving: on means moving, off means not moving (stopped)
    # occupancy: on means occupied, off means not occupied (clear)
    # opening: on means open, off means closed
    # plug: on means device is plugged in, off means device is unplugged
    # power: on means power detected, off means no power
    # presence: on means home, off means away
    # problem: on means problem detected, off means no problem (OK)
    # safety: on means unsafe, off means safe
    # smoke: on means smoke detected, off means no smoke (clear)
    # sound: on means sound detected, off means no sound (clear)
    # vibration: on means vibration detected, off means no vibration (clear)
    # window: on means open, off means closed
    async def setup(self):
        self.device = {
            'manufacturer': 'Delta Dore',
            'model': 'Sensor',
            'name': self.device_name,
            'identifiers': self.parent_device_id
        }

        self.config_sensor_topic = SENSOR_CONFIG_TOPIC.format(id=self.id)

        self.config = {'name': self.name, 'unique_id': self.id}
        try:
            self.config['device_class'] = self.device_class
        except AttributeError:
            pass
        try:
            self.config['unit_of_measurement'] = self.unit_of_measurement
        except AttributeError:
            pass
        # self.config['device_class'] = self.device_class
        
        #
        # self.config['value_template'] = "{{ value_json."+self.elem_name+" }}"
        # self.config['attributes'] = self.attributes

        # DISABLED, ALL VALUES
        # value_json = "value_json."+self.elem_name+'"'
        # self.config['value_template'] = "{% if "+value_json+" is defined and "+value_json+" != '' %} {{ value_json."+value_json+" }} {% else %} {{ states('sensor." + self.name + "') }} {% endif %}"

        # self.config['force_update'] = True
        self.config['device'] = self.device
        self.config['state_topic'] = self.json_attributes_topic

        if self.mqtt is not None:
            self.mqtt.mqtt_client.publish((self.config_topic).lower(), json.dumps(self.config), qos=0, retain=True)  # sensor Config
        # print("CONFIG : ",(self.config_topic).lower(), json.dumps(self.config))

    async def update(self):
        # 3 items are necessary :
        # - config to config config_sensor_topic + config payload is the schema
        # - state payload to state topic in config with all attributes

        if 'name' in self.elem_name or 'device_type' in self.elem_name or self.elem_value == None:
            pass  # OOOOOOOOOH that's quick and dirty
        else:
            await self.setup()  # Publish config
            payload_value = self.elem_value

            # Publish state json to state topic
            if self.mqtt is not None:
                # print(self.json_attributes_topic, self.attributes)
                # self.mqtt.mqtt_client.publish(self.json_attributes_topic, self.attributes, qos=0) #sensor json State
                if self.binary:
                    if self.elem_value:
                        payload_value = "ON"
                    else:
                        payload_value = "OFF"
                self.mqtt.mqtt_client.publish(self.json_attributes_topic, payload_value, qos=0) #sensor State
            if not self.binary:
                print("Sensor created / updated : ", self.name, payload_value, self.id)
            else:
                print("Binary sensor created / updated : ", self.name, payload_value, self.id)