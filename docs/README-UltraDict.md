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

## How To Know When Shared Memory Is/Isn't Working

The following provides a method to verify that the shared memory has been created and available for use.  These commands work on most Linux based computers including Raspberry Pi's running Raspberry Pi OS.  These commands were _discovered_ while debugging a shared memory problem.  You will see that the only data being shared was input by hand into the Python REPL.


The first command gets a list of processes (```ps```) and sends its output to a filter (```grep```) that only passes through processes that contain the string ```python3.11```.  The first filter passes its output onto another filter (```-v```) that removes all output lines that contain ```grep```.  This results in process (```ps```) information that only includes process names with ```python3.11``` in them.

The second field in the process output is the process ID number.  This number (```384572```) is unique to an individual process running on the system.

Using the process ID number (```384572```), the process memory map command (```pmap```) is used to get that specific process's shared memory (```-x```) information.  We use the filter (```grep```) to pull out the lines that contain the shared dictionary name (```--shared_dictionary_name```) command line parameter (```GPS```) in a case independent way (```-i```).

The result is two memory mapped regions supporting the shared dictionary between ```gps_logger``` and other running processes like ```gps_logger```.


```bash
lbp@telemetry2:~ $ python3.11
Python 3.11.6 (main, Oct 12 2023, 16:09:12) [GCC 12.2.0] on linux
Type "help", "copyright", "credits" or "license" for more information.
>>> from tcounter.common import (
...     default_shared_gps_command_list as SHARED_DICTIONARY_COMMAND_LIST,
...     SharedDictionaryManager,
...     BASE_PATH
... )
>>> sdm = SharedDictionaryManager('TELEMETRY')
>>> for thing in sdm:
...     print(thing)
... 
>>> sdm['thing'] = 'another thing'
>>> for thing in sdm:
...     print(thing)
... 
thing
>>> <CTRL-D>
lbp@telemetry2:~$
```

Get a list of all the telemetry related processes using ```ps```, a Linux utility program providing basic process info.  Narrow the search by using ```grep``` to filter the ouput to just list processes running Python 3.11.  The process ID (**1713**), the number in the second column of output below, is needed in the following steps.

```bash
lbp@telemetry2:~$ ps -eaf | grep python3.11 | grep -v grep
lbp         1713    1681  0 14:34 ?        00:00:00 /home/lbp/.local/bin/python3.11 -m gps_logger.gps_logger --verbose --shared_dictionary_name TELEMETRY /home/lbp/telemetry-data/data
lbp         2129    1739  5 14:35 ?        00:01:59 /home/lbp/.local/bin/python3.11 -m telemetry_obd.obd_logger --timeout 4.0 --no_fast --config_dir /home/lbp/telemetry-data/config --full_cycles 10000 --shared_dictionary_name TELEMETRY --gps_defaults /home/lbp/telemetry-data/data
lbp         2441    2422  0 14:38 pts/2    00:00:00 python3.11

lbp@telemetry2:~$ 
```

Get a list of all the ```TELEMETRY``` related shared memory resources using ```pmap```, a Linux utility program.  ```pmap``` needs the process ID (**1713**) from the previous step.  Again, ```grep``` is used to filter the results to just the shared memory related to **TELEMETRY**, the name I use for shared memory in Telemetry related programs.

```bash
lbp@telemetry2:~$ sudo pmap -x 1713 | grep TELEMETRY
1713:   /home/lbp/.local/bin/python3.11 -m gps_logger.gps_logger --verbose --shared_dictionary_name TELEMETRY /home/lbp/telemetry-data/data
0000007fa36e0000    1024       0       0 rw-s- TELEMETRY_memory
0000007fa5768000      12       0       0 rw-s- TELEMETRY_register_memory
0000007fa576b000       4       4       4 rw-s- TELEMETRY_register
0000007fa576c000       4       4       4 rw-s- TELEMETRY
lbp@telemetry2:~$ 
```

Shared memory segments are represented within the Linux file system.  This is useful showing shared memory segments and access permissions in the first column.  The Linux ```ls -l``` command represents file permissions using the first column which contains 10 subfields and each character (including the dash or ```-```) is a field.

- 1st character: ```-``` means not a directory.
- 2nd through 4th characters are owner permissions.  ```r``` is read, ```w``` is write and ```-``` is not executable.
- 5th through 7th is group permissions.  There are no group permissions.
- 8th through 10th are everybody permissions.  There are no everybody permissions.

Conclusion! Only user ```lbp``` can read and write into these shared memory segments.  This is **GOOD**.

```bash
root@telemetry2:~# ls -l /dev/shm/TELEMETRY*
total 20
-rw------- 1 lbp dialout    1000 Oct 31 14:34 TELEMETRY
-rw------- 1 lbp dialout 1048576 Oct 31 14:42 TELEMETRY_memory
-rw------- 1 lbp dialout    1000 Oct 31 14:34 TELEMETRY_register
-rw------- 1 lbp dialout   10000 Oct 31 14:34 TELEMETRY_register_memory

root@telemetry2:~# cat /dev/shm/TELEMETRY
-11

root@telemetry2:~# cat /dev/shm/TELEMETRY_register
1

root@telemetry2:~# cat /dev/shm/TELEMETRY_register_memory

root@telemetry2:~# cat /dev/shm/TELEMETRY_memory | strings
thing
another thing

root@telemetry2:~#

root@telemetry2:~# lsof /dev/shm/TELEMETRY_memory 
lsof: WARNING: can't stat() fuse.gvfsd-fuse file system /run/user/1000/gvfs
      Output information may be incomplete.
lsof: WARNING: can't stat() fuse.portal file system /run/user/1000/doc
      Output information may be incomplete.
COMMAND    PID USER   FD   TYPE DEVICE SIZE/OFF NODE NAME
python3.1 1713  lbp  mem    REG   0,22  1048576   12 /dev/shm/TELEMETRY_memory
python3.1 1713  lbp    6u   REG   0,22  1048576   12 /dev/shm/TELEMETRY_memory
python3.1 1713  lbp    7u   REG   0,22  1048576   12 /dev/shm/TELEMETRY_memory
python3.1 2129  lbp  mem    REG   0,22  1048576   12 /dev/shm/TELEMETRY_memory
python3.1 2129  lbp    5u   REG   0,22  1048576   12 /dev/shm/TELEMETRY_memory
python3.1 2129  lbp    6u   REG   0,22  1048576   12 /dev/shm/TELEMETRY_memory
python3.1 2441  lbp  mem    REG   0,22  1048576   12 /dev/shm/TELEMETRY_memory
python3.1 2441  lbp    5u   REG   0,22  1048576   12 /dev/shm/TELEMETRY_memory
python3.1 2441  lbp    6u   REG   0,22  1048576   12 /dev/shm/TELEMETRY_memory

root@telemetry2:~# 
```


### Why ```ipcs``` Doesn't Work Anymore

```bash
lbp@telemetry2:~# sudo ipcs -m

------ Shared Memory Segments --------
key        shmid      owner      perms      bytes      nattch     status      
```

[```ipcs``` doesn't show my shared memory and semaphores](https://stackoverflow.com/questions/15660812/
ipcs-doesnt-show-my-shared-memory-and-semaphores)

```ipcs``` uses the UNIX System V Release 4 shared memory model.  I used that software in the 1980's.  UltraDict uses the modern Linux model for shared memory.  Much better.
