#!/usr/bin/bash
# obd_logger.sh
#
# Runs OBD Logger

# Need time for the system to startup the Bluetooth connection
export STARTUP_DELAY=10

# Need time for system/vehicle OBD interface recover after failure
export RESTART_DELAY=60

export APP_ID="obd"
export APP_HOME="/home/$(whoami)/telemetry-data"
export APP_CONFIG_DIR="${APP_HOME}/config"
export APP_TMP_DIR="${APP_HOME}/tmp"
export APP_BASE_PATH="${APP_HOME}/data"
export APP_FULL_CYCLES=10000
export APP_TEST_CYCLES=100
export APP_PYTHON="/home/$(whoami)/.local/bin/python3.11"
export DEBUG="True"
export TIMEOUT=4.0

# get next application startup counter
export APP_COUNT=$(${APP_PYTHON} -m tcounter.app_counter ${APP_ID})

# get current system startup counter
export BOOT_COUNT=$(${APP_PYTHON} -m tcounter.boot_counter --current_boot_count)

export APP_LOG_FILE="telemetry-${BOOT_COUNT}-${APP_ID}-${APP_COUNT}.log"

# Run Command Tester one time if following file exists
export COMMAND_TESTER="${APP_HOME}/RunCommandTester"
export COMMAND_TESTER_DELAY=60

# Debugging support
if [ "${DEBUG}" = "True" ]
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
	# get next application startup counter
	export TEST_APP_COUNT=$(${APP_PYTHON} -m tcounter.app_counter 'obd-cmd-test')
	echo ${TEST_APP_COUNT}

	${APP_PYTHON} -m telemetry_obd.obd_command_tester \
		--timeout "${TIMEOUT}" \
		--no_fast \
		--cycle "${APP_TEST_CYCLES}" \
		"${APP_BASE_PATH}"

	export RtnVal="$?"
	echo obd_command_tester returns "${RtnVal}"

	rm -f "${COMMAND_TESTER}"
	sleep "${COMMAND_TESTER_DELAY}"
fi

while date '+%Y/%m/%d %H:%M:%S'
do
	${APP_PYTHON} -m telemetry_obd.obd_logger \
		--timeout "${TIMEOUT}" \
		--no_fast \
		--config_dir "${APP_CONFIG_DIR}" \
		--full_cycles "${APP_FULL_CYCLES}" \
		"${APP_BASE_PATH}"

	export RtnVal="$?"
	echo obd_logger returns "${RtnVal}"

	sleep "${RESTART_DELAY}"
done

