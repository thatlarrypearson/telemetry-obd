"""telemetry_obd/configuration_file_validation.py: Validate configuration file."""

import obd
from argparse import ArgumentParser
from pathlib import Path
import json
from .obd_common_functions import (
    load_custom_commands,
    CommandNameGenerator
)


def main():
    """Run main function."""
    parser = ArgumentParser(description="Telemetry: Settings file validation tool.")
    parser.add_argument(
        "--config_file",
        help="Settings file name. Defaults to <vehicle-VIN>.ini or 'default.ini'.",
        default=None
    )
    parser.add_argument(
        "--config_dir",
        help="Settings directory path. Defaults to './config'.",
        default='./config'
    )
    parser.add_argument(
        "--data_file",
        help="Data file base directory (e.g. where '<VIIN>/<VIN>-<YYYYMMDDhhmmss>-utc.json' get placed)."
    )
    parser.add_argument(
        "--verbose",
        help="Turn verbose output on. Default is off.",
        default=False,
        action='store_true'
    )
    args = vars(parser.parse_args())

    custom_commands = load_custom_commands(None)
    data_file_name = args['data_file']

    command_name_generator = CommandNameGenerator(
        Path(args['config_dir']) / Path(args['config_file'])
    )

    array = [
        command_name_generator.startup_names,
        command_name_generator.cycle_names,
        command_name_generator.housekeeping_names,
    ]
    all_names = set(x for l in array for x in l)
    name_analysis = {}

    # Name Duplicates
    # Check by 'name' to see that all of the commands are supported
    # by either (not both)
    #   - OBD
    #   - Custom Commands
    for name in all_names:
        if name not in name_analysis:
            name_analysis[name] = {
                'count': 1,
                'startup': 0,
                'cycle': 0,
                'housekeeping': 0,
                'OBD': 0,
                'Custom Commands': 0,
                'pid': '',
            }
        if name in command_name_generator.startup_names:
            name_analysis[name]['startup'] += 1
        if name in command_name_generator.cycle_names:
            name_analysis[name]['cycle'] += 1
        if name in command_name_generator.housekeeping_names:
            name_analysis[name]['housekeeping'] += 1
        if name in custom_commands:
            name_analysis[name]['Custom Commands'] += 1
        if obd.commands.has_name(name):
            name_analysis[name]['OBD'] += 1

    # Command Duplicates
    # check by 'cmd' to ensure that the same 'cmd' is not also used under
    # different 'name's
    cmd_analysis = {}
    for name in all_names:
        if name in custom_commands:
            cmd_analysis[name] = {
                'custom_command_command': custom_commands[name].command,
                'obd_name': None,
            }
            if obd.commands.has_command(custom_commands[name].command):
                for command in obd.commands:
                    if command.command == custom_commands[name].command:
                        cmd_analysis[name]['obd_name'] = command.name

    # Unsupported Commands
    # Valueless Commands
    # Valued Commands
    # Output file analysis by command_name:
    #   - count number of times command_name present
    #   - count number of times obd_response_value is
    #       - "not supported"
    #       - None or ""
    #       - something else
    vin = None
    data_file_analysis = {}
    with open(data_file_name, mode='r', encoding='utf-8') as in_file:
        for line in in_file:
            # some of the files don't get closed properly
            # assume JSON decoding failure is same as EOF
            try:
                record = json.loads(line)
            except:
                break

            command_name = record['command_name']
            if (
                command_name == "VIN" and
                record['obd_response_value']
            ):
                vin = record['obd_response_value']
            if command_name not in data_file_analysis:
                data_file_analysis[command_name] = {
                    'count': 1,
                    'not_supported': 0,
                    'no_value': 0,
                    'value': 0,
                }
            else:
                data_file_analysis[command_name]['count'] += 1

            if (
                record['obd_response_value'] and
                record['obd_response_value'] == "not supported"
            ):
                data_file_analysis[command_name]['not_supported'] += 1
            elif (
                not record['obd_response_value'] or
                len(str(record['obd_response_value'])) == 0
            ):
                data_file_analysis[command_name]['no_value'] += 1
            else:
                data_file_analysis[command_name]['value'] += 1

    print(f"\n{vin} Name Duplicates")
    for name in (sorted(all_names)):
        if (
            name_analysis[name]['OBD'] > 0 and
            name_analysis[name]['Custom Commands'] > 0
        ):
            print(
                f"\tDuplicate Name: {name}",
                f"startup {bool(name_analysis[name]['startup'])}",
                f"housekeeping {bool(name_analysis[name]['housekeeping'])}",
                f"cycle {bool(name_analysis[name]['cycle'])}"
            )

    print(f"\n{vin} Command Duplicates")
    for name in cmd_analysis:
        if (
            cmd_analysis[name]['custom_command_command'] and
            cmd_analysis[name]['obd_name']
        ):
            print(
                f"\tCustom {name} and OBD {cmd_analysis[name]['obd_name']}",
                "share hex command",
                f"{cmd_analysis[name]['custom_command_command']}"
            )

    print(f"\n{vin} Unsupported Commands")
    for name in data_file_analysis:
        if data_file_analysis[name]['not_supported'] > 0:
            print(f"\t{name}")
    print(f"\n{vin} Valueless Commands")
    for name in data_file_analysis:
        if data_file_analysis[name]['no_value'] > 0:
            print(f"\t{name}")
    print(f"{vin} Valued Commands")
    for name in data_file_analysis:
        if data_file_analysis[name]['value'] > 0:
            print(f"\t{name}")


if __name__ == "__main__":
    main()
