import json
import logging
import sys
from http.client import HTTPResponse
from http.server import BaseHTTPRequestHandler
from io import BytesIO

import urllib3

from alarm_control_panel import Alarm
from boiler import Boiler
from cover import Cover
from light import Light
from sensors import Sensor

_LOGGER = logging.getLogger(__name__)

# Dicts
DEVICE_ALARM_KEYWORDS = ['alarmMode', 'alarmState', 'alarmSOS', 'zone1State', 'zone2State', 'zone3State', 'zone4State', 'zone5State', 'zone6State', 'zone7State', 'zone8State', 'gsmLevel', 'inactiveProduct', 'zone1State', 'liveCheckRunning', 'networkDefect', 'unitAutoProtect', 'unitBatteryDefect', 'unackedEvent', 'alarmTechnical', 'systAutoProtect', 'sysBatteryDefect', 'zsystSupervisionDefect', 'systOpenIssue', 'systTechnicalDefect', 'videoLinkDefect', 'outTemperature']
DEVICE_ALARM_DETAILS_KEYWORDS = ['alarmSOS', 'zone1State', 'zone2State', 'zone3State', 'zone4State', 'zone5State', 'zone6State', 'zone7State', 'zone8State', 'gsmLevel', 'inactiveProduct', 'zone1State', 'liveCheckRunning', 'networkDefect', 'unitAutoProtect', 'unitBatteryDefect', 'unackedEvent', 'alarmTechnical', 'systAutoProtect', 'sysBatteryDefect', 'zsystSupervisionDefect', 'systOpenIssue', 'systTechnicalDefect', 'videoLinkDefect', 'outTemperature']

DEVICE_LIGHT_KEYWORDS = ['level', 'onFavPos', 'thermicDefect', 'battDefect', 'loadDefect', 'cmdDefect', 'onPresenceDetected', 'onDusk']
DEVICE_LIGHT_DETAILS_KEYWORDS = ['onFavPos', 'thermicDefect', 'battDefect', 'loadDefect', 'cmdDefect', 'onPresenceDetected', 'onDusk']

DEVICE_DOOR_KEYWORDS = ['openState', 'intrusionDetect']
DEVICE_DOOR_DETAILS_KEYWORDS = ['onFavPos', 'thermicDefect', 'obstacleDefect', 'intrusion', 'battDefect']

DEVICE_COVER_KEYWORDS = ['position', 'onFavPos', 'thermicDefect', 'obstacleDefect', 'intrusion', 'battDefect']
DEVICE_COVER_DETAILS_KEYWORDS = ['onFavPos', 'thermicDefect', 'obstacleDefect', 'intrusion', 'battDefect', 'position']

#climateKeywords = ['temperature', 'authorization', 'hvacMode', 'setpoint']

DEVICE_BOILER_KEYWORDS = [
    'thermicLevel',
    'delayThermicLevel',
    'temperature',
    'authorization',
    'hvacMode',
    'timeDelay',
    'tempoOn',
    'antifrostOn',
    'openingDetected',
    'presenceDetected',
    'absence',
    'loadSheddingOn',
    'setpoint',
    'delaySetpoint',
    'anticipCoeff',
    'outTemperature'
]

DEVICE_CONSUMPTION_CLASSES = {
    'energyInstantTotElec': 'current',
    'energyInstantTotElec_Min': 'current',
    'energyInstantTotElec_Max': 'current',
    'energyScaleTotElec_Min': 'current',
    'energyScaleTotElec_Max': 'current',
    'energyInstantTotElecP': 'power',
    'energyInstantTotElec_P_Min': 'power',
    'energyInstantTotElec_P_Max': 'power',
    'energyScaleTotElec_P_Min': 'power',
    'energyScaleTotElec_P_Max': 'power',
    'energyInstantTi1P': 'power',
    'energyInstantTi1P_Min': 'power',
    'energyInstantTi1P_Max': 'power',
    'energyScaleTi1P_Min': 'power',
    'energyScaleTi1P_Max': 'power',
    'energyInstantTi1I': 'current',
    'energyInstantTi1I_Min': 'current',
    'energyInstantTi1I_Max': 'current',
    'energyScaleTi1I_Min': 'current',
    'energyScaleTi1I_Max': 'current',
    'energyTotIndexWatt': 'energy'
}

