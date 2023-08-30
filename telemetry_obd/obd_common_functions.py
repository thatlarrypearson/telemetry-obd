"""telemetry_obd/common.py: Common functions."""

from time import sleep
from pathlib import Path
from typing import List
from datetime import datetime, timezone
import logging
import configparser
import obd
from pint import UnitRegistry
from obd.utils import BitArray
from obd.codes import BASE_TESTS
from obd.OBDResponse import Status
from .add_commands import NEW_COMMANDS, ureg

logger = logging.getLogger(__name__)

CONNECTION_WAIT_DELAY = 15.0
CONNECTION_RETRY_COUNT = 5

local_commands = {
    new_command.name: new_command for new_command in NEW_COMMANDS
}

OBD_ERROR_MESSAGES = {
    "ACT ALERT": "OBD adapter switching to low power mode in 1 minute.",
    "BUFFER FULL": "Incoming OBD message buffer overflow.",
    "BUS BUSY": "Send timeout occurred before bus became idle.",
    "BUS ERROR": "Potential OBD adapter to vehicle OBD interface circuit problem.",
    "CAN ERROR": "OBD adapter having trouble transmitting or receiving messages",
    ">DATA ERROR": "CRC/checksum error.",
    "DATA ERROR": "Data formatting error.",
    "FB ERROR": "Feedback error.  Circuit problem?",
    "FC RX TIMEOUT": "Timeout error.  Circuit problem?",
    "LP ALERT": "Low power alert.  Standby mode in 2 seconds.",
    "LV RESET": "Low voltage reset.  Vehicle power brownout condition?",
    "NO DATA": "No vehicle response before read timeout.  Command not supported?",
    "OUT OF MEMORY": "Not enough RAM in adapter to complete operation.",
    "RX ERROR": "Received message garbled.  Incorrect baud rate?",
    "STOPPED": "Adapter received character on UART interrupting current OBD command.",
    "UART RX OVERFLOW": "UART receive buffer overflow.",
    "UNABLE TO CONNECT": "OBD adapter unable to detect supported vehicle OBD protocol.",
}

class CommandNameGenerator():
    """Iterator for providing a never ending list of OBD commands."""

    # Three different cycles for running commands
    startup_names: List[str] = []
    startup = None
    housekeeping_names: List[str] = []
    housekeeping = None
    cycle_names: List[str] = []
    cycle = None
    full_cycles_count = 0

    def __init__(self, settings_file: str):
        """Init function."""
        self.settings_file = settings_file
        self.load_names()

    def load_names(self):
        """Load three sets of OBD command names."""
        config = configparser.ConfigParser()
        config.read(self.settings_file)
        self.startup_names = (config['STARTUP NAMES']['startup']).split()
        self.startup = self.startup_names.__iter__()

        self.housekeeping_names = (
                (config['HOUSEKEEPING NAMES']['housekeeping']).split()
        )
        self.housekeeping = self.housekeeping_names.__iter__()

        self.cycle_names = (config['CYCLE NAMES']['cycle']).split()
        self.cycle = self.cycle_names.__iter__()

    def __iter__(self):
        """Start iterator."""
        return self

    def __next__(self):
        """Get the next iterable."""
        if self.startup:
            try:
                return self.startup.__next__()
            except StopIteration:
                self.startup = None

        if self.cycle:
            try:
                return self.cycle.__next__()
            except StopIteration:
                self.cycle = None

        if not self.housekeeping:
            self.housekeeping = self.housekeeping_names.__iter__()

        self.cycle = self.cycle_names.__iter__()

        try:
            return self.housekeeping.__next__()
        except StopIteration:
            self.housekeeping = None
            self.full_cycles_count += 1

        return self.__next__()


def get_vin_from_vehicle(connection):
    """Get Vehicle Information Number (VIN) from vehicle."""
    obd_response = connection.query(obd.commands["VIN"])

    if obd_response and obd_response.value:
        return str(bytes(obd_response.value), 'utf-8')

    return 'UNKNOWN_VIN'

def get_elm_info(connection):
    """Return ELM version and voltage"""
    version_response = connection.query(obd.commands["ELM_VERSION"])
    voltage_response = connection.query(obd.commands["ELM_VOLTAGE"])

    return str(version_response.value), str(voltage_response.value)

def get_directory(base_path:str, vin:str) -> Path:
    """Generate directory where data files go."""
    path = Path(base_path) / Path(vin)
    path.mkdir(parents=True, exist_ok=True)
    return path

def get_config_path(base_path:str, vin:str) -> Path:
    """Return path to settings file."""
    path = Path(f"{vin}.ini")
    if path.is_file():
        return path

    path = Path(base_path) / path
    if path.is_file():
        return path

    path = Path('default.ini')
    if path.is_file():
        return path

    path = Path(base_path) / path
    if path.is_file():
        return path

    raise ValueError(f"no default.ini or {vin}.ini available")

