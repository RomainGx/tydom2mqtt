from devices import devicesKeywords
from devices.utils import is_shutter, is_light, is_window, is_door, is_boiler, is_consumption, is_alarm, is_electric
from tydomMessagehandler import device_name_dict, device_type_dict, device_endpoint_dict


def parse_light_endpoint(endpoint):
    light_attributes = {}

    for endpoint_attributes in endpoint["data"]:
        if endpoint_attributes["name"] in devicesKeywords.LIGHT and endpoint_attributes["validity"] == 'upToDate':
            light_attributes[endpoint_attributes["name"]] = endpoint_attributes["value"]

    return light_attributes


def parse_cover_endpoint(endpoint):
    covers_attributes = {}

    for endpoint_attributes in endpoint["data"]:
        if endpoint_attributes["name"] in devicesKeywords.COVER and endpoint_attributes["validity"] == 'upToDate':
            covers_attributes[endpoint_attributes["name"]] = endpoint_attributes["value"]

    return covers_attributes


def parse_door_endpoint(endpoint):
    door_attributes = {}

    for endpoint_attributes in endpoint["data"]:
        if endpoint_attributes["name"] in devicesKeywords.DOOR and endpoint_attributes["validity"] == 'upToDate':
            door_attributes[endpoint_attributes["name"]] = endpoint_attributes["value"]

    return door_attributes


def parse_window_endpoint(endpoint):
    window_attributes = {}

    for endpoint_attributes in endpoint["data"]:
        if endpoint_attributes["name"] in devicesKeywords.DOOR and endpoint_attributes["validity"] == 'upToDate':
            window_attributes[endpoint_attributes["name"]] = endpoint_attributes["value"]

    return window_attributes


def parse_boiler_endpoint(endpoint):
    boiler_attributes = {}

    for endpoint_attributes in endpoint["data"]:
        if endpoint_attributes["name"] in devicesKeywords.BOILER and endpoint_attributes["validity"] == 'upToDate':
            boiler_attributes[endpoint_attributes["name"]] = endpoint_attributes["value"]

    return boiler_attributes


def parse_alarm_endpoint(endpoint):
    alarm_attributes = {}

    for endpoint_attributes in endpoint["data"]:
        if endpoint_attributes["name"] in devicesKeywords.ALARM and endpoint_attributes["validity"] == 'upToDate':
            alarm_attributes[endpoint_attributes["name"]] = endpoint_attributes["value"]

    return alarm_attributes


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