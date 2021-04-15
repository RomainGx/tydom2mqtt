import json
import logging
import sys

from alarm_control_panel import Alarm
from boiler import Boiler
from communication.utils import *
from cover import Cover
from devices.utils import *
from light import Light
from parsing.utils import *
from sensors import Sensor

_LOGGER = logging.getLogger(__name__)

# Device dict for parsing
device_name_dict = dict()
device_endpoint_dict = dict()
device_type_dict = dict()


def print_incoming_message_exception(bytes_str):
    print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
    print('RAW INCOMING :')
    print(bytes_str)
    print('END RAW')
    print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")


def print_global_incoming_message_exception(bytes_str, incoming, error):
    print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
    print('receiveMessage error')
    print('RAW :')
    print(bytes_str)
    print("Incoming payload :")
    print(incoming)
    print("Error :")
    print(error)
    print('Exiting to ensure systemd restart....')


def get_type_from_id(unique_id):
    device_type = ""
    if len(device_type_dict) != 0 and unique_id in device_type_dict.keys():
        device_type = device_type_dict[unique_id]
    else:
        print('{} not in dic device_type'.format(unique_id))

    return device_type


def get_name_from_id(unique_id):
    name = ""
    if len(device_name_dict) != 0 and unique_id in device_name_dict.keys():
        name = device_name_dict[unique_id]
    else:
        print('{} not in dic device_name'.format(unique_id))
    return name


def parse_config_data(parsed):
    for endpoint_info in parsed["endpoints"]:
        last_usage = str(endpoint_info["last_usage"])
        device_unique_id = str(endpoint_info["id_endpoint"]) + "_" + str(endpoint_info["id_device"])

        if is_shutter(last_usage) or is_light(last_usage) or is_window(last_usage) or is_door(last_usage) or is_boiler(last_usage) or is_consumption(last_usage):
            device_name_dict[device_unique_id] = endpoint_info["name"]
            device_type_dict[device_unique_id] = endpoint_info["last_usage"]
            device_endpoint_dict[device_unique_id] = endpoint_info["id_endpoint"]
        elif is_alarm(last_usage):
            device_name_dict[device_unique_id] = "Tyxal Alarm"
            device_type_dict[device_unique_id] = 'alarm'
            device_endpoint_dict[device_unique_id] = endpoint_info["id_endpoint"]
        elif is_electric(last_usage):
            device_name_dict[device_unique_id] = endpoint_info["name"]
            device_type_dict[device_unique_id] = 'boiler'
            device_endpoint_dict[device_unique_id] = endpoint_info["id_endpoint"]

    print('Configuration updated')


