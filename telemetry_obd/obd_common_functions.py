"""telemetry_obd/common.py: Common functions."""
from pathlib import Path
from typing import List
from datetime import datetime, timezone
import configparser
import obd
from .add_commands import NEW_COMMANDS


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

    # return str(bytes(version_response.value), 'utf-8'), str(bytes(voltage_response.value), 'utf-8')
    return str(version_response.value), str(voltage_response.value)

def get_directory(base_path, vin):
    """Generate directory where data files go."""
    # print("base_path", base_path, "vin", vin)
    path = Path(base_path) / Path(str(vin))
    path.mkdir(parents=True, exist_ok=True)
    return path

def get_config_path(base_path, vin):
    """Return path to settings file."""
    path = Path(str(vin) + '.ini')
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

def get_output_file_name(vin):
    """Create an output file name."""
    dt_now = datetime.now(tz=timezone.utc).strftime("%Y%m%d%H%M%S")
    return Path(f"{vin}-{dt_now}-utc.json")

def load_custom_commands(connection):
    """Load custom commands into a dictionary."""
    local_commands = {}
    for new_command in NEW_COMMANDS:
        if connection:
            connection.supported_commands.add(new_command)
        local_commands[new_command.name] = new_command
    return local_commands
