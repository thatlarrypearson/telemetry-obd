#!/bin/bash
# RaspberryPi-Auto-Run.sh
#
# To get this script to run automatically after booting, see README.md

# Need to debug this script?  Uncomment the following line.
# set -x

export HOME="/home/$(whoami)"
export FULL_CYCLES="1000"
export TEST_CYCLES="5"
export RUN_DIRECTORY="${HOME}/src/telemetry-obd"
export CONFIG_DIR="${HOME}/src/telemetry-obd/config"
export BASE_PATH="${HOME}/src/telemetry-obd/data"
export LOG_DIR="${HOME}/src/telemetry-obd/tmp"
export LOG_FILE="$(date '+%Y%m%d%H%M%S%z').log"

export PYTHON=python3.8

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

# optional - run command test first
"${PYTHON}" -m telemetry_obd.obd_command_tester \
	--cycle "${TEST_CYCLES}" \
	--base_path "${BASE_PATH}"

# the following flags can be used for debugging purposes.
#		--logging \
#		--verbose \
#		--full_cycles="${FULL_CYCLES}" \
#		--config_file=default.ini \

"${PYTHON}" -m telemetry_obd.obd_logger \
		--config_dir="${CONFIG_DIR}" \
		"${BASE_PATH}" \
		< /dev/null >&1 > "${LOG_DIR}/${LOG_FILE}" 2>&1 &

