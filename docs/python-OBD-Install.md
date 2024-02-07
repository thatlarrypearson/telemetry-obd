# ```python-OBD``` Package Install

```python-OBD``` is a Python package handling realtime sensor data from OBD vehicle interfaces. Works with ELM327 OBD-II compliant adapters and runs on the Raspberry Pi without modification with Python 3.8.

However, ```python-OBD``` needs to run on Python 3.10 to take advantage of other third party Python packages like [UltraDict](https://github.com/ronny-rentner/UltraDict) and the newest versions of [pint](https://github.com/hgrecco/pint).

## Get The Source Code

```bash
human@hostname:~ $ # Install python-OBD from source (github repository)
human@hostname:~ $ git clone https://github.com/brendan-w/python-OBD.git
```

## Check Dependency Requirements

```bash
human@hostname:~ $ # Check to see what version of Pint is specified in dependency requirements
human@hostname:~ $ cd python-OBD
human@hostname:~/python-OBD $ grep pint setup.py
    install_requires=["pyserial==3.*", "pint==0.7.*"],
human@hostname:~/python-OBD $
```

The above dependency requirements as specified by the ```install_requires``` keyword in the ```setup.py``` file show that any ```pint``` version starting with ```0.7.``` can be used.  During ```pip``` install, the ```pint``` version used will be ```0.7.2```.

If the dependency requirements show pint version as ```0.7.*```, Python 3.10 *will not* work.

If the dependency requirements show any version of pint before ```0.19.2```, Python 3.10 *may not work*.

These packages *WILL NOT WORK* without Python 3.10 and Pint 0.19.2:

- [telemetry-obd](https://github.com/thatlarrypearson/telemetry-obd)
- [telemetry-obd-log-to-csv](https://github.com/thatlarrypearson/telemetry-obd-log-to-csv)
- [telemetry-gps](https://github.com/thatlarrypearson/telemetry-gps)

## Change Dependency Requirements

Using a code editor like [Thonny Python IDE](https://thonny.org/) or [Visual Studio Code](https://code.visualstudio.com/), change  ```0.7.*``` to ```0.19.2``` in ```setup.py```.

```bash
human@hostname:~/python-OBD $ # Check your work
human@hostname:~/python-OBD $ grep pint setup.py
    install_requires=["pyserial==3.*", "pint==0.19.2"],
human@hostname:~/python-OBD $
```

## Install Using Necessary Dependency Requirements

```bash
human@hostname:~/python-OBD $ # Build and install OBD package
human@hostname:~/python-OBD $ python3.10 -m build
human@hostname:~/python-OBD $ python3.10 -m pip install --user dist/obd-0.7.1-py3-none-any.whl
```

## Test Installation

```bash
human@hostname:~/python-OBD $ python3.10
Python 3.10.4 (main, Apr 11 2022, 15:49:38) [GCC 10.2.1 20210110] on linux
Type "help", "copyright", "credits" or "license" for more information.
>>> import obd
>>> exit
Use exit() or Ctrl-D (i.e. EOF) to exit
>>> exit()
human@hostname:~/python-OBD $
```

## LICENSE

[MIT License](../LICENSE.md)
