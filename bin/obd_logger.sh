#!/usr/bin/bash
# obd_logger.sh
#
# Runs OBD Logger

# Need time for the system to startup the Bluetooth connection
export STARTUP_DELAY=10

# Need time for system/vehicle OBD interface recover after failure
export RESTART_DELAY=60

export APP_HOME="/home/$(whoami)/telemetry-obd"
export APP_CONFIG_DIR="${APP_HOME}/config"
export APP_TMP_DIR="${APP_HOME}/tmp"
export APP_BASE_PATH="${APP_HOME}/data"
export APP_LOG_FILE="telemetry-$(date '+%Y-%m-%d %H_%M_%S').log"
export APP_FULL_CYCLES=1000
export APP_TEST_CYCLES=5
export APP_PYTHON=python3.8
export DEBUG="True"

# Run Command Tester one time if following file exists
export COMMAND_TESTER="${APP_HOME}/RunCommandTester"
export COMMAND_TESTER_DELAY=60

# Debugging support
if [ "${DEBUG}" == "True" ]
then
	# enable shell debug mode
	set -x
fi

if [ ! -d "${APP_TMP_DIR}" ]
then
	mkdir --parents "${APP_TMP_DIR}"
fi

# turn off stdin
0<&-

# redirect all stdout and stderr to file
exec &> "${APP_TMP_DIR}/${APP_LOG_FILE}"

date '+%Y/%m/%d %H:%M:%S'

if [ ! -d "${APP_BASE_PATH}" ]
then
	mkdir --parents "${APP_BASE_PATH}"
fi

if [ ! -d "${APP_CONFIG_DIR}" ]
then
	mkdir --parents "${APP_CONFIG_DIR}"
fi

cd "${APP_HOME}"

sleep ${STARTUP_DELAY}

if [ -f "${COMMAND_TESTER}" ]
then
	${APP_PYTHON} -m telemetry_obd.obd_command_tester \
		--cycle "${APP_TEST_CYCLES}" \
		--base_path "${APP_BASE_PATH}" \
		--verbose --logging

	export RtnVal="$?"
	echo obd_command_tester returns "${RtnVal}"
	date '+%Y/%m/%d %H:%M:%S'

	rm -f "${COMMAND_TESTER}"
	sleep "${COMMAND_TESTER_DELAY}"
fi

while date '+%Y/%m/%d %H:%M:%S'
do
	${APP_PYTHON} -m telemetry_obd.obd_logger \
		--config_file "${APP_CONFIG_FILE}" \
		--config_dir "${APP_CONFIG_DIR}" \
		--full_cycles "${APP_FULL_CYCLES}" \
		"${APP_BASE_PATH}"

	export RtnVal="$?"
	echo obd_logger returns "${RtnVal}"
	date '+%Y/%m/%d %H:%M:%S'

	sleep "${RESTART_DELAY}"
done
