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

