# Telemetry OBD Logging

The Telemetry OBD Logger captures vehicle performance data while the program is running.  A separate Configuration File Validation program assists in the creation of more efficient logging configuration files.

![High Level System View](docs/README-HighLevelSystemView.JPG)

The software is designed to run on Raspberry Pi with Raspberry Pi OS (formerly known as Raspbian) installed.  Bluetooth capabilities are added to the Raspberry Pi through a USB Bluetooth adapter (BT Dongle) and installed software (Bluetooth Driver and tools).

The OBD Logger and Configuration Validation software run in the Python3 (versions 3.6 or newer) environment.  Storage is utilized by the programs for storing output and configuration data.

## OBD Logger

The Telemetry OBD Logger application command line interface (CLI) is as follows:

```bash
PS C:\Users\human\src\telemetry-obd> python3.8 -m telemetry_obd.obd_logger  --help
usage:  obd_logger.py [-h] [--config_file CONFIG_FILE] [--config_dir CONFIG_DIR]
        [--full_cycles FULL_CYCLES] [--timeout TIMEOUT] [--logging] [--no_fast] [--verbose]
        [base_path]

Telemetry OBD Logger

positional arguments:
  base_path             Relative or absolute output data directory. Defaults to 'data'.

optional arguments:
  -h, --help            show this help message and exit
  --config_file CONFIG_FILE
                        Settings file name. Defaults to '<vehicle-VIN>.ini' or 'default.ini'.
  --config_dir CONFIG_DIR
                        Settings directory path. Defaults to './config'.
  --full_cycles FULL_CYCLES
                        The number of full cycles before a new output file is started. Default is 50.
  --timeout TIMEOUT     The number seconds before the current command times out. Default is 0.5 seconds.
  --logging             Turn on logging in python-obd library. Default is off.
  --no_fast             When on, commands for every request will be unaltered with potentially long timeouts when
                        the car doesn't respond promptly or at all. When off (fast is on), commands are optimized
                        before being sent to the car. A timeout is added at the end of the command. Default is off.
  --verbose             Turn verbose output on. Default is off.
PS C:\Users\human\src\telemetry-obd>
```

### Telemetry OBD Logger Run Cycles

While logging, OBD Logger submits a pattern of OBD commands to the vehicle and stores the vehicle's responses.  There are three patterns:

* Startup
* Housekeeping
* Cycle

![Run Cycles](docs/README-RunCycles.JPG)

#### Startup

The startup list of OBD commands is only executed when the program starts up.  Typically, this list of OBD commands includes:

* OBD commands whose return values never change (e.g. ```ECU_NAME```, ```ELM_VERSION```, ```ELM_VOLTAGE```)
* OBD commands with slow changing return values that might be needed for startup baseline like ```AMBIANT_AIR_TEMP``` and ```BAROMETRIC_PRESSURE```.

#### Housekeeping

A list of OBD commands that have ("relatively") "slow changing" return values such as  ```AMBIANT_AIR_TEMP``` and ```BAROMETRIC_PRESSURE```.  These are commands that need to be run over and over again but in a slower loop.

#### Cycle

A list of OBD commands that have fast changing return values such as ```RPM```, ```MAF``` (Mass Air Flow) and ```PERCENT_TORQUE```.  The idea is for these commands to run over and over again in relatively fast loops.

#### Full Cycle

The repeating part of the OBD command pattern is called a "full cycle" and has OBD commands from Cycle executed in a group followed by the next Housekeeping command.  This basic pattern repeats over and over.  When the end of the Housekeeping commands is reached, a "Full Cycle" has been achieved.

The total number of command submissions in a full cycle is the ```count of commands in Housekeeping``` times (one plus the ```count of commands in Cycle```).

The ```--full_cycles``` parameter is used to set the number of ```full_cycles``` contained in output data files.  Once the ```--full_cycles``` limit is reached, the data file is closed and a new one is opened.  This keeps data loss from unplanned Raspberry Pi shutdowns to a minimum.

