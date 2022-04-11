# obd_logger.sh
#
# Runs OBD Logger

# Need time for the system to startup the Bluetooth connection
export STARTUP_DELAY=10

# Need time for system/vehicle OBD interface recover after failure
export RESTART_DELARY=60

export APP_HOME="/home/$(whoami)/telemetry-obd"
export APP_CONFIG_DIR="${APP_HOME}/config"
export APP_TMP_DIR="${APP_HOME}/tmp"
export APP_BASE_PATH="${APP_HOME}/data"
export APP_LOG_FILE="telemetry-$(date '+%Y%m%d%H%M%S').log"
export APP_FULL_CYCLES=1000
export APP_TEST_CYCLES=5
export APP_PYTHON=python3.8

# Run Command Tester one time if following file exists
export COMMAND_TESTER="${APP_HOME}/RunCommandTester"
export COMMAND_TESTER_DELAY=60

if [ ! -d "${APP_BASE_PATH}" ]
then
	mkdir --parents "${APP_BASE_PATH}"
fi

if [ ! -d "${APP_CONFIG_DIR}" ]
then
	mkdir --parents "${APP_CONFIG_DIR}"
fi

if [ ! -d "${APP_TMP_DIR}" ]
then
	mkdir --parents "${APP_TMP_DIR}"
fi

cd "${APP_HOME}"

sleep ${STARTUP_DELAY}

if [ -f "${COMMAND_TESTER}" ]
then
	${APP_PYTHON} -m telemetry_obd.obd_command_tester \
		--cycle "${APP_TEST_CYCLES}" \
		--base_path "${APP_BASE_PATH}" \
		--verbose --logging \
		>> "${APP_TMP_DIR}/${APP_LOG_FILE}" 2>&1

	export RtnVal="$?"
	echo >> "${APP_TMP_DIR}/${APP_LOG_FILE}" 2>&1
	echo obd_command_tester returns "${RtnVal}" >> "${APP_TMP_DIR}/${APP_LOG_FILE}" 2>&1
	date '+%Y%m%d%H%M%S' >> "${APP_TMP_DIR}/${APP_LOG_FILE}" 2>&1

	rm -f "${COMMAND_TESTER}"
	sleep "${COMMAND_TESTER_DELAY}"
fi

while date >> "${APP_TMP_DIR}/${APP_LOG_FILE}" 2>&1
do
	${APP_PYTHON} -m telemetry_obd.obd_logger \
		--config_file "${APP_CONFIG_FILE}" \
		--config_dir "${APP_CONFIG_DIR}" \
		--full_cycles "${APP_FULL_CYCLES}" \
		"${APP_BASE_PATH}" \
		>> "${APP_TMP_DIR}/${APP_LOG_FILE}" 2>&1

	export RtnVal="$?"
	echo >> "${APP_TMP_DIR}/${APP_LOG_FILE}" 2>&1
	echo obd_logger returns "${RtnVal}" >> "${APP_TMP_DIR}/${APP_LOG_FILE}" 2>&1
	date >> "${APP_TMP_DIR}/${APP_LOG_FILE}" 2>&1

	sleep "${RESTART_DELAY}"
done
