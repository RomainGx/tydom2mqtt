def is_shutter(device_type):
    return device_type in ['shutter', 'klineShutter']


def is_light(device_type):
    return device_type == 'light'


def is_boiler(device_type):
    return device_type == 'boiler'


def is_consumption(device_type):
    return device_type == 'conso'


def is_window(device_type):
    return device_type in ['window', 'windowFrench', 'klineWindowFrench']


def is_door(device_type):
    return device_type in ['belmDoor', 'klineDoor']


def is_alarm(device_type):
    return device_type == 'alarm'


def is_electric(device_type):
    return device_type == 'electric'