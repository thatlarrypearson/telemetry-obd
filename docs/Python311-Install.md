# Python 3.11 Installation Instructions

These instructions are for installing Python 3.11 on a Raspberry Pi 4 computer running Rasberry Pi OS Bullseye version 11.3.  With some (or no) modification, these instructions will work on any recent Debian release based Linux distributions.

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

Run the test to determine if Python 3.11 is already installed.

```bash
# Test to determine if Python 3.11 is already installed
python3.11 --version
```

A ```commmand not found``` response means *python 3.11* must be installed.

If ```Python 3.11```, isn't already installed you will need to make it from source to install it.

If ```python3.11``` responds with a version number, then you need to do the following test to see if it can work for you:

```bash
python3.11 -m pip install pip --upgrade
```

If the first line of the response is "```error: externally-managed-environment```" then you can't use the system ```python3.11```.  You must install your own private ```python3.11```.

Go to the [Python Downloads](https://www.python.org/downloads/source/) page.  Find the most recent version of Python 3.11 from the list.  Currently, the latest 3.11 release is at version 3.11.6.  The build instructions below assume python3.11.6.

The following commands install all of the system libraries required to build Python 3.11 from source code.  You will get better results if you upgrade your Raspberry Pi operating system to version ```12.2 bookworm``` or higher.  See code below to get your operating system version information.

```bash
# install build tools
sudo apt-get update
sudo apt-get upgrade -y
sudo apt-get install -y build-essential checkinstall

# look for Raspberry Pi OS version
# e.g. '11.7' is `bullseye`
# e.g. '12.2' is 'bookworm'
cat /etc/debian_version

# look for VERSION_CODENAME, e.g. 'bookworm'
cat /etc/os-release | grep VERSION_CODENAME

# Raspberry Pi OS versions before 11.0 Bullseye
# sudo apt-get install -y libreadline-gplv2-dev
# sudo apt-get install -y libncursesw5-dev libssl-dev
# sudo apt-get install -y libsqlite3-dev tk-dev libgdbm-dev libc6-dev libbz2-dev libffi-dev zlib1g-dev

# Raspberry Pi OS version 11.x Bullseye 
# sudo apt-get install -y libreadline-dev
# sudo apt-get install -y libncursesw5-dev libssl-dev
# sudo apt-get install -y libsqlite3-dev tk-dev libgdbm-dev libc6-dev libbz2-dev libffi-dev zlib1g-dev

# Raspberry Pi OS version 12.x Bookworm
sudo apt-get install -y libreadline-dev libgdbm-compat-dev liblzma-dev
sudo apt-get install -y libncurses5-dev libnss3-dev libffi-dev
sudo apt-get install -y libncursesw5-dev libssl-dev
sudo apt-get install -y libsqlite3-dev tk-dev libgdbm-dev libc6-dev libbz2-dev libffi-dev zlib1g-dev
```

The following builds Python 3.11 from source code.

```bash
# the following makes and installs python3.11 into /usr/local/bin
# with the libraries in /usr/local/lib.
cd
wget https://www.python.org/ftp/python/3.11.6/Python-3.11.6.tgz
tar xvzf ~/Python-3.11.6.tgz
cd Python-3.11.6

# compile Python 3.11
./configure --enable-optimizations --prefix=${HOME}/.local --exec-prefix=${HOME}/.local --with-ensurepip=install

# install compiled Python 3.11
make --jobs=$(nproc) altinstall

# cleanup
make clean
rm -rf Python-3.11.6

# test installation
${HOME}.local/bin/python3.11 --version
```

All is well when ```Python 3.11.6``` is returned by the ```python3.11 --version``` command.

The latest available production version of Python 3.11 should be used when available.  The latest versions of source code can always be found on the [Python Source Releases](https://www.python.org/downloads/source/) web page.  Just scan down the list for the first Python 3.11 version.
