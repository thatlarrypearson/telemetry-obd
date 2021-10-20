"""telemetry_obd/obd_logger.py: Onboard Diagnostic Data Logger."""

from time import sleep
from datetime import datetime, timezone
from pathlib import Path
from argparse import ArgumentParser
import sys
import json
import logging
import obd
from .obd_common_functions import (
    load_custom_commands,
    get_vin_from_vehicle,
    get_elm_info,
    get_config_path,
    CommandNameGenerator,
    get_directory,
    get_output_file_name
)

CONNECTION_WAIT_DELAY = 15.0
FULL_CYCLES_COUNT = 50
TIMEOUT=1.0

logger = logging.getLogger(__name__)

def argument_parsing()-> dict:
    """Argument parsing"""
    parser = ArgumentParser(description="Telemetry OBD Logger")
    parser.add_argument(
        "base_path",
        nargs='?',
        metavar="base_path",
        default=["data", ],
        help="Relative or absolute output data directory. Defaults to 'data'."
    )
    parser.add_argument(
        "--config_file",
        help="Settings file name. Defaults to '<vehicle-VIN>.ini' or 'default.ini'.",
        default=None
    )
    parser.add_argument(
        "--config_dir",
        help="Settings directory path. Defaults to './config'.",
        default='./config'
    )
    parser.add_argument(
        '--full_cycles',
        type=int,
        default=FULL_CYCLES_COUNT,
        help=(
            "The number of full cycles before a new output file is started." +
            f"  Default is {FULL_CYCLES_COUNT}."
        )
    )
    parser.add_argument(
        '--timeout',
        type=float,
        default=TIMEOUT,
        help=(
            "The number seconds before the current command times out." +
            f"  Default is {TIMEOUT} seconds."
        )
    )
    parser.add_argument(
        "--logging",
        help="Turn on logging in python-obd library. Default is off.",
        default=False,
        action='store_true'
    )
    parser.add_argument(
        "--no_fast",
        help="When on, commands for every request will be unaltered with potentially long timeouts " +
        "when the car doesn't respond promptly or at all. " +
        "When off (fast is on), commands are optimized before being sent to the car. A timeout is " + 
        "added at the end of the command.  Default is off. ",
        default=False,
        action='store_true'
    )
    parser.add_argument(
        "--verbose",
        help="Turn verbose output on. Default is off.",
        default=False,
        action='store_true'
    )
    return vars(parser.parse_args())

def main():
    """Run main function."""

    args = argument_parsing()

    if args['logging']:
        logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
        obd.logger.setLevel(obd.logging.DEBUG)

    fast = not args['no_fast']
    timeout = args['timeout']
    verbose = args['verbose']

    # OBD(portstr=None, baudrate=None, protocol=None, fast=True, timeout=0.1, check_voltage=True)
    connection = obd.OBD(fast=fast, timeout=timeout)
    while not connection.is_connected():
        if connection.status() == obd.OBDStatus.NOT_CONNECTED:
            print("ELM Adapter Not Found, Ending")
            exit(1)
        if verbose:
            print(f"Waiting for OBD Connection: {connection.status()}")
        sleep(CONNECTION_WAIT_DELAY)
        connection = obd.OBD()

    elm_version, elm_voltage = get_elm_info(connection)
    print("ELM VERSION", elm_version, "ELM VOLTAGE", elm_voltage)

    custom_commands = load_custom_commands(connection)

    vin = get_vin_from_vehicle(connection)
    print(f"VIN: {vin}")

    config_file = args['config_file']
    config_dir = args['config_dir']
    base_path = ''.join(args['base_path'])
    
    if not config_file:
        config_path = get_config_path(config_dir, vin)
    else:
        config_path = Path(config_dir) / Path(config_file)

    command_name_generator = CommandNameGenerator(config_path)

    while command_name_generator:
        with open(
            (get_directory(base_path, vin)) / (get_output_file_name(vin)),
            mode='w',
            encoding='utf-8'
        ) as out_file:
            for command_name in command_name_generator:
                iso_format_pre = datetime.isoformat(
                    datetime.now(tz=timezone.utc)
                )

                if obd.commands.has_name(command_name):
                    obd_response = connection.query(
                        obd.commands[command_name],
                        force=True
                    )
                elif command_name in custom_commands.keys():
                    obd_response = connection.query(
                        custom_commands[command_name],
                        force=True
                    )
                else:
                    if verbose:
                        print(f"\nmissing command: <{command_name}>\n")
                    continue

                iso_format_post = datetime.isoformat(
                    datetime.now(tz=timezone.utc)
                )

                if obd_response.is_null():
                    obd_response_value = "not supported"
                else:
                    obd_response_value = obd_response.value

                if verbose:
                    print(
                        command_name,
                        obd_response_value,
                        iso_format_pre,
                        iso_format_post
                    )

                if isinstance(obd_response_value, bytearray):
                    if command_name == "VIN":
                        obd_response_value = obd_response_value.decode("utf-8")
                    else:
                        obd_response_value = obd_response_value.hex()

                out_file.write(json.dumps({
                            'command_name': command_name,
                            'obd_response_value': f"{obd_response_value}",
                            'iso_ts_pre': iso_format_pre,
                            'iso_ts_post': iso_format_post,
                        }) + "\n"
                )

                if (
                    command_name_generator.full_cycles_count >
                    FULL_CYCLES_COUNT
                ):
                    command_name_generator.full_cycles_count = 0
                    break


if __name__ == "__main__":
    main()