def get_counter_value(base_path:str, vin:str)->int:
    # get the counter value (integer) held in the hidden file
    # f"{base_path}/.{vin}-counter_value.txt"
    path = Path(base_path) / Path(f".{vin}-counter_value.txt")
    if path.is_file():
        with open(path,"r") as counter_file:
            counter_value = int(counter_file.read())
    else:
        counter_value = 0

    return counter_value

def save_counter_value(base_path:str, vin:str, counter_value:int):
    # save the counter value (integer) as a string held in the hidden file
    # f"{base_path}/.{vin}-counter_value.txt"
    path = Path(base_path) / Path(f".{vin}-counter_value.txt")
    with open(path, 'w') as counter_file:
        counter_file.write(str(counter_value))
    return

def get_output_file_name(base_path:str, vin:str, output_file_name_counter=False) -> Path:
    """Create output file name."""
    if output_file_name_counter:
        counter_value = get_counter_value(base_path, vin)
        counter_value += 1
        save_counter_value(base_path, vin, counter_value)
        counter_string = (f"{counter_value:10d}").replace(' ', '0')
        return Path(f"{vin}-{counter_string}.json")

    dt_now = datetime.now(tz=timezone.utc).strftime("%Y%m%d%H%M%S")
    return Path(f"{vin}-{dt_now}-utc.json")

def load_custom_commands(connection):
    """Load custom commands into a dictionary."""
    custom_commands = {}
    for new_command in NEW_COMMANDS:
        logging.info(f"load_custom_commands(): {new_command.name}")
        if connection:
            connection.supported_commands.add(new_command)
        custom_commands[new_command.name] = new_command
    return custom_commands

def tuple_to_list_converter(t:tuple)->list:
    """
    Converts python-OBD/OBD/OBDCommand.py OBDCommand tuple output to list output.
    For example, O2_SENSORS value: "((), (False, False, False, False), (False, False, False, True))"
    gets converted to [False, False, False, False, False, False, False, True]
    """
    return_value = []
    for item in t:
        if isinstance(item, tuple) and len(item) == 0:
            continue
        elif isinstance(item, tuple):
            return_value += tuple_to_list_converter(item)
        elif isinstance(item, BitArray):
            for b in item:
                return_value.append(b)
        else:
            return_value.append(item)

    return return_value

def list_cleaner(command_name:str, items:list)->list:
    return_value = []
    for item in items:
        if (
            isinstance(item, ureg.Quantity) or
            isinstance(item, bytearray)
        ):
            return_value.append(str(item))
        elif 'Quantity' in item.__class__.__name__:
            return_value.append(str(item))
        else:
            return_value.append(item)
    return return_value

def clean_obd_query_response(command_name:str, obd_response):
    """
    fixes problems in OBD connection.query responses.
    - is_null() True to "no response"
    - tuples to lists
    - bytearrays to strings
    - "NO DATA", "CAN ERROR", etc. to "no response"
    - None to "no response"
    - BitArray to list of True/False values
    - Status to serialized version of Status
    - pint Quantity object serialized by pint.
    """
    if not obd_response:
        logging.debug(f"command_name {command_name}: obd_response is None")
        return None

    if obd_response.is_null() or obd_response.value is None:
        logging.debug(f"command_name {command_name}: obd_response.is_null or obd_response.value is None")
        return "no response"

    for message in obd_response.messages:
        for obd_error_message, obd_error_description in OBD_ERROR_MESSAGES.items():
            raw_message = message.raw()
            if obd_error_message in raw_message:
                logging.error(f"command_name: {command_name}: OBD adapter message error: \"{obd_error_message}\": {obd_error_description}")
                return "no response"

    if isinstance(obd_response.value, bytearray):
        return obd_response.value.decode("utf-8")

    if isinstance(obd_response.value, BitArray):
        return list(obd_response.value)

    if isinstance(obd_response.value, Status):
        return [
            str(obd_response.value.__dict__[base_test])
            for base_test in BASE_TESTS
        ]

    if isinstance(obd_response.value, ureg.Quantity) or 'Quantity' in obd_response.value.__class__.__name__:
        return str(obd_response.value)

    if isinstance(obd_response.value, list):
        return list_cleaner(command_name, obd_response.value)

    if isinstance(obd_response.value, tuple):
        return tuple_to_list_converter(obd_response.value)

    return obd_response.value