DEVICE_CONSUMPTION_UNIT_OF_MEASUREMENT = {
    'energyInstantTotElec': 'A',
    'energyInstantTotElec_Min': 'A',
    'energyInstantTotElec_Max': 'A',
    'energyScaleTotElec_Min': 'A',
    'energyScaleTotElec_Max': 'A',
    'energyInstantTotElecP': 'W',
    'energyInstantTotElec_P_Min': 'W',
    'energyInstantTotElec_P_Max': 'W',
    'energyScaleTotElec_P_Min': 'W',
    'energyScaleTotElec_P_Max': 'W',
    'energyInstantTi1P': 'W',
    'energyInstantTi1P_Min': 'W',
    'energyInstantTi1P_Max': 'W',
    'energyScaleTi1P_Min': 'W',
    'energyScaleTi1P_Max': 'W',
    'energyInstantTi1I': 'A',
    'energyInstantTi1I_Min': 'A',
    'energyInstantTi1I_Max': 'A',
    'energyScaleTi1I_Min': 'A',
    'energyScaleTi1I_Max': 'A',
    'energyTotIndexWatt': 'Wh'
}
DEVICE_CONSUMPTION_KEYWORDS = DEVICE_CONSUMPTION_CLASSES.keys()

# Device dict for parsing
device_name_dict = dict()
device_endpoint_dict = dict()
device_type_dict = dict()
# Thanks @Max013 !