class TydomMessageHandler():
    def __init__(self, incoming_bytes, tydom_client, mqtt_client):
        self.incoming_bytes = incoming_bytes
        self.tydom_client = tydom_client
        self.cmd_prefix = tydom_client.cmd_prefix
        self.mqtt_client = mqtt_client

    async def incoming_triage(self):
        bytes_str = self.incoming_bytes

        # If there is no MQTT client, return the incoming message
        if self.mqtt_client is None:
            return bytes_str
        else:
            incoming = None
            # Scanning the first characters
            first = str(bytes_str[:40])

            try:
                if "Uri-Origin: /refresh/all" in first in first:
                    pass
                elif ("PUT /devices/data" in first) or ("/devices/cdata" in first):
                    try:
                        incoming = self.parse_put_response(bytes_str)
                        await self.parse_response(incoming)
                    except:
                        print_incoming_message_exception(bytes_str)
                elif "scn" in first:
                    try:
                        incoming = get(bytes_str)
                        await self.parse_response(incoming)
                        print('Scenarii message processed !')
                        print("##################################")
                    except:
                        print_incoming_message_exception(bytes_str)
                elif "POST" in first:
                    try:
                        incoming = self.parse_put_response(bytes_str)
                        await self.parse_response(incoming)
                        print('POST message processed !')
                    except:
                        print_incoming_message_exception(bytes_str)
                elif "HTTP/1.1" in first:
                    response = response_from_bytes(bytes_str[len(self.cmd_prefix):])
                    incoming = response.data.decode("utf-8")
                    try:
                        await self.parse_response(incoming)
                    except:
                        print_incoming_message_exception(bytes_str)
                else:
                    print("Didn't detect incoming type, here it is :")
                    print_incoming_message_exception(bytes_str)

            except Exception as e:
                print_global_incoming_message_exception(bytes_str, incoming, e)
                # Exit all to ensure systemd restart
                sys.exit()

    # Basic response parsing. Typically GET responses + instanciate covers and alarm class for updating data
    async def parse_response(self, incoming):
        data = incoming
        msg_type = None
        first = str(data[:40])

        # Detect type of incoming data
        if data != '':
            if "id_catalog" in data:
                print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
                print('Incoming message type : config detected')
                msg_type = 'msg_config'
            elif "id" in first:
                print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
                print('Incoming message type : data detected')
                msg_type = 'msg_data'
            elif "doctype" in first:
                print('Incoming message type : html detected (probable 404)')
                msg_type = 'msg_html'
                print(data)
            elif "productName" in first:
                print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
                print('Incoming message type : Info detected')
                msg_type = 'msg_info'
            else:
                print('Incoming message type : no type detected')
                print(data)

            if not (msg_type is None):
                try:
                    if msg_type == 'msg_config':
                        parsed = json.loads(data)
                        parse_config_data(parsed)
                    elif msg_type == 'msg_data':
                        parsed = json.loads(data)
                        await self.parse_devices_data(parsed)
                    elif msg_type == 'msg_html':
                        print("HTML Response ?")
                    elif msg_type == 'msg_info':
                        pass
                    else:
                        # Default json dump
                        print()
                        print(json.dumps(parsed, sort_keys=True, indent=4, separators=(',', ': ')))
                except Exception as error:
                    print('Cannot parse response !')
                    if error != 'Expecting value: line 1 column 1 (char 0)':
                        print("Error : ", error)
                        print(parsed)
            print('Incoming data parsed successfully !')
            return 0

    async def parse_consumption_endpoint(self, endpoint_id, device_id, endpoint, friendly_name):
        attr_consumption = {}

        for endpoint_attributes in endpoint["data"]:
            if endpoint_attributes["name"] in devicesKeywords.CONSUMPTION and endpoint_attributes["validity"] == "upToDate":
                attr_consumption = {
                    'device_id': device_id,
                    'endpoint_id': endpoint_id,
                    'id': str(device_id) + '_' + str(endpoint_id),
                    'name': friendly_name,
                    'device_type': 'sensor',
                    endpoint_attributes["name"]: endpoint_attributes["value"]
                }

                if endpoint_attributes["name"] in devicesKeywords.CONSUMPTION_CLASSES:
                    attr_consumption['device_class'] = devicesKeywords.CONSUMPTION_CLASSES[endpoint_attributes["name"]]

                if endpoint_attributes["name"] in devicesKeywords.CONSUMPTION_UNITS:
                    attr_consumption['unit_of_measurement'] = devicesKeywords.CONSUMPTION_UNITS[endpoint_attributes["name"]]

                new_consumption = Sensor(endpoint_attributes["name"], attr_consumption, self.mqtt_client)
                await new_consumption.update()

        return attr_consumption

    async def configure_alarm(self, alarm_attributes, device_id, endpoint_id):
        attr_alarm = {
            'device_id': device_id,
            'endpoint_id': endpoint_id,
            'id': str(device_id) + '_' + str(endpoint_id),
            'alarm_name': "Tyxal Alarm",
            'name': "Tyxal Alarm"
        }
        for attribute_name in alarm_attributes.keys():
            attr_alarm[attribute_name] = alarm_attributes[attribute_name]

        state = None
        sos_state = False
        try:
            if 'alarmState' in attr_alarm and (attr_alarm['alarmState'] == "ON" or attr_alarm['alarmState'] == "QUIET"):
                state = "triggered"
            elif 'alarmState' in attr_alarm and attr_alarm['alarmState'] == "DELAYED":
                state = "pending"

            if 'alarmSOS' in attr_alarm and attr_alarm['alarmSOS'] == "true":
                state = "triggered"
                sos_state = True
            elif 'alarmMode' in attr_alarm and attr_alarm["alarmMode"] == "ON":
                state = "armed_away"
            elif 'alarmMode' in attr_alarm and attr_alarm["alarmMode"] == "ZONE":
                state = "armed_home"
            elif 'alarmMode' in attr_alarm and attr_alarm["alarmMode"] == "OFF":
                state = "disarmed"
            elif 'alarmMode' in attr_alarm and attr_alarm["alarmMode"] == "MAINTENANCE":
                state = "disarmed"

            if sos_state:
                print("SOS !")

            if not (state is None):
                alarm = Alarm(state, attr_alarm, self.mqtt_client)
                await alarm.update()
        except Exception as e:
            print("Error in alarm parsing !")
            print(e)

    async def create_sensor(self, device_id, endpoint_id, friendly_name, all_attributes, keywords):
        sensor_attributes = {
            'device_id': device_id,
            'endpoint_id': endpoint_id,
            'id': str(device_id) + '_' + str(endpoint_id),
            'name': friendly_name
        }

        for attribute_name in keywords.keys():
            if attribute_name in all_attributes:
                sensor_attributes[attribute_name] = all_attributes[attribute_name]
                if keywords[attribute_name] is not None:
                    sensor_attributes['device_class'] = keywords[attribute_name]
                new_sensor = Sensor(attribute_name, sensor_attributes, self.mqtt_client)
                await new_sensor.update()

    async def parse_endpoint(self, device_id, endpoint):
        try:
            endpoint_id = endpoint["id"]
            unique_id = str(endpoint_id) + "_" + str(device_id)
            name_of_id = get_name_from_id(unique_id)
            type_of_id = get_type_from_id(unique_id)
            print("Traite endpoint {}, device {} ; name = {} (type {})".format(endpoint_id, device_id, name_of_id, type_of_id))
            print(endpoint)

            friendly_name = device_id
            if len(name_of_id) != 0:
                friendly_name = name_of_id

            if is_light(type_of_id):
                light_attributes = parse_light_endpoint(endpoint)
                if len(light_attributes.keys()) > 0:
                    new_light = Light(light_attributes, device_id, endpoint_id, friendly_name, mqtt=self.mqtt_client)
                    await new_light.update()
            elif is_shutter(type_of_id):
                cover_attributes = parse_cover_endpoint(endpoint)
                if len(cover_attributes.keys()) > 0:
                    new_cover = Cover(cover_attributes, device_id, endpoint_id, friendly_name, mqtt=self.mqtt_client)
                    await new_cover.update()
            elif is_window(type_of_id):
                window_attributes = parse_window_endpoint(endpoint)
                if len(window_attributes.keys()) > 0:
                    await self.create_sensor(device_id, endpoint_id, friendly_name, window_attributes, devicesKeywords.WINDOW)
            elif is_door(type_of_id):
                door_attributes = parse_door_endpoint(endpoint)
                if len(door_attributes.keys()) > 0:
                    await self.create_sensor(device_id, endpoint_id, friendly_name, door_attributes, devicesKeywords.DOOR)
            elif is_boiler(type_of_id):
                attr_boiler = parse_boiler_endpoint(endpoint)
                if len(attr_boiler.keys()) > 0:
                    new_boiler = Boiler(attr_boiler, device_id, endpoint_id, friendly_name, self.tydom_client, self.mqtt_client)
                    await new_boiler.update()
            elif is_alarm(type_of_id):
                alarm_attributes = parse_alarm_endpoint(endpoint)
                if len(alarm_attributes.keys()) > 0:
                    await self.configure_alarm(alarm_attributes, device_id, endpoint_id)
            elif is_consumption(type_of_id):
                await self.parse_consumption_endpoint(endpoint_id, device_id, endpoint, friendly_name)
            else:
                print("Unknown type for {}".format(unique_id))
        except Exception as e:
            print('msg_data error in parsing !')
            print(e)

    async def parse_devices_data(self, parsed):
        for i in parsed:
            for endpoint in i["endpoints"]:
                if endpoint["error"] == 0 and len(endpoint["data"]) > 0:
                    await self.parse_endpoint(device_id=i["id"], endpoint=endpoint)

    # PUT response DIRTY parsing
    def parse_put_response(self, bytes_str):
        # TODO : Find a cooler way to parse nicely the PUT HTTP response
        resp = bytes_str[len(self.cmd_prefix):].decode("utf-8")
        fields = resp.split("\r\n")
        fields = fields[6:]  # ignore the PUT / HTTP/1.1
        end_parsing = False
        i = 0
        output = str()
        while not end_parsing:
            field = fields[i]
            if len(field) == 0 or field == '0':
                end_parsing = True
            else:
                output += field
                i = i + 2
        parsed = json.loads(output)
        return json.dumps(parsed)
