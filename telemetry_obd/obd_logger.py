# telemetry_obd/obd_logger.py: Onboard Diagnostic Data Logger.
"""
telemetry_obd/obd_logger.py: Onboard Diagnostic Data Logger.
"""
from sys import stdout, stderr
from os import fsync
from time import sleep
from datetime import datetime, timezone
from pathlib import Path
from argparse import ArgumentParser
from pint import OffsetUnitCalculusError
import sys
import json
import logging
from traceback import print_exc
import obd
from .__init__ import __version__

from tcounter.common import (
    get_config_file_path,
    get_output_file_name,
    get_next_application_counter_value,
    BASE_PATH,
)

from .obd_common_functions import (
    get_vin_from_vehicle,
    get_elm_info,
    CommandNameGenerator,
    clean_obd_query_response,
    get_obd_connection,
    recover_lost_connection,
    execute_obd_command,
)

logger = logging.getLogger("obd_logger")

FULL_CYCLES_COUNT = 5000
TIMEOUT=1.0                         # seconds
DEFAULT_START_CYCLE_DELAY=0         # seconds

def argument_parsing()-> dict:
    """Argument parsing"""
    parser = ArgumentParser(description="Telemetry OBD Logger")

    parser.add_argument(
        "base_path",
        nargs='?',
        metavar="base_path",
        default=[BASE_PATH, ],
        help=f"Relative or absolute output data directory. Defaults to '{BASE_PATH}'."
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
        "--start_cycle_delay",
        help=f"Delay in seconds before first OBD command in cycle. Default is {DEFAULT_START_CYCLE_DELAY}.",
        default=DEFAULT_START_CYCLE_DELAY,
        type=float,
    )

    parser.add_argument(
        "--verbose",
        help="Turn verbose output on. Default is off.",
        default=False,
        action='store_true'
    )

    parser.add_argument(
        "--version",
        help="Print version number and exit.",
        default=False,
        action='store_true'
    )

    return vars(parser.parse_args())

def main():
    """
    Run main function.
    """

    args = argument_parsing()

    if args['version']:
        print(f"Version {__version__}", file=stdout)
        exit(0)

    fast = not args['no_fast']
    timeout = args['timeout']
    verbose = args['verbose']
    debug = args['logging']
    full_cycles = args['full_cycles']
    start_cycle_delay = args['start_cycle_delay']

    logging_level = logging.WARNING

    if verbose:
        logging_level = logging.INFO

    if debug:
        logging_level = logging.DEBUG

    logging.basicConfig(stream=sys.stdout, level=logging_level)
    obd.logger.setLevel(logging_level)

    logging.info(f"argument --fast: {fast}")
    logging.info(f"argument --timeout: {timeout}")
    logging.info(f"argument --verbose: {verbose}")
    logging.info(f"argument --full_cycles: {full_cycles}")
    logging.info(f"argument --logging: {args['logging']} ")
    logging.info(f"argument --start_cycle_delay: {start_cycle_delay}")
    logging.debug("debug logging enabled")

    # OBD(portstr=None, baudrate=None, protocol=None, fast=True, timeout=0.1, check_voltage=True)
    connection = get_obd_connection(fast=fast, timeout=timeout)

    elm_version, elm_voltage = get_elm_info(connection)
    logging.info(f"ELM VERSION: {elm_version} ELM VOLTAGE: {elm_voltage}")

    vin = get_vin_from_vehicle(connection)
    logging.info(f"VIN: {vin}")

    config_file = args['config_file']
    config_dir = args['config_dir']
    BASE_PATH = ''.join(args['base_path'])

    if config_file:
        config_path = Path(config_dir) / Path(config_file)
    else:
        config_path = get_config_file_path(vin)

    command_name_generator = CommandNameGenerator(config_path)

    first_command_name = command_name_generator.cycle_names[0]
    last_command_name = command_name_generator.cycle_names[-1]
    logging.info(f"first_command_name: {first_command_name}")
    logging.info(f"last_command_name: {last_command_name}")

    while command_name_generator:
        output_file_path = get_output_file_name('obd', vin=vin)
        logging.info(f"output file: {output_file_path}")

        try:
            # x - open for exclusive creation, failing if the file already exists
            with open(output_file_path, mode='x', encoding='utf-8') as out_file:

                for command_name in command_name_generator:
                    if first_command_name == command_name:
                        # insert delay here
                        if start_cycle_delay > 0:
                            sleep(start_cycle_delay)

                    logging.info(f"command_name: {command_name}")

                    if '-' in command_name:
                        logging.error(f"skipping malformed command_name: {command_name}")
                        continue

                    iso_ts_pre = datetime.isoformat(
                        datetime.now(tz=timezone.utc)
                    )

                    try:

                        obd_response = execute_obd_command(connection, command_name)

                    except OffsetUnitCalculusError as e:
                        logging.exception(f"Exception: {e.__class__.__name__}: {e}")
                        logging.exception(f"OffsetUnitCalculusError on {command_name}, decoder must be fixed")
                        print_exc()

                    except Exception as e:
                        logging.exception(f"Exception: {e}")
                        print_exc()
                        if not connection.is_connected():
                            logging.info(f"connection failure on {command_name}, reconnecting")
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
                    out_file.flush()
                    fsync(out_file.fileno())

                    if not connection.is_connected():
                        logging.error(f"connection lost, retrying after {command_name}")
                        connection = recover_lost_connection(connection, fast=fast, timeout=timeout)

                    if (
                        command_name_generator.full_cycles_count >
                        full_cycles
                    ):
                        command_name_generator.full_cycles_count = 0
                        break

        except FileExistsError:
            logger.error(f"open(): FileExistsError: {output_file_path}")
            imu_counter = get_next_application_counter_value('obd')
            logger.error(f"get_log_file_handle(): Incremented 'obd' counter to {imu_counter}")

if __name__ == "__main__":
    main()