### Telemetry OBD Logger Configuration Files

Configuration files are used to tell OBD Logger what OBD commands to send the vehicle and the order to send those commands in.  A sample configuration file is shown below and another one is included in the source code.

#### Default Configuration File

A default configuration file is included in the repository at ```config/default.ini```.  This configuration file contains every known possible OBD command.  Wide variations in supported command sets by manufacturer, model, trim level and year exist.  By starting out with this configuration file, OBD Logger will try all commands.  After a full cycle is run, unsupported commands will respond with ```"obd_response_value": "not supported"``` in the output data.  The Python program ```configuration_file_validation.py``` identifies good commands.  The generated list of good commands can be used to create a vehicle specific configuration file.

Some commands will result in an OBD response value of ```"not supported"``` (```"obd_response_value": "not supported"```) when the vehicle is unable to satisfy the OBD data request quickly enough.  You can identify this problem by searching for all responses for a particular command and seeing if sometimes the command responds with ```"not supported"``` or with a value.

For example, 2017 Ford F-450 truck ```FUEL_RATE``` command in the ```cycle``` section of the configuration file returned mixed results.  In 1,124 attempts, 1084 responded with a good value while 40 responded with ```not supported```.

```bash
human@computer:data/FT8W4DT5HED00000$ grep FUEL_RATE FT8W4DT5HED00000-20210910204443-utc.json | grep "not supported" | wc -l
40
human@computer:data/FT8W4DT5HED00000$ grep FUEL_RATE FT8W4DT5HED00000-20210910204443-utc.json | grep -v "not supported" | wc -l
1084
```

This problem can be solved by increasing the OBD command timeout from its default to a higher value.  Use the ```--timeout``` setting when invoking the ```obd_logger``` command.

#### Sample Configuration File For 2013 Jeep Wrangler Rubicon

The Python program ```configuration_file_validation.py``` was used to identify good commands after data was collected using ```default.ini```.  The list of known good commands were then used to create this vehicle specific configuration file.

```text
[STARTUP NAMES]
startup =
  AMBIANT_AIR_TEMP
  BAROMETRIC_PRESSURE
  CONTROL_MODULE_VOLTAGE
  COOLANT_TEMP
  DISTANCE_SINCE_DTC_CLEAR
  ECU_NAME
  ECU_NAME_MESSAGE_COUNT
  ELM_VERSION
  ELM_VOLTAGE
  FUEL_STATUS
  GET_CURRENT_DTC
  GET_DTC
  INTAKE_TEMP
  OBD_COMPLIANCE
  VIN
  WARMUPS_SINCE_DTC_CLEAR

[HOUSEKEEPING NAMES]
housekeeping =
  AMBIANT_AIR_TEMP
  BAROMETRIC_PRESSURE
  CATALYST_TEMP_B1S1
  CATALYST_TEMP_B2S1
  CONTROL_MODULE_VOLTAGE
  COOLANT_TEMP
  DISTANCE_W_MIL
  INTAKE_TEMP
  RUN_TIME

[CYCLE NAMES]
cycle =
  FUEL_LEVEL
  ABSOLUTE_LOAD
  ACCELERATOR_POS_D
  ACCELERATOR_POS_E
  COMMANDED_EQUIV_RATIO
  ENGINE_LOAD
  EVAPORATIVE_PURGE
  EVAP_VAPOR_PRESSURE
  INTAKE_PRESSURE
  LONG_FUEL_TRIM_1
  LONG_FUEL_TRIM_2
  RELATIVE_THROTTLE_POS
  RPM
  SHORT_FUEL_TRIM_1
  SHORT_FUEL_TRIM_2
  SPEED
  THROTTLE_ACTUATOR
  THROTTLE_POS_B
  THROTTLE_POS
  TIMING_ADVANCE

```

### Telemetry OBD Logger Output Data Files

Output data files are in a hybrid format.  Data files contain records separated by line feeds (```LF```) or carriage return and line feeds (```CF``` and ```LF```).  The records themselves are formatted in JSON.  Sample output follows:

