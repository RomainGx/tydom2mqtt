from devices import devicesKeywords


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
        if endpoint_attributes["name"] in devicesKeywords.DOOR.keys() and endpoint_attributes["validity"] == 'upToDate':
            door_attributes[endpoint_attributes["name"]] = endpoint_attributes["value"]

    return door_attributes


def parse_window_endpoint(endpoint):
    window_attributes = {}

    for endpoint_attributes in endpoint["data"]:
        if endpoint_attributes["name"] in devicesKeywords.WINDOW.keys() and endpoint_attributes["validity"] == 'upToDate':
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
