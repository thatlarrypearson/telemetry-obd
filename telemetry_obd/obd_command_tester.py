# OBD Command Tester
# telemetry-obd/telemetry_obd/obd_command_tester.py
"""
Tests every known OBD command against an OBD interface.
"""

from obd.commands import __mode1__,  __mode9__
from datetime import datetime, timezone
from pathlib import Path
from pint import OffsetUnitCalculusError
from argparse import ArgumentParser
from sys import stdout, stderr
from traceback import print_exc

import sys
import json
import logging
import obd
from .obd_common_functions import (
    load_custom_commands,
    get_vin_from_vehicle,
    get_elm_info,
    get_directory,
    get_output_file_name,
    clean_obd_query_response,
    get_obd_connection,
    execute_obd_command,
)
from .add_commands import NEW_COMMANDS

CONNECTION_WAIT_DELAY = 15.0
CYCLE_COUNT = 40
TIMEOUT=0.5

logger = logging.getLogger(__name__)

def get_command_list() -> list:
    """
    Return list of all available OBD commands.
    """
    return [cmd.name for cmd in __mode1__ + __mode9__ + NEW_COMMANDS]

def argument_parsing()-> dict:
    """Argument parsing"""
    parser = ArgumentParser(description="Telemetry OBD Command Tester")
    parser.add_argument(
        "--base_path",
        default="data",
        help="Relative or absolute output data directory. Defaults to 'data'."
    )
    parser.add_argument(
        '--cycles',
        type=int,
        default=CYCLE_COUNT,
        help=(
            "The number of cycles before ending.  A cycle consists of all known OBD commands." +
            f"  Default is {CYCLE_COUNT}."
        )
    )
    parser.add_argument(
        '--timeout',
        type=float,
        default=TIMEOUT,
        help=(
            "The number seconds before a command times out." +
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
        "added at the end of the command.  Default is off so fast is on. ",
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
    cycles = args['cycles']

    if verbose:
        print(f"argument fast: {fast}")
        print(f"argument timeout: {timeout}")
        print(f"argument verbose: {verbose}")
        print(f"argument cycles: {cycles}")

    connection = get_obd_connection(fast=fast, timeout=timeout, verbose=verbose)

    elm_version, elm_voltage = get_elm_info(connection)
    if verbose:
        print("ELM VERSION", elm_version, "ELM VOLTAGE", elm_voltage)

    custom_commands = load_custom_commands(connection)

    vin = get_vin_from_vehicle(connection)
    if verbose:
        print(f"VIN: {vin}")

    base_path = args['base_path']

    with open(
        (get_directory(base_path, vin)) / (get_output_file_name(vin + '-TEST')),
        mode='w',
        encoding='utf-8'
    ) as out_file:
        for cycle in range(cycles):
            if verbose:
                print(f"cycle {cycle} in {cycles}")
            for command_name in get_command_list():
                if verbose:
                    print(f"command_name {command_name}")

                iso_format_pre = datetime.isoformat(
                    datetime.now(tz=timezone.utc)
                )

                try:

                    obd_response = execute_obd_command(connection, command_name, verbose=verbose)

                except OffsetUnitCalculusError as e:
                    print(f"Excpetion: {e.__class__.__name__}: {e}")
                    print(f"OffsetUnitCalculusError on {command_name}, decoder must be fixed")
                    print_exc()

                except Exception as e:
                    stdout.flush()
                    stderr.flush()
                    print_exc()
                    print(f"Exception: {e}")
                    if not connection.is_connected():
                        print(f"connection failure on {command_name}, reconnecting")
                        connection.close()
                        connection = get_obd_connection(fast=fast, timeout=timeout, verbose=verbose)

                iso_format_post = datetime.isoformat(
                    datetime.now(tz=timezone.utc)
                )

                obd_response_value = clean_obd_query_response(command_name, obd_response, verbose=verbose)

                if verbose:
                    print("saving:",
                        command_name,
                        obd_response_value,
                        iso_format_pre,
                        iso_format_post
                    )

                out_file.write(json.dumps({
                            'command_name': command_name,
                            'obd_response_value': obd_response_value,
                            'iso_ts_pre': iso_format_pre,
                            'iso_ts_post': iso_format_post,
                        }) + "\n"
                )



if __name__ == "__main__":
    main()