```json
{"command_name": "AMBIANT_AIR_TEMP", "obd_response_value": "25 degC", "iso_ts_pre": "2020-09-09T15:38:29.114895+00:00", "iso_ts_post": "2020-09-09T15:38:29.185457+00:00"}<CR>
{"command_name": "BAROMETRIC_PRESSURE", "obd_response_value": "101 kilopascal", "iso_ts_pre": "2020-09-09T15:38:29.186497+00:00", "iso_ts_post": "2020-09-09T15:38:29.259106+00:00"}<CR>
{"command_name": "CONTROL_MODULE_VOLTAGE", "obd_response_value": "0.0 volt", "iso_ts_pre": "2020-09-09T15:38:29.260143+00:00", "iso_ts_post": "2020-09-09T15:38:29.333047+00:00"}<CR>
{"command_name": "VIN", "obd_response_value": "TEST_VIN_22_CHARS", "iso_ts_pre": "2020-09-09T15:38:30.029478+00:00", "iso_ts_post": "2020-09-09T15:38:30.061014+00:00"}
{"command_name": "FUEL_STATUS", "obd_response_value": "not supported", "iso_ts_pre": "2020-09-09T15:38:29.771997+00:00", "iso_ts_post": "2020-09-09T15:38:29.824129+00:00"}
```

#### JSON Fields

* ```command_name```
  OBD command name submitted to vehicle.

