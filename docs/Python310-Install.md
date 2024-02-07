# Python 3.10 Installation Instructions

These instructions are for installing Python 3.10 on a Raspberry Pi 4 computer running Rasberry Pi OS Bullseye version 11.3.  With some (or no) modification, these instructions will work on any recent Debian release based Linux distributions.

Ensure that the Raspberry Pi software is completely updated to the most recent release.  One way to do this is as follows:

```bash
# update and upgrade Linux/Raspberry Pi OS
sudo apt update
sudo apt upgrade -y
sudo apt autoremove -y
sudo shutdown -r now
sudo apt dist-upgrade -y
sudo shutdown -r now
```

Run the test to determine if Python 3.10 is already installed.

```bash
# Test to determine if Python 3.10 is already installed
python3.10 --version
```

A ```commmand not found``` response means *python 3.10* must be installed.

If ```Python 3.10```, isn't already installed you will need to make it from source to install it.

Go to the [Python Downloads](https://www.python.org/downloads/source/) page.  Find the most recent version of Python 3.10 from the list.  Currently, the latest 3.10 release is at version 3.10.4.  The build instructions below assume python3.10.4.

The following commands install all of the system libraries required to build Python 3.10 from source code.

```bash
# install build tools
sudo apt-get update
sudo apt-get upgrade -y
sudo apt-get install -y build-essential checkinstall

# look for Raspberry Pi OS version, e.g. '11.3'
cat /etc/debian_version

# look for VERSION_CODENAME, e.g. 'bullseye'
cat /etc/os-release | grep VERSION_CODENAME

# Raspberry Pi OS versions before 11.3 Bullseye
# sudo apt-get install -y libreadline-gplv2-dev

# Raspberry Pi OS version 11.3 Bullseye 
sudo apt-get install -y libreadline-dev

sudo apt-get install -y libncursesw5-dev libssl-dev
sudo apt-get install -y libsqlite3-dev tk-dev libgdbm-dev libc6-dev libbz2-dev libffi-dev zlib1g-dev
```

The following builds Python 3.10 from source code.

```bash
# the following makes and installs python3.10 into /usr/local/bin
# with the libraries in /usr/local/lib.
cd
wget https://www.python.org/ftp/python/3.10.13/Python-3.10.13.tgz
cd /opt
sudo tar xvzf ~/Python-3.10.13.tgz
cd Python-3.10.13

# compile Python 3.10
sudo ./configure --enable-optimizations

# install compiled Python 3.10
sudo make altinstall

# cleanup
sudo make clean
cd /opt
sudo rm -rf Python-3.10.13

# test installation
python3.10 --version
```

All is well when ```Python 3.10.13``` is returned by the ```python3.10 --version``` command.

The latest available production version of Python 3.10 should be used when available.  The latest versions of source code can always be found on the [Python Source Releases](https://www.python.org/downloads/source/) web page.  Just scan down the list for the first Python 3.10 version.

## LICENSE

[MIT License](../LICENSE.md)
