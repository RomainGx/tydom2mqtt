import asyncio
import time
import json
import socket
import sys
import re
from datetime import datetime
from gmqtt import Client as MQTTClient
from cover import Cover
from alarm_control_panel import Alarm
from light import Light
from boiler import Boiler

TYDOM_TOPIC = "homeassistant/+/tydom/#"
REFRESH_TOPIC = "homeassistant/requests/tydom/refresh"
hostname = socket.gethostname()

# STOP = asyncio.Event()
def get_ids(topic):
    ids = re.search('.*_([0-9]+)_([0-9]+)', topic)
    return {
        "device_id": ids.group(1),
        "endpoint_id": ids.group(2)
    }


def get_value(payload):
    return str(payload).strip('b').strip("'")


class MqttHassio():
    def __init__(self, broker_host, port, user, password, mqtt_ssl, home_zone=1, night_zone=2, tydom = None, tydom_alarm_pin = None):
        self.broker_host = broker_host
        self.port = port
        self.user = user
        self.password = password
        self.ssl = mqtt_ssl
        self.tydom = tydom
        self.tydom_alarm_pin = tydom_alarm_pin
        self.mqtt_client = None
        self.home_zone = home_zone
        self.night_zone = night_zone

    async def connect(self):
        try:
            print('""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""')
            print('Attempting MQTT connection...')
            print('MQTT host : ', self.broker_host)
            print('MQTT user : ', self.user)
            address = hostname + str(datetime.fromtimestamp(time.time()))

            client = MQTTClient(address)

            client.on_connect = self.on_connect
            client.on_message = self.on_message
            client.on_disconnect = self.on_disconnect

            client.set_auth_credentials(self.user, self.password)
            await client.connect(self.broker_host, self.port, self.ssl)

            self.mqtt_client = client
            return self.mqtt_client
        except Exception as e:
            print("MQTT connection Error : ", e)
            print('MQTT error, restarting in 8s...')
            await asyncio.sleep(8)
            await self.connect()

    def on_connect(self, client, flags, rc, properties):
        print("##################################")
        try:
            print("Subscribing to : ", TYDOM_TOPIC)
            client.subscribe('homeassistant/status', qos=0)
            client.subscribe(TYDOM_TOPIC, qos=0)
        except Exception as e:
            print("Error on connect : ", e)

    async def on_message(self, client, topic, payload, qos, properties):
        print('Incoming MQTT message : ', topic, payload)
        if 'update' in str(topic):
            print('Incoming MQTT update request : ', topic, payload)
            await self.tydom.get_data()
        elif 'kill' in str(topic):
            print('Incoming MQTT kill request : ', topic, payload)
            print('Exiting...')
            sys.exit()
        elif topic == "homeassistant/requests/tydom/refresh":
            print('Incoming MQTT refresh request : ', topic, payload)
            await self.tydom.post_refresh()
        elif topic == "homeassistant/requests/tydom/scenarii":
            print('Incoming MQTT scenarii request : ', topic, payload)
            await self.tydom.get_scenarii()
        elif topic == "homeassistant/status" and payload.decode() == 'online':
            await self.tydom.get_devices_data()
        elif topic == "/tydom/init":
            print('Incoming MQTT init request : ', topic, payload)
            await self.tydom.connect()
        # elif ('set_scenario' in str(topic)):
        #     print('Incoming MQTT set_scenario request : ', topic, payload)
        #     get_id = (topic.split("/"))[3] #extract id from mqtt
        #     # print(tydom, str(get_id), 'position', json.loads(payload))
        #     if not self.tydom.connection.open:
        #         print('Websocket not opened, reconnect...')
        #         await self.tydom.connect()
        #         await self.tydom.put_devices_data(str(get_id), 'position', str(json.loads(payload)))
        #     else:
        #         await self.tydom.put_devices_data(str(get_id), 'position', str(json.loads(payload)))
        elif 'set_positionCmd' in str(topic):
            print('Incoming MQTT set_positionCmd request : ', topic, payload)
            value = get_value(payload)
            ids = get_ids(topic)
            print('positionCmd', value, ids)
            await Cover.put_positionCmd(tydom_client=self.tydom, device_id=ids["device_id"], cover_id=ids["endpoint_id"], positionCmd=str(value))
        elif ('set_position' in str(topic)) and not ('set_positionCmd'in str(topic)):
            print('Incoming MQTT set_position request : ', topic, json.loads(payload))
            value = json.loads(payload)
            ids = get_ids(topic)
            print('position', value, ids)
            await Cover.put_position(tydom_client=self.tydom, device_id=ids["device_id"], cover_id=ids["endpoint_id"], position=str(value))
        elif 'set_levelCmd' in str(topic):
            print('Incoming MQTT set_positionCmd request : ', topic, payload)
            value = get_value(payload)
            ids = get_ids(topic)
            print('levelCmd', value, ids["device_id"], ids["endpoint_id"])
            await Light.put_level_cmd(tydom_client=self.tydom, device_id=ids["device_id"], light_id=ids["endpoint_id"], level_cmd=str(value))
        elif ('set_level' in str(topic)) and not ('set_levelCmd' in str(topic)):
            print('Incoming MQTT set_position request : ', topic, json.loads(payload))
            value = json.loads(payload)
            ids = get_ids(topic)
            print('putLevel', value, ids["device_id"], ids["endpoint_id"])
            await Light.put_level(tydom_client=self.tydom, device_id=ids["device_id"], light_id=ids["endpoint_id"], level=str(value))
        elif ('set_alarm_state' in str(topic)) and not ('homeassistant'in str(topic)):
            command = get_value(payload)
            ids = get_ids(topic)
            print('put_alarm_state', ids["device_id"], ids["endpoint_id"])
            await Alarm.put_alarm_state(tydom_client=self.tydom, device_id=ids["device_id"], alarm_id=ids["endpoint_id"], asked_state=command, home_zone=self.home_zone, night_zone=self.night_zone)
        elif 'set_setpoint' in str(topic):
            value = json.loads(payload)
            print('Incoming MQTT setpoint request : ', topic, value)
            ids = get_ids(topic)
            print('put_temperature', value, ids["device_id"], ids["endpoint_id"])
            await Boiler.put_temperature(tydom_client=self.tydom, device_id=ids["device_id"], boiler_id=ids["endpoint_id"], set_setpoint=str(value))
        elif 'set_hvacMode' in str(topic):
            value = get_value(payload)
            print('Incoming MQTT set_hvacMode request : ', topic, value)
            ids = get_ids(topic)
            print('put_hvacMode', value, ids["device_id"], ids["endpoint_id"])
            await Boiler.put_hvac_mode(tydom_client=self.tydom, device_id=ids["device_id"], boiler_id=ids["endpoint_id"], set_hvac_mode=str(value))
        elif 'set_thermicLevel' in str(topic):
            value = get_value(payload)
            print('Incoming MQTT set_thermicLevel request : ', topic, value)
            ids = get_ids(topic)
            print('put_thermicLevel', value, ids["device_id"], ids["endpoint_id"])
            await Boiler.put_thermicLevel(tydom_client=self.tydom, device_id=ids["device_id"], boiler_id=ids["endpoint_id"], set_thermic_level=str(value))
        else:
            pass

    def on_disconnect(self, client, packet, exc=None):
        print('MQTT Disconnected !')
        print("##################################")
        # self.connect()

    def on_subscribe(self, client, mid, qos):
        print("MQTT is connected and suscribed ! =)", client)
        try:
            pyld = str(datetime.fromtimestamp(time.time()))
            client.publish('homeassistant/sensor/tydom/last_clean_startup', pyld, qos=1, retain=True)
        except Exception as e:
            print("on subscribe error : ", e)