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
from tcounter.common import (
    get_output_file_name,
    get_next_application_counter_value,
    BASE_PATH,
)
from .obd_common_functions import (
    load_custom_commands,
    get_vin_from_vehicle,
    get_elm_info,
    clean_obd_query_response,
    get_obd_connection,
    execute_obd_command,
)
from .add_commands import NEW_COMMANDS

logger = logging.getLogger(__name__)

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
        "base_path",
        nargs='?',
        metavar="base_path",
        default=[BASE_PATH, ],
        help=f"Relative or absolute output data directory. Defaults to '{BASE_PATH}'."
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

    base_path = args['base_path']
    fast = not args['no_fast']
    timeout = args['timeout']
    verbose = args['verbose']
    cycles = args['cycles']

    logging_level = logging.WARNING

    if verbose:
        logging_level = logging.INFO

    if args['logging']:
        logging_level = logging.DEBUG

    logging.basicConfig(stream=sys.stdout, level=logging_level)
    obd.logger.setLevel(logging_level)

    logging.info(f"argument --fast: {fast}")
    logging.info(f"argument --timeout: {timeout}")
    logging.info(f"argument --verbose: {verbose}")
    logging.info(f"argument --cycles: {cycles}")
    logging.info(f"argument --logging: {args['logging']} ")
    logging.debug("debug logging enabled")

    connection = get_obd_connection(fast=fast, timeout=timeout)

    elm_version, elm_voltage = get_elm_info(connection)
    logging.info("ELM VERSION: {elm_version}, ELM VOLTAGE: {elm_voltage}")

    custom_commands = load_custom_commands(connection)

    vin = get_vin_from_vehicle(connection)
    logging.info(f"VIN: {vin}")

    base_path = args['base_path']

    output_file_path = get_output_file_name('obd-cmd-test', base_path=base_path, vin=vin)
    logging.info(f"output file: {output_file_path}")

    try:
        with open(output_file_path, mode='x', encoding='utf-8') as out_file:
            for cycle in range(cycles):
                logging.info(f"cycle {cycle} in {cycles}")
                for command_name in get_command_list():
                    logging.info(f"command_name {command_name}")

                    iso_ts_pre = datetime.isoformat(
                        datetime.now(tz=timezone.utc)
                    )

                    try:

                        obd_response = execute_obd_command(connection, command_name)

                    except OffsetUnitCalculusError as e:
                        logging.exception(f"Exception: {e.__class__.__name__}: {e}")
                        logging.exception(f"OffsetUnitCalculusError on {command_name}, decoder must be fixed")
                        logging.exception(f"Exception: {e}")

                    except Exception as e:
                        logging.exception(f"Exception: {e}")
                        if not connection.is_connected():
                            logging.error(f"connection failure on {command_name}, reconnecting")
                            connection.close()
                            connection = get_obd_connection(fast=fast, timeout=timeout)

                    iso_ts_post = datetime.isoformat(
                        datetime.now(tz=timezone.utc)
                    )

                    obd_response_value = clean_obd_query_response(command_name, obd_response)

                    logging.info(f"saving: {command_name}, {obd_response_value}, {iso_ts_pre}, {iso_ts_post}")

                    out_file.write(json.dumps({
                                'command_name': command_name,
                                'obd_response_value': obd_response_value,
                                'iso_ts_pre': iso_ts_pre,
                                'iso_ts_post': iso_ts_post,
                            }) + "\n"
                    )

    except FileExistsError:
        logger.error(f"open(): FileExistsError: {output_file_path}")
        imu_counter = get_next_application_counter_value('obd-cmd-test')
        logger.error(f"get_log_file_handle(): Incremented 'obd-cmd-test' counter to {imu_counter}")


if __name__ == "__main__":
    main()

