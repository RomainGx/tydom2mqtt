def is_shutter(device_type):
    return device_type in ['shutter', 'klineShutter']


def is_light(device_type):
    return device_type == 'light'


def is_boiler(device_type):
    return device_type == 'boiler'


def is_consumption(device_type):
    return device_type == 'conso'


def is_dvi(device_type):
    return device_type == 'klineWindowSliding'


def is_window(device_type):
    return device_type in ['window', 'windowFrench', 'klineWindowFrench']


def is_door(device_type):
    return device_type in ['belmDoor', 'klineDoor']


def is_alarm(device_type):
    return device_type == 'alarm'


def is_electric(device_type):
    return device_type == 'electric'


def get_device_info(device_name, device_id, model=None):
    device = {
        'manufacturer': 'Delta Dore',
        'name': device_name,
        'identifiers': device_id
    }
    if model is not None:
        device['model'] = model
    return device
