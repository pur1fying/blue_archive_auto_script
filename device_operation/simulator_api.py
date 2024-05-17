from .device_config import device_config, load_data
from .get_adb_address import get_simulator_port


### simulator apis ###

def get_adb_address(simulator_type, multi_instance=None):
    if simulator_type:
        return get_simulator_port(simulator_type, multi_instance)
    else:
        raise ValueError("MISSING_INPUT_PARAMETER")


def get_adb_address_by_uuid(uuid):
    data = load_data(uuid)
    if data is not None:
        return data['latest_adb_address']


def get_simulator_uuid(simulator_type, multi_instance=None):
    return device_config(simulator_type, multi_instance)


def get_simulator_commandline_uuid(uuid):
    try:
        return load_data(uuid)[3]
    except:
        raise FileNotFoundError('simulators not founded')

### End simulator apis ###
