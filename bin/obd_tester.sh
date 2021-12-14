# obd_logger.sh
#
# Runs OBD Logger

# Need time for the system to startup the Bluetooth connection
export STARTUP_DELAY=10

export APP_HOME="/home/$(whoami)/telemetry-obd"
export APP_TMP_DIR="${APP_HOME}/tmp"
export APP_BASE_PATH="${APP_HOME}/data"
export APP_LOG_FILE="telemetry-$(date '+%Y%m%d%H%M%S').log"
export APP_TEST_CYCLES=5
export APP_PYTHON=python3.8

# Run Command Tester one time if following file exists
export COMMAND_TESTER="${APP_HOME}/RunCommandTester"
export COMMAND_TESTER_DELAY=60

if [ ! -d "${APP_BASE_PATH}" ]
then
	mkdir --parents "${APP_BASE_PATH}"
fi

if [ ! -d "${APP_TMP_DIR}" ]
then
	mkdir --parents "${APP_TMP_DIR}"
fi

cd "${APP_HOME}"

sleep ${STARTUP_DELAY}

${APP_PYTHON} -m telemetry_obd.obd_command_tester \
	--cycle "${APP_TEST_CYCLES}" \
	--base_path "${APP_BASE_PATH}" \
	--verbose --logging

#	>> "${APP_TMP_DIR}/${APP_LOG_FILE}" 2>&1

export RtnVal="$?"
echo
echo obd_command_tester returns "${RtnVal}"
date '+%Y%m%d%H%M%S'
