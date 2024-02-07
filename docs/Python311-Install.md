# Python 3.11 Installation Instructions

These instructions are for installing Python 3.11 on a Raspberry Pi 4 computer running Rasberry Pi OS Bookworm version 12.2.  With some (or no) modification, these instructions will work on any recent Debian release based Linux distributions.

The latest available production version of Python 3.11 should be used when available.  The latest versions of source code can always be found on the [Python Source Releases](https://www.python.org/downloads/source/) web page.  Just scan down the list for the first (and latest) Python 3.11 version.

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

# configure build Python 3.11
./configure --enable-optimizations --prefix=${HOME}/.local --exec-prefix=${HOME}/.local --with-ensurepip=install

# build/install compiled Python 3.11
#    the build process can be speeded up using "make --jobs=$(nproc) altinstall"
#    but this often fails for unknown reasons on Raspberry Pi 4B 4GB RAM
make altinstall

# cleanup
make clean
rm -rf Python-3.11.6

# test installation
${HOME}/.local/bin/python3.11 --version
```

When ```Python 3.11.6``` is returned by the ```python3.11 --version``` command, then the python installation is complete.

## **Another Important Thing**

The Python version just installed may not be in your execution path and it needs to be so that you can execute the correct ```python3.11``` from the command line.

```bash
which python3.11
```

If this returns "```/home/<your user name>/.local/bin/python3.11```", then you may be good to go.

First, check to see if "```.profile```" exists in your home directory and includes "'''.local/bin'''" in your path.

```bash
cd
cat .profile
```

You are good if you see "```PATH="$HOME/.local/bin:$PATH"```" in the following code ```bash``` shell code fragment at the end of the file:

```bash
# set PATH so it includes user's private bin if it exists
if [ -d "$HOME/.local/bin" ] ; then
    PATH="$HOME/.local/bin:$PATH"
fi
```

If you don't see the above code fragment in your "```.profile```" file, then add it on at the end.

```bash
# if you modified .profile
source .profile
which python3.11
```

This should return "```/home/<your user name>/.local/bin/python3.11```".  If so, **Python 3.11 is correctly installed.**  Otherwise start over.

## **Some More Important Things**

Update ```pip```, the Python package installer.

```bash
# Python pip Install Support
python3.11 -m pip install --upgrade pip
```

Install package building tools.

```bash
python3.11 -m pip install --upgrade wheel setuptools markdown build cython psutil
```

## LICENSE

[MIT License](../LICENSE.md)