def get_obd_connection(fast:bool, timeout:float)->obd.OBD:
    """
    return an OBD connection instance that connects to the first ELM 327 compatible device
    connected to any of the local serial ports.  If no device found, exit program with error code 1.
    """
    ports = sorted(obd.scan_serial())

    logging.info(f"identified ports {ports}")

    for port in ports:
        logging.info(f"connecting to port {port}")

        try:

            # OBD(portstr=None, baudrate=None, protocol=None, fast=True, timeout=0.1, check_voltage=True)
            connection = obd.OBD(portstr=port, fast=fast, timeout=timeout)
            for t in range(1, CONNECTION_RETRY_COUNT):

                if connection.is_connected():
                    logging.info(f"connected to {port} on try {t} of {CONNECTION_RETRY_COUNT}")
                    custom_commands = load_custom_commands(connection)
                    return connection

                if connection.status() == obd.OBDStatus.NOT_CONNECTED:
                    logging.warn(f"ELM 327 Adapter Not Found on {port}on try {t} of {CONNECTION_RETRY_COUNT}")
                    break

                logging.info(f"Waiting for OBD Connection on {port} on try {t} of {CONNECTION_RETRY_COUNT}: {connection.status()}")

                sleep(CONNECTION_WAIT_DELAY)

        except Exception as e:
            logging.exception(f"OBD Connection on port {port} unavailable.  Exception: {e}")

    logging.info(f"ELM 327 type device not found in devices: {ports}")
    logging.info("exiting...")

    exit(1)

def recover_lost_connection(connection:obd.OBD, fast:bool, timeout:float)->obd.OBD:
    """
    Recover lost connection and return a new working connection handle.
    """
    logging.info("recovering lost connection")
    connection.close()
    sleep(CONNECTION_WAIT_DELAY)
    connection = get_obd_connection(fast=fast, timeout=timeout)

    return connection

def execute_obd_command(connection:obd.OBD, command_name:str):
    """
    executes OBD interface query given command_name on OBD connection.
    returns list or value
    """
    if obd.commands.has_name(command_name):
        obd_response = connection.query(obd.commands[command_name], force=True)

    elif command_name in local_commands:
        obd_response = connection.query(local_commands[command_name], force=True)
    else:
        # raise LookupError(f"command <{command_name}> missing from python-obd and custom commands")
        logging.warn(f"LookupError: config file has command name <{command_name}> that doesn't exist")
        return None

    return obd_response

try:
    # Not making UltraDict a requirement.
    from UltraDict import UltraDict

    class SharedDictionaryManager(UltraDict):
        """
        Shared Dictionary Manager - Uses a dictionary as the shared memory metaphor.
        Supports multiple instances within single process so long as 'name'
        is distinct for each instance.  This is not enforced as this class doesn't
        use the singleton pattern.
        Different processes can share the same shared memory/dictionary so long as they use the
        same value for the 'name' constructor variable.
        Code assumes there is only one writer and one or more readers for each memory region.  If more
        more than one writer is needed, create multiple instances, one for each writer.
        """
        def __init__(self, name:str):
            """
            SharedDictionaryManager constructor
            arguments
                name
                    name of the shared memory/dictionary region
            """
            # UltraDict(*arg, name=None, buffer_size=10000, serializer=pickle, shared_lock=False, full_dump_size=None, auto_unlink=True, recurse=False, **kwargs)
            super().__init__(
                name=name,
                buffer_size=1048576,    # 1 MB
                shared_lock=True,       # enabling multiple writers on shared memory/dictionary
                full_dump_size=None,    # change this value to buffer_size or larger for Windows machines
                auto_unlink=False,      # once created, shared memory/dictionary persists on process exit
                recurse=False           # dictionary can contain dictionary but updates not nested
            )
    
    default_shared_gps_command_list = [
        "NMEA_GNGNS",       # Fix data
        "NMEA_GNGST",       # Pseudorange error statistics
        "NMEA_GNVTG",       # Course over ground and ground speed
        "NMEA_GNZDA",       # Time and data
    ]

    default_shared_weather_command_list = [
        "WTHR_rapid_wind",
        "WTHR_hub_status",
        "WTHR_device_status",
        "WTHR_obs_st",
        "WTHR_evt_precip",
    ]

    def shared_dictionary_to_dictionary(shared_dictionary:UltraDict)->dict:
        # sourcery skip: assign-if-exp, dict-comprehension
        """
        Convert UltraDict item to a real dictionary
        so that the return value will work in json.dumps functions
        """
        logging.info(f"shared_dictionary type {type(shared_dictionary)}")

        if 'UltraDict' not in str(type(shared_dictionary)):
            return shared_dictionary
 
        return_value = {}
        
        for key, value in shared_dictionary.items():
            logging.info(f"key {key} value type {type(value)}")
            if 'UltraDict' in str(type(shared_dictionary)):
                return_value[key] = shared_dictionary_to_dictionary(value)
            else:
                return_value[key] = value
        
        return return_value

except ImportError:
    SharedDictionaryManager = None
    default_shared_gps_command_list = None
    default_shared_weather_command_list = None

    def shared_dictionary_to_dictionary(shared_dictionary:dict)->dict:
        return shared_dictionary
