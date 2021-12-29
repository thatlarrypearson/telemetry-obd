# OBD List All Commands
# telemetry-obd/telemetry_obd/list_all_commands.py
"""
Lists every known OBD command with relevant info.
"""
import csv
import logging
from sys import stdout
from rich.console import Console
from rich.table import Table
from obd.commands import __mode1__,  __mode9__
from argparse import ArgumentParser
from .add_commands import NEW_COMMANDS

logger = logging.getLogger(__name__)

def get_command_list() -> dict:
    """
    Return dictionary of commands.
    """
    return_value = {cmd.name: {
            'command': cmd.name,
            'description': cmd.desc,
            'source': '__mode1__',
            'mode': cmd.command.decode('utf-8')[:2],
            'pid': cmd.command.decode('utf-8')[2:4],
        } for cmd in __mode1__}

    for cmd in __mode9__: 
        return_value[cmd.name] = {
            'command': cmd.name,
            'description': cmd.desc,
            'source': '__mode9__',
            'mode': cmd.command.decode('utf-8')[:2],
            'pid': cmd.command.decode('utf-8')[2:4],
        }

    for cmd in NEW_COMMANDS: 
        return_value[cmd.name] = {
            'command': cmd.name,
            'description': cmd.desc,
            'source': 'NEW_COMMANDS',
            'mode': cmd.command.decode('utf-8')[:2],
            'pid': cmd.command.decode('utf-8')[2:4],
        }

    return return_value

def sort_dict_keys(dict_thing:dict) -> list:
    """
    sort dictionary keys
    """
    return_value = [key for key in dict_thing]
    return sorted(return_value)

def argument_parsing()-> dict:
    """Argument parsing"""
    parser = ArgumentParser(description="Telemetry OBD List All Commands")
    parser.add_argument(
        "--csv",
        help="Output in CSV format.",
        default=False,
        action='store_true'
    )

    return vars(parser.parse_args())

def csv_print(output:dict, output_file=stdout):
    field_names = [
        'command',
        'description',
        'source',
        'mode',
        'pid',
    ]
    writer = csv.DictWriter(output_file, fieldnames=field_names)
    writer.writeheader()
    
    for command_name in output:
        writer.writerow(output[command_name])

def rich_print(output:dict):
    console = Console()

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("OBD Command", justify='left')
    table.add_column("Description", justify='left')
    table.add_column("Source", justify='left')
    table.add_column("Mode")
    table.add_column("PID")

    for command_name in output:
        table.add_row(
            output[command_name]['command'],
            output[command_name]['description'],
            output[command_name]['source'],
            f"0x{output[command_name]['mode']}",
            f"0x{output[command_name]['pid']}",
        )

    table.add_row(
        '[bold red]Total Commands[/bold red]',
        f"[bold red]{len(output)}[/bold red]"
        '',
        '',
        '',
    )


    console.print(table)


def main():
    """Run main function."""

    args = argument_parsing()

    csv = args['csv']

    command_list = get_command_list()
    command_names = sort_dict_keys(command_list)
    output = {command_name: {
            'command': command_name,
            'description': command_list[command_name]['description'],
            'source': command_list[command_name]['source'],
            'mode': command_list[command_name]['mode'],
            'pid': command_list[command_name]['pid'],
        } for command_name in command_names}

    if csv:
        csv_print(output)
    else:
        rich_print(output)


if __name__ == "__main__":
    main()

