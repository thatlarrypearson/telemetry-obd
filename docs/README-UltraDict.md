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