* ```obd_response_value```
  OBD response value returned by the vehicle.  When the OBD command is not supported, the response is ```"not supported"```.  Response values are either a string like ```"not supported"``` and ```"TEST_VIN_22_CHARS"``` or they are a [Pint](https://pint.readthedocs.io/en/stable/) encoded value like ```"25 degC"``` and ```"101 kilopascal"```.

* ```iso_ts_pre```
  ISO formatted timestamp taken before the OBD command was issued to the vehicle (```datetime.isoformat(datetime.now(tz=timezone.utc))```).

* ```iso_ts_post```
  ISO formatted timestamp taken after the OBD command was issued to the vehicle (```datetime.isoformat(datetime.now(tz=timezone.utc))```).

[Pint](https://pint.readthedocs.io/en/stable/) encoded values are strings with a numeric part followed by the unit.  For example, ```"25 degC"``` represents 25 degrees Centigrade.  ```"101 kilopascal"``` is around 14.6 PSI (pounds per square inch).  Pint values are used so that the units are always kept with the data and so that unit conversions can easily be done in downstream analysis software.  These strings are easy to deserialize to Pint objects for use in Python programs.

### Telemetry OBD Logger Debug Output

OBD Logger provides additional information while running when the ```--verbose``` option is used.  Additionally, The underlying python ```obd``` library (```python-obd```) supports detailed low-level logging capabilities which can be enabled within OBD Logger with the ```--logging``` option.

Sample ```--logging``` output follows:

```text
[obd.obd] ======================= python-OBD (v0.7.1) =======================
INFO:obd.obd:======================= python-OBD (v0.7.1) =======================
[obd.obd] Using scan_serial to select port
INFO:obd.obd:Using scan_serial to select port
[obd.obd] Available ports: ['/dev/rfcomm0']
INFO:obd.obd:Available ports: ['/dev/rfcomm0']
[obd.obd] Attempting to use port: /dev/rfcomm0
INFO:obd.obd:Attempting to use port: /dev/rfcomm0
[obd.elm327] Initializing ELM327: PORT=/dev/rfcomm0 BAUD=auto PROTOCOL=auto
INFO:obd.elm327:Initializing ELM327: PORT=/dev/rfcomm0 BAUD=auto PROTOCOL=auto
[obd.elm327] Response from baud 38400: b'\x7f\x7f\r?\r\r>'
DEBUG:obd.elm327:Response from baud 38400: b'\x7f\x7f\r?\r\r>'
[obd.elm327] Choosing baud 38400
DEBUG:obd.elm327:Choosing baud 38400
[obd.elm327] write: b'ATZ\r'
DEBUG:obd.elm327:write: b'ATZ\r'
[obd.elm327] wait: 1 seconds
DEBUG:obd.elm327:wait: 1 seconds
[obd.elm327] read: b'ATZ\r\r\rELM327 v1.5\r\r>'
DEBUG:obd.elm327:read: b'ATZ\r\r\rELM327 v1.5\r\r>'
[obd.elm327] write: b'ATE0\r'
DEBUG:obd.elm327:write: b'ATE0\r'
[obd.elm327] read: b'ATE0\rOK\r\r'
DEBUG:obd.elm327:read: b'ATE0\rOK\r\r'
[obd.elm327] write: b'ATH1\r'
DEBUG:obd.elm327:write: b'ATH1\r'
[obd.elm327] read: b'OK\r\r>'
DEBUG:obd.elm327:read: b'OK\r\r>'
[obd.elm327] write: b'ATL0\r'
```

## Configuration File Validation

The Python program ```configuration_file_validation.py``` identifies good commands.  The generated list of good commands can be used to create a vehicle specific configuration file.

```bash
PS C:\Users\human\src\telemetry-obd> python3.8 -m telemetry_obd.configuration_file_validation --help
usage: configuration_file_validation.py [-h] [--config_file CONFIG_FILE] [--config_dir CONFIG_DIR] [--data_file DATA_FILE] [--verbose]

Telemetry: Settings file validation tool.

optional arguments:
  -h, --help            show this help message and exit
  --config_file CONFIG_FILE
                        Settings file name. Defaults to <vehicle-VIN>.ini or 'default.ini'.
  --config_dir CONFIG_DIR
                        Settings directory path. Defaults to './config'.
  --data_file DATA_FILE
                        Data file base directory (e.g. where '<VIIN>/<VIN>-<YYYYMMDDhhmmss>-utc.json' get placed).
  --verbose             Turn verbose output on. Default is off.
PS C:\Users\human\src\telemetry-obd>
```

The OBD Logger program defaults to using the ```"default.ini"``` configuration file.  This file, included in the software distribution under ```"config/default.ini"``` contains all the known OBD commands.  Because of the wide variations in supported command sets by manufacturer, model, trim level and year made, it is difficult to know what OBD commands a specific car will respond to. Additionally, manufacturers don't typically publish lists of valid OBD commands for each vehicle sold.  This "try-them-all" method seems to be the only approach to identifying which OBD commands a specific vehicle will respond to.

Once all the possible known OBD commands have been tried, it becomes possible to create a list of valid known commands to be used in the creation of a vehicle specific configuration file.  The OBD Logger software was written to automatically choose configuration files appropriately named ```"<VIN>.ini"``` by default.  If the ```"<VIN>.ini"``` isn't available, then the other default, ```"default.ini"```, is chosen by default.

When creating vehicle specific configuration files, the Configuration File Validation output section titled ```"<vin> Valued Commands"``` is particularly helpful.  The commands in this section provide a list of commands that generate valid vehicle responses.  Only valid OBD commands should be used long term when gathering vehicle data.

## Raspberry Pi System Installation

Ensure that the Raspberry Pi software is completely updated to the most recent release.  One way to do this is as follows:

```bash
# update and upgrade Linux/Raspberry Pi OS
sudo apt-get update
sudo apt-get upgrade -y
sudo apt-get autoremove -y
sudo shutdown -r now
sudo apt-get dist-upgrade -y
sudo shutdown -r now
```

Install useful software:

```bash
# git software
sudo apt-get install -y git
```

Install the Bluetooth support software and then reboot the system:

```bash
# Bluetooth support software
sudo apt-get install -y bluetooth bluez bluez-tools blueman bluez-hcidump
sudo shutdown -r now
```

Plug in your Bluetooth USB dongle.  When purchasing USB Bluetooth devices, ensure that the device is supported by the operating system.

If your system has built-in Bluetooth support, it is possible that the built in Bluetooth device won't work and will need to be disabled.  This problem has been reported in Linux and Raspberry Pi online forums.

At some point, the Raspberry Pi will need to pair with an OBD Interface that is compatible with the ```python-obd``` software library.  Look for Bluetooth OBD interface hardware based on ELM 327 chips at version 1.5 or greater.  Some Bluetooth OBD interfaces use different chip sets which may work fine so long as they support the ELM 327 command language.

Because an OBD emulator was available, pairing the OBD interface to the Raspberry Pi worked fine using the pairing program accessible through the Pi's GUI.  The only complaint is there isn't much time to pair.  In general, from the time the OBD interface is plugged into either the car or the emulator, there is less than 20 seconds to complete the pairing before the OBD interface turns off pairing.  It took a few times to get paired.

Pairing with the OBD interface plugged into a vehicle is considerably more challenging.  OBD interface extension cords are available.  Extension cords are useful because the lights on the OBD interface can be seen.  These lights are important while trying to pair.  Lights also blink when the Pi is communicating to the OBD interface.

Validate that your Raspberry Pi has at least Python version 3.6 available:

```bash
# Python 3 version
human@hostname:~$ python3 --version
Python 3.6.9
# Python 3.6 version
human@hostname:~$ python3.6 --version
Python 3.6.9
# Python 3.8 version
human@hostname:~$ python3.8 --version
Python 3.8.5
human@hostname:~$
```

If you are comfortable with Linux, you may want to install and use Python 3.8, the version the software is being developed and tested with.

Once you are comfortable with the Python version on your system, run the following:

```bash
# Python pip Install Support
python3.8 -m pip install --upgrade --user pip
python3.8 -m pip install --upgrade --user wheel setuptools markdown

# Python Code support
python3.8 -m pip install --upgrade --user pint
```

To get VIN number retrieval, must get the most recent ```python-OBD``` source code from ```github```.

```bash
# get latest python-OBD from github repository
git clone https://github.com/brendan-w/python-OBD.git
cd python-OBD
python3.8 setup.py sdist
python3.8 -m pip install --user .
```

For Apple Mac and Windows 10 installations, see [installation on Read The Docs](https://python-obd.readthedocs.io/en/latest/#installation).

Install this software:

```bash
# get latest version of this software from github repository
git clone https://github.com/thatlarrypearson/telemetry-obd.git
cd telemetry-obd
python3.8 setup.py sdist
python3.8 -m pip install --user .
```

On Windows 10, connecting to USB or Bluetooth ELM 327 OBD interfaces is simple.  Plug in the USB and it works.  Pair the Bluetooth ELM 327 OBD interface and it works.  Linux and Raspberry Pi systems are a bit more challenging.

On Linux/Raspberry Pi based systems, USB ELM 327 based OBD interfaces present as ```tty``` devices (e.g. ```/dev/ttyUSB0```).  If software reports that the OBD interface can't be accessed, the problem may be one of permissions.  Typically, ```tty``` devices are owned by ```root``` and group is set to ```dialout```.  The user that is running the OBD data capture program must be a member of the same group (e.g. ```dialout```) as the ```tty``` device.

On Linux/Raspberry Pi, Bluetooth serial device creation is not automatic.  After Bluetooth ELM 327 OBD interface has been paired, ```sudo rfcomm bind rfcomm0 <BT-MAC-ADDRESS>``` will create the required serial device.   An example follows:

```bash
# get the Bluetooth ELM 327 OBD interface's MAC (Media Access Control) address
sudo bluetoothctl
[bluetooth]# paired-devices
Device 00:00:00:33:33:33 OBDII
[bluetooth]# exit
# MAC Address for OBD is "00:00:00:33:33:33"

# bind the Bluetooth ELM 327 OBD interface to a serial port/device using the interfaces Bluetooth MAC (Media Access Control) address:
sudo rfcomm bind rfcomm0 00:00:00:33:33:33
```

On Linux/Raspberry Pi systems, the ```rfcomm``` command creates the device ```/dev/rfcomm0``` as a serial device owned by  ```root``` and group ```dialout```.  If multiple Bluetooth serial devices are paired and bound to ```/dev/rfcomm0```, ```/dev/rfcomm1```, ```/dev/rfcomm2``` and so on, OBD Logger will only automatically connect to the first device.  The code can be modified to resolve this limitation.

Regardless of connection type (USB or Bluetooth) to an ELM 327 OBD interface, the serial device will be owned by ```root``` with group ```dialout```.  Access to the device is limited to ```root``` and users in the group ```dialout```.

Users need to be added to the group ```dialout```.  Assuming the user's username is ```human```:

```bash
human@telemetry-1:~ $ ls -l /dev/ttyUSB0
crw-rw---- 1 root dialout 188, 0 Aug 13 15:47 /dev/ttyUSB0
human@telemetry-1:~ $ ls -l /dev/rfcomm0
crw-rw---- 1 root dialout 120, 0 Aug 13 15:47 /dev/rfcomm0
human@telemetry-1:~ $ sudo adduser human dialout
```

## Headless Operation On Raspberry Pi

In order to reliably run in an automotive environment, the OBD Logger application needs to start automatically after all preconditions are satisfied.  That is, the application must start without any user interaction.  The trigger for starting the application is powering up the Raspberry Pi system.

On the Raspberry Pi, commands embedded in "```/etc/rc.local```" will be run at the end of the system startup sequence by the ```root``` user.  A sample "```/etc/rc.local```" follows:

```text
#!/bin/sh -e
#
# rc.local
#
# This script is executed at the end of each multi-user run-level.
# Make sure that the script will "exit 0" on success or any other
# value on error.
#
# In order to enable or disable this script just change the execution
# bits.
#
# By default this script does nothing.

# Print the IP address
_IP=$(hostname -I) || true
if [ "$_IP" ]; then
  printf "My IP address is %s\n" "$_IP"
fi

# Bind the paired OBDII device to /dev/rfcomm0
rfcomm bind rfcomm0 00:19:5D:26:4B:5F

# Run the script RaspberryPi-Auto-Run.sh as user "${OBD_USER}" and group "dialout"
export OBD_USER=human
export OBD_HOME="/home/${OBD_USER}/"
runuser -u "${OBD_USER}" -g dialout "${OBD_HOME}/src/telemetry-obd/bin/RaspberryPi-Auto-Run.sh" > /tmp/obd-log.$$ 2>&1

exit 0
```

The ```runuser``` command in "```/etc/rc.local```" file runs the "```RaspberryPi-Auto-Run.sh```" ```bash``` shell program as user "```human```" and group "```dialout```".  The shell program is as follows:

```bash
#!/bin/bash
# RaspberryPi-Auto-Run.sh
#
# To get this script to run automatically after booting, place the following in /etc/rc.local
#
# # Bind the paired OBDII device to /dev/rfcomm0
# rfcomm bind rfcomm0 00:19:5D:26:4B:5F
#
# # Run the script RaspberryPi-Auto-Run.sh as user "${OBD_USER}" and group "dialout"
# export OBD_USER=human
# export OBD_HOME="/home/${OBD_USER}/"
# runuser -u "${OBD_USER}" -g dialout "${OBD_HOME}/src/telemetry-obd/bin/RaspberryPi-Auto-Run.sh" > /tmp/obd-log.$$ 2>&1

# Need to debug this script?  Uncomment the following line.
# set -x

export HOME="/home/$(whoami)"
export FULL_CYCLES="30"
export RUN_DIRECTORY="${HOME}/src/telemetry-obd"
export CONFIG_DIR="${HOME}/src/telemetry-obd/config"
export BASE_PATH="${HOME}/src/telemetry-obd/data"
export LOG_DIR="${HOME}/src/telemetry-obd/tmp"
export LOG_FILE="$(date '+%Y%m%d%H%M%S%z').log"

. ${HOME}/.profile

cd "${RUN_DIRECTORY}"

if [ ! -d "${BASE_PATH}" ]
then
	mkdir --parents "${BASE_PATH}"
fi

if [ ! -d "${CONFIG_DIR}" ]
then
	mkdir --parents "${CONFIG_DIR}"
fi

if [ ! -d "${LOG_DIR}" ]
then
	mkdir --parents "${LOG_DIR}"
fi

# the following flags can be used for debugging purposes.
#		--logging \
#		--verbose \
#		--full_cycles="${FULL_CYCLES}" \
#		--config_file=default.ini \

python3.8 -m telemetry_obd.obd_logger \
		--config_dir="${CONFIG_DIR}" \
		"${BASE_PATH}" \
		< /dev/null >&1 > "${LOG_DIR}/${LOG_FILE}" 2>&1 &
```

## Running Raspberry Pi In Vehicle

Getting the Raspberry Pi and OBD interface to work reliably in running vehicles turned out to be problematic.  The initial setup used a USB OBD interface.  The thinking was that a hard wired USB connection between the Raspberry Pi and the ODB interface would be simpler and more reliable.  On the 2013 Jeep Wrangler Rubicon, this was true.  The 110 VAC power adapter was plugged into the Jeep's 110 VAC outlet.

However, both the 2017 Ford F-450 Truck and 2019 Ford EcoSport SUV wouldn't power the Raspberry Pi if it was connected via USB to an OBD interface.  It didn't matter if the Pi was plugged into 12 VDC or 110 VAC  outlets.  It wasn't until a 600 Watt Sine Wave Inverter was used to power the Raspberry Pi that the underlying problem became clear.  The inverter has [GFCI](https://www.bobvila.com/articles/gfci-outlets/#:~:text=A%20GFCI%20outlet%20contains%20a,of%20electricity%20in%20the%20outlet) circuitry that tripped soon after the Raspberry Pi started communicating through USB to the OBD interface.  There wasn't adequate electrical isolation between the vehicle OBD port and the Raspberry Pi.

Given that electrical isolation was an issue, it became clear that wireless connection between components would be necessary.  This is why Bluetooth became the preferred solution.

Depending on the power supply powering the Raspberry Pi, there may also be issues with power when powering the Pi directly through the vehicle.  Switching to a portable 12 VDC battery also made the solution more stable.

## Driver Responsibilities

![Run Cycles](docs/README-DriveSequence.JPG)

Before turning on the ignition:

* Plug OBD extension cord into vehicle OBD port.
* Plug Bluetooth ELM 327 OBD interface into OBD extension cord.
* Turn on vehicle ignition and start the vehicle.

After vehicle is running:

* Connect Bluetooth enabled Raspberry Pi to power.
* Watch Bluetooth ELM 327 OBD interface lights to ensure that the Raspberry Pi is interacting with the interface within one minute.  No lights flashing indicates a failure.

Before turning off the vehicle:

* Disconnect power from Raspberry Pi.

## Software Testing

Software was tested using a [Freematics OBD-II Emulator](https://freematics.com/products/freematics-obd-emulator-mk2/) (vehicle emulator)as well as in actual vehicles.  The test environment is as follows:

![Run Cycles](docs/README-TestEnvironment.JPG)

## Manufacturer Warranty Information

The 2019 Ford EcoSport manual has the following statement with respect to aftermarket OBD devices:

"_Your vehicle has an OBD Data Link
Connector (DLC) that is used in
conjunction with a diagnostic scan tool for
vehicle diagnostics, repairs and
reprogramming services. Installing an
aftermarket device that uses the DLC
during normal driving for purposes such as
remote insurance company monitoring,
transmission of vehicle data to other
devices or entities, or altering the
performance of the vehicle, may cause
interference with or even damage to
vehicle systems. We do not recommend
or endorse the use of aftermarket plug-in
devices unless approved by Ford. The
vehicle Warranty will not cover damage
caused by an aftermarket plug-in device._"

You use this software at your own risk.
