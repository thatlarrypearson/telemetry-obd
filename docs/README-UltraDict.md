# UltraDict Installation

[UltraDict](https://github.com/ronny-rentner/UltraDict) is a new package that is currently under development.  The package provides a way for different running processes to share memory using the Python dictionary as both a storage metaphor and high level object interface definition.  That is, it works justs like a Python dictionary (```{}``` or ```dict()```).

The ```UltraDict``` Python package is not ```pip``` installable from the Internet repository.   ```UltraDict``` plays well with ```gps_logger.gps_logger``` and ```obd_logger.obd_logger``` processes when all of the dependencies are met.

## Install Dependencies

Some dependencies may be problematic to install on Windows and Mac.  These inststructions should work on all 64 bit Debian and Debian based Linux versions in sync with (Debian) Bookworm Version 12.2 or newer.

```bash
# UltraDict Documented Dependencies
sudo apt-get install -y cmake
python3.11 -m pip install --user pyrtcm
python3.11 -m pip install --user atomics
python3.11 -m pip install --user psutil
python3.11 -m pip install --user ultraimport
```

## Install UltraDict

Here is how you access the development branch and install ```UltraDict``` on Linux.  I haven't taken the time to install on Windows (missing certain Microsoft development tools) and I'm not even trying to figure out what can be done on Macs.  These instructions assume that you have already downloaded Python 3.11 source code and then built and installed Python 3.11 from that code.  You need the development tools from that build.

The following assumes that the current version is ```0.0.6```.

```bash
cd
git clone https://github.com/thatlarrypearson/UltraDict.git
cd UltraDict
python3.11 -m build .
python3.11 -m pip install dist/UltraDict-0.0.6-py3-none-any.whl
```

This build may take some time on a Raspberry Pi.

## Diagnosing UltraDict Related Problems

When using ```UltraDict```, the most embarrassing **bug** to find is the one where ```--shared_dictionary_name``` is set in the consuming application (e.g. ```telemetry_obd.obd_logger```) but GPS or weather data just isn't showing up.  When the expected data isn't showing up, add one or more of the following to the command line of ```telemetry_obd.obd_logger```:

- ```--shared_dictionary_command_list```
- ```--gps_defaults```
- ```--wthr_defaults```
- ```--imu_defaults```

Ask me how I know. :unamused:

```UltraDict``` can be difficult to install on some systems such as **Windows 10**.  This library will work without UltraDict installed.  However, there will be a log message on startup whenever the ```--shared_dictionary_name``` command line argument is used as shown below.

```powershell
PS C:\Users\human\src\telemetry-wthr> python3.11 -m gps_logger.gps_logger --shared_dictionary_name gps
ERROR:gps_logger:import error: Shared Dictionary (gps) feature unsupported: UltraDict Not installed.
...
...
...
```

The following provides a method to verify that the shared memory has been mapped into the ```gps_logger``` process space.  These commands work on most Linux based computers including Raspberry Pi's running Raspberry Pi OS.

```bash
$ ps -eaf | grep python3.11 | grep -v grep
human     384572  380137  0 13:02 pts/2    00:00:00 python3.11 -m gps_logger.gps_logger --shared_dictionary_name GPS --log_file_directory data
$ sudo pmap -x 384572 | grep -i GPS
384572:   python3.11 -m gps_logger.gps_logger --shared_dictionary_name GPS --log_file_directory data
0000007f9027a000    1024       0       0 rw-s- GPS_memory
0000007f91507000       4       4       4 rw-s- GPS
$
```

The first command gets a list of processes (```ps```) and sends its output to a filter (```grep```) that only passes through processes that contain the string ```python3.11```.  The first filter passes its output onto another filter (```-v```) that removes all output lines that contain ```grep```.  This results in process (```ps```) information that only includes process names with ```python3.11``` in them.

The second field in the process output is the process ID number.  This number (```384572```) is unique to an individual process running on the system.

Using the process ID number (```384572```), the process memory map command (```pmap```) is used to get that specific process's shared memory (```-x```) information.  We use the filter (```grep```) to pull out the lines that contain the shared dictionary name (```--shared_dictionary_name```) command line parameter (```GPS```) in a case independent way (```-i```).

The result is two memory mapped regions supporting the shared dictionary between ```gps_logger``` and other running processes like ```gps_logger```.

The following also shows shared memory owned by user ```human```.  It doesn't identify the use for the shared memory like the above example does.  This **is** useful because it shows the shared memory access permissions in the **perms** column.  The value ```600``` means the shared memory segment is accessible for read and write only by the owner ```human```.

```bash
$ ipcs -m

------ Shared Memory Segments --------
key        shmid      owner      perms      bytes      nattch     status
0x00000000 2          human      600        134217728  2          dest
0x00000000 8          human      600        524288     2          dest
0x00000000 11         human      600        524288     2          dest
0x00000000 16         human      600        524288     2          dest
0x00000000 28         human      600        524288     2          dest

$
```