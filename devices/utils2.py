from sensors import Sensor


async def create_and_update_sensor(mqtt_client, device_id, endpoint_id, friendly_name, all_attributes, keywords):
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
            new_sensor = Sensor(attribute_name, sensor_attributes, mqtt_client)
            await new_sensor.update()
