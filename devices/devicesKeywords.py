ALARM = ['alarmMode', 'alarmState', 'alarmSOS', 'zone1State', 'zone2State', 'zone3State', 'zone4State', 'zone5State', 'zone6State', 'zone7State', 'zone8State', 'gsmLevel', 'inactiveProduct', 'zone1State', 'liveCheckRunning', 'networkDefect', 'unitAutoProtect', 'unitBatteryDefect', 'unackedEvent', 'alarmTechnical', 'systAutoProtect', 'sysBatteryDefect', 'zsystSupervisionDefect', 'systOpenIssue', 'systTechnicalDefect', 'videoLinkDefect', 'outTemperature']
ALARM_DETAILS = ['alarmSOS', 'zone1State', 'zone2State', 'zone3State', 'zone4State', 'zone5State', 'zone6State', 'zone7State', 'zone8State', 'gsmLevel', 'inactiveProduct', 'zone1State', 'liveCheckRunning', 'networkDefect', 'unitAutoProtect', 'unitBatteryDefect', 'unackedEvent', 'alarmTechnical', 'systAutoProtect', 'sysBatteryDefect', 'zsystSupervisionDefect', 'systOpenIssue', 'systTechnicalDefect', 'videoLinkDefect', 'outTemperature']

LIGHT = ['level', 'onFavPos', 'thermicDefect', 'battDefect', 'loadDefect', 'cmdDefect', 'onPresenceDetected', 'onDusk']
LIGHT_DETAILS = ['onFavPos', 'thermicDefect', 'battDefect', 'loadDefect', 'cmdDefect', 'onPresenceDetected', 'onDusk']

DOOR = ['openState', 'intrusionDetect']
DOOR_DETAILS = ['onFavPos', 'thermicDefect', 'obstacleDefect', 'intrusion', 'battDefect']

COVER = ['position', 'onFavPos', 'thermicDefect', 'obstacleDefect', 'intrusion', 'battDefect']
COVER_DETAILS = ['onFavPos', 'thermicDefect', 'obstacleDefect', 'intrusion', 'battDefect', 'position']

# CLIMATE_KEYWORDS = ['temperature', 'authorization', 'hvacMode', 'setpoint']

BOILER = [
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

CONSUMPTION_CLASSES = {
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

CONSUMPTION_UNITS = {
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
CONSUMPTION = CONSUMPTION_CLASSES.keys()