class TydomMessageHandler():
    def __init__(self, incoming_bytes, tydom_client, mqtt_client):
        self.incoming_bytes = incoming_bytes
        self.tydom_client = tydom_client
        self.cmd_prefix = tydom_client.cmd_prefix
        self.mqtt_client = mqtt_client

    async def incomingTriage(self):
        bytes_str = self.incoming_bytes

        if self.mqtt_client is None:  # If not MQTT client, return incoming message to use it with anything.
            return bytes_str
        else:
            incoming = None
            first = str(bytes_str[:40])  # Scanning 1st characters

            try:
                if "Uri-Origin: /refresh/all" in first in first:
                    pass
                elif ("PUT /devices/data" in first) or ("/devices/cdata" in first):
                    try:
                        incoming = self.parse_put_response(bytes_str)
                        await self.parse_response(incoming)
                    except:
                        print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
                        print('RAW INCOMING :')
                        print(bytes_str)
                        print('END RAW')
                        print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
                elif "scn" in first:
                    try:
                        incoming = get(bytes_str)
                        await self.parse_response(incoming)
                        print('Scenarii message processed !')
                        print("##################################")
                    except:
                        print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
                        print('RAW INCOMING :')
                        print(bytes_str)
                        print('END RAW')
                        print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
                elif "POST" in first:
                    try:
                        incoming = self.parse_put_response(bytes_str)
                        await self.parse_response(incoming)
                        print('POST message processed !')
                    except:
                        print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
                        print('RAW INCOMING :')
                        print(bytes_str)
                        print('END RAW')
                        print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
                elif "HTTP/1.1" in first:  # (bytes_str != 0) and
                    response = self.response_from_bytes(bytes_str[len(self.cmd_prefix):])
                    incoming = response.data.decode("utf-8")
                    try:
                        await self.parse_response(incoming)
                    except:
                        print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
                        print('RAW INCOMING :')
                        print(bytes_str)
                        print('END RAW')
                        print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
                else:
                    print("Didn't detect incoming type, here it is :")
                    print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
                    print('RAW INCOMING :')
                    print(bytes_str)
                    print('END RAW')
                    print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")

            except Exception as e:
                print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
                print('receiveMessage error')
                print('RAW :')
                print(bytes_str)
                print("Incoming payload :")
                print(incoming)
                print("Error :")
                print(e)
                print('Exiting to ensure systemd restart....')
                sys.exit()  # Exit all to ensure systemd restart

    # Basic response parsing. Typically GET responses + instanciate covers and alarm class for updating data
    async def parse_response(self, incoming):
        data = incoming
        msg_type = None

        first = str(data[:40])
        # Detect type of incoming data
        if data != '':
            if "id_catalog" in data:  # search for id_catalog in all data to be sure to get configuration detected
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
                # print(data)
            else:
                print('Incoming message type : no type detected')
                print(data)

            if not (msg_type is None):
                try:
                    if msg_type == 'msg_config':
                        parsed = json.loads(data)
                        # print(parsed)
                        await self.parse_config_data(parsed=parsed)

                    elif msg_type == 'msg_data':
                        parsed = json.loads(data)
                        # print(parsed)
                        await self.parse_devices_data(parsed=parsed)
                    elif msg_type == 'msg_html':
                        print("HTML Response ?")
                    elif msg_type == 'msg_info':
                        pass
                    else:
                        # Default json dump
                        print()
                        print(json.dumps(parsed, sort_keys=True, indent=4, separators=(',', ': ')))
                except Exception as e:
                    print('Cannot parse response !')
                    # print('Response :')
                    # print(data)
                    if (e != 'Expecting value: line 1 column 1 (char 0)'):
                        print("Error : ", e)
                        print(parsed)
            print('Incoming data parsed successfully !')
            return(0)

    async def is_shutter(self, type):
        return type in ['shutter', 'klineShutter']

    async def is_light(self, type):
        return type == 'light'

    async def is_boiler(self, type):
        return type == 'boiler'

    async def is_consumption(self, type):
        return type == 'conso'

    async def is_window(self, type):
        return type in ['window', 'windowFrench', 'klineWindowFrench']

    async def is_door(self, type):
        return type in ['belmDoor', 'klineDoor']

    async def is_alarm(self, type):
        return type == 'alarm'

    async def is_electric(self, type):
        return type == 'electric'

    async def parse_config_data(self, parsed):
        for endpoint_info in parsed["endpoints"]:
            last_usage = endpoint_info["last_usage"]
            device_unique_id = str(endpoint_info["id_endpoint"]) + "_" + str(endpoint_info["id_device"])

            if self.is_shutter(type = last_usage) or self.is_light(type = last_usage) or self.is_window(type = last_usage)\
                    or self.is_door(type = last_usage) or self.is_boiler(type = last_usage) or self.is_consumption(type = last_usage):
                device_name_dict[device_unique_id] = endpoint_info["name"]
                device_type_dict[device_unique_id] = endpoint_info["last_usage"]
                device_endpoint_dict[device_unique_id] = endpoint_info["id_endpoint"]
            elif self.is_alarm(type = last_usage):
                device_name_dict[device_unique_id] = "Tyxal Alarm"
                device_type_dict[device_unique_id] = 'alarm'
                device_endpoint_dict[device_unique_id] = endpoint_info["id_endpoint"]
            elif self.is_electric(type = last_usage):
                device_name_dict[device_unique_id] = endpoint_info["name"]
                device_type_dict[device_unique_id] = 'boiler'
                device_endpoint_dict[device_unique_id] = endpoint_info["id_endpoint"]

        print('Configuration updated')

    async def parse_light_endpoint(self, endpoint_id, device_id, endpoint, friendly_name):
        attr_light = {}

        for endpoint_attributes in endpoint["data"]:
            if endpoint_attributes["name"] in DEVICE_LIGHT_KEYWORDS and endpoint_attributes["validity"] == 'upToDate':
                attr_light['device_id'] = device_id
                attr_light['endpoint_id'] = endpoint_id
                attr_light['id'] = str(device_id) + '_' + str(endpoint_id)
                attr_light['light_name'] = friendly_name
                attr_light['name'] = friendly_name
                attr_light['device_type'] = 'light'
                attr_light[endpoint_attributes["name"]] = endpoint_attributes["value"]

        return attr_light

    async def parse_cover_endpoint(self, endpoint_id, device_id, endpoint, friendly_name):
        attr_cover = {}

        for endpoint_attributes in endpoint["data"]:
            if endpoint_attributes["name"] in DEVICE_COVER_KEYWORDS and endpoint_attributes["validity"] == 'upToDate':
                attr_cover['device_id'] = device_id
                attr_cover['endpoint_id'] = endpoint_id
                attr_cover['id'] = str(device_id) + '_' + str(endpoint_id)
                attr_cover['cover_name'] = friendly_name
                attr_cover['name'] = friendly_name
                attr_cover['device_type'] = 'cover'
                attr_cover[endpoint_attributes["name"]] = endpoint_attributes["value"]
                print("Ajoute shutter {}".format(endpoint_attributes["name"]))

        return attr_cover

    async def parse_door_endpoint(self, endpoint_id, device_id, endpoint, friendly_name):
        attr_door = {}

        for endpoint_attributes in endpoint["data"]:
            if endpoint_attributes["name"] in DEVICE_DOOR_KEYWORDS and endpoint_attributes["validity"] == 'upToDate':
                attr_door['device_id'] = device_id
                attr_door['endpoint_id'] = endpoint_id
                attr_door['id'] = str(device_id) + '_'+str(endpoint_id)
                attr_door['door_name'] = friendly_name
                attr_door['name'] = friendly_name
                attr_door['device_type'] = 'sensor'
                attr_door[endpoint_attributes["name"]] = endpoint_attributes["value"]
                print("Ajoute door {}".format(endpoint_attributes["name"]))

        return attr_door

    async def parse_window_endpoint(self, endpoint_id, device_id, endpoint, friendly_name):
        attr_window = {}

        for endpoint_attributes in endpoint["data"]:
            if endpoint_attributes["name"] in DEVICE_DOOR_KEYWORDS and endpoint_attributes["validity"] == 'upToDate':
                attr_window['device_id'] = device_id
                attr_window['endpoint_id'] = endpoint_id
                attr_window['id'] = str(device_id) + '_' + str(endpoint_id)
                attr_window['door_name'] = friendly_name
                attr_window['name'] = friendly_name
                attr_window['device_type'] = 'sensor'
                attr_window[endpoint_attributes["name"]] = endpoint_attributes["value"]

        return attr_window

    async def parse_boiler_endpoint(self, endpoint_id, device_id, endpoint, friendly_name):
        attr_boiler = {}

        for endpoint_attributes in endpoint["data"]:
            if endpoint_attributes["name"] in DEVICE_BOILER_KEYWORDS and endpoint_attributes["validity"] == 'upToDate':
                attr_boiler['device_id'] = device_id
                attr_boiler['endpoint_id'] = endpoint_id
                attr_boiler['id'] = str(device_id) + '_' + str(endpoint_id)
                # attr_boiler['boiler_name'] = friendly_name
                attr_boiler['name'] = friendly_name
                attr_boiler['device_type'] = 'climate'
                attr_boiler[endpoint_attributes["name"]] = endpoint_attributes["value"]

        return attr_boiler

    async def parse_alarm_endpoint(self, endpoint_id, device_id, endpoint):
        attr_alarm = {}

        for endpoint_attributes in endpoint["data"]:
            if endpoint_attributes["name"] in DEVICE_ALARM_KEYWORDS and endpoint_attributes["validity"] == 'upToDate':
                attr_alarm['device_id'] = device_id
                attr_alarm['endpoint_id'] = endpoint_id
                attr_alarm['id'] = str(device_id) + '_' + str(endpoint_id)
                attr_alarm['alarm_name'] = "Tyxal Alarm"
                attr_alarm['name'] = "Tyxal Alarm"
                attr_alarm['device_type'] = 'alarm_control_panel'
                attr_alarm[endpoint_attributes["name"]] = endpoint_attributes["value"]

        return attr_alarm

    async def parse_consumption_endpoint(self, endpoint_id, device_id, endpoint, friendly_name):
        attr_consumption = {}

        for endpoint_attributes in endpoint["data"]:
            if endpoint_attributes["name"] in DEVICE_CONSUMPTION_KEYWORDS and endpoint_attributes["validity"] == "upToDate":
                attr_consumption = {
                    'device_id': device_id,
                    'endpoint_id': endpoint_id,
                    'id': str(device_id) + '_' + str(endpoint_id),
                    'name': friendly_name,
                    'device_type': 'sensor',
                    endpoint_attributes["name"]: endpoint_attributes["value"]
                }

                if endpoint_attributes["name"] in DEVICE_CONSUMPTION_CLASSES:
                    attr_consumption['device_class'] = DEVICE_CONSUMPTION_CLASSES[endpoint_attributes["name"]]

                if endpoint_attributes["name"] in DEVICE_CONSUMPTION_UNIT_OF_MEASUREMENT:
                    attr_consumption['unit_of_measurement'] = DEVICE_CONSUMPTION_UNIT_OF_MEASUREMENT[endpoint_attributes["name"]]

                new_consumption = Sensor(elem_name=endpoint_attributes["name"], tydom_attributes_payload=attr_consumption, attributes_topic_from_device='useless', mqtt=self.mqtt_client)
                await new_consumption.update()

        return attr_consumption

    async def parse_endpoint(self, device_id, endpoint):
        attr_light = {}
        attr_cover = {}
        attr_door ={}
        attr_window ={}
        attr_boiler = {}
        attr_alarm = {}
        attr_consumption = {}

        try:
            endpoint_id = endpoint["id"]
            unique_id = str(endpoint_id) + "_" + str(device_id)
            name_of_id = self.get_name_from_id(unique_id)
            type_of_id = self.get_type_from_id(unique_id)
            print("Traite endpoint {}, device {} (type {})".format(endpoint_id, device_id, type_of_id))

            friendly_name = device_id
            if len(name_of_id) != 0:
                friendly_name = name_of_id

            if self.is_light(type = type_of_id):
                attr_light = await self.parse_light_endpoint(endpoint_id, device_id, endpoint, friendly_name)
            elif self.is_shutter(type = type_of_id):
                attr_cover = await self.parse_cover_endpoint(endpoint_id, device_id, endpoint, friendly_name)
            elif self.is_door(type = type_of_id):
                attr_door = await self.parse_door_endpoint(endpoint_id, device_id, endpoint, friendly_name)
            elif self.is_window(type = type_of_id):
                attr_window = await self.parse_window_endpoint(endpoint_id, device_id, endpoint, friendly_name)
            elif self.is_boiler(type = type_of_id):
                attr_boiler = await self.parse_boiler_endpoint(endpoint_id, device_id, endpoint, friendly_name)
            elif self.is_alarm(type = type_of_id):
                attr_alarm = await self.parse_alarm_endpoint(endpoint_id, device_id, endpoint)
            elif self.is_consumption(type = type_of_id):
                attr_consumption = await self.parse_consumption_endpoint(endpoint_id, device_id, endpoint, friendly_name)
        except Exception as e:
            print('msg_data error in parsing !')
            print(e)

        if 'device_type' in attr_cover and attr_cover['device_type'] == 'cover':
            new_cover = Cover(tydom_attributes=attr_cover, mqtt=self.mqtt_client)
            await new_cover.update()
        elif 'device_type' in attr_door and attr_door['device_type'] == 'sensor':
            new_door = Sensor(elem_name='openState', tydom_attributes_payload=attr_door, attributes_topic_from_device='useless', mqtt=self.mqtt_client)
            await new_door.update()
        elif 'device_type' in attr_window and attr_window['device_type'] == 'sensor':
            new_window = Sensor(elem_name='openState', tydom_attributes_payload=attr_window, attributes_topic_from_device='useless', mqtt=self.mqtt_client)
            await new_window.update()
        elif 'device_type' in attr_light and attr_light['device_type'] == 'light':
            new_light = Light(tydom_attributes=attr_light, mqtt=self.mqtt_client)
            await new_light.update()
        elif 'device_type' in attr_boiler and attr_boiler['device_type'] == 'climate':
            new_boiler = Boiler(tydom_attributes=attr_boiler, tydom_client=self.tydom_client, mqtt=self.mqtt_client)
            await new_boiler.update()
        elif 'device_type' in attr_alarm and attr_alarm['device_type'] == 'alarm_control_panel':
            state = None
            sos_state = False
            maintenance_mode = False
            out = None
            try:
                # {
                # "name": "alarmState",
                # "type": "string",
                # "permission": "r",
                # "enum_values": ["OFF", "DELAYED", "ON", "QUIET"]
                # },
                # {
                # "name": "alarmMode",
                # "type": "string",
                # "permission": "r",
                # "enum_values": ["OFF", "ON", "TEST", "ZONE", "MAINTENANCE"]
                # }

                if ('alarmState' in attr_alarm and attr_alarm['alarmState'] == "ON") or ('alarmState' in attr_alarm and attr_alarm['alarmState']) == "QUIET":
                    state = "triggered"

                elif 'alarmState' in attr_alarm and attr_alarm['alarmState'] == "DELAYED":
                    state = "pending"

                if 'alarmSOS' in attr_alarm and attr_alarm['alarmSOS'] == "true":
                    state = "triggered"
                    sos_state = True

                elif 'alarmMode' in attr_alarm and attr_alarm ["alarmMode"]  == "ON":
                    state = "armed_away"
                elif 'alarmMode' in attr_alarm and attr_alarm["alarmMode"]  == "ZONE":
                    state = "armed_home"
                elif 'alarmMode' in attr_alarm and attr_alarm["alarmMode"]  == "OFF":
                    state = "disarmed"
                elif 'alarmMode' in attr_alarm and attr_alarm["alarmMode"]  == "MAINTENANCE":
                    maintenance_mode = True
                    state = "disarmed"

                if 'outTemperature' in attr_alarm:
                    out = attr_alarm["outTemperature"]

                if sos_state:
                    print("SOS !")

                if not (state is None):
                    alarm = Alarm(current_state=state, tydom_attributes=attr_alarm, mqtt=self.mqtt_client)
                    await alarm.update()

            except Exception as e:
                print("Error in alarm parsing !")
                print(e)
                pass
        else:
            pass

    async def parse_devices_data(self, parsed):
        for i in parsed:
            for endpoint in i["endpoints"]:
                if endpoint["error"] == 0 and len(endpoint["data"]) > 0:
                    await self.parse_endpoint(device_id = i["id"], endpoint = endpoint)

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

    ######### FUNCTIONS

    def response_from_bytes(self, data):
        sock = BytesIOSocket(data)
        response = HTTPResponse(sock)
        response.begin()
        return urllib3.HTTPResponse.from_httplib(response)

    def put_response_from_bytes(self, data):
        request = HTTPRequest(data)
        return request

    def get_type_from_id(self, id):
        deviceType = ""
        if len(device_type_dict) != 0 and id in device_type_dict.keys():
            deviceType = device_type_dict[id]
        else:
            print('{} not in dic device_type'.format(id))

        return(deviceType)

    # Get pretty name for a device id
    def get_name_from_id(self, id):
        name = ""
        if len(device_name_dict) != 0 and id in device_name_dict.keys():
            name = device_name_dict[id]
        else:
            print('{} not in dic device_name'.format(id))
        return name


class BytesIOSocket:
    def __init__(self, content):
        self.handle = BytesIO(content)

    def makefile(self, mode):
        return self.handle

class HTTPRequest(BaseHTTPRequestHandler):
    def __init__(self, request_text):
        #self.rfile = StringIO(request_text)
        self.raw_requestline = request_text
        self.error_code = self.error_message = None
        self.parse_request()

    def send_error(self, code, message):
        self.error_code = code
        self.error_message = message
