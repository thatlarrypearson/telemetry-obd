# obd_logger.sh
#
# Runs OBD Logger

# Need time for the system to startup the Bluetooth connection
export STARTUP_DELAY=10

export APP_HOME="/home/$(whoami)/telemetry-obd"
export APP_CONFIG_DIR="${APP_HOME}/config"
export APP_BASE_PATH="${APP_HOME}/data"
export APP_FULL_CYCLES=1000
export APP_TEST_CYCLES=5
export APP_PYTHON=python3.8

# Run Command Tester one time if following file exists
export COMMAND_TESTER="${APP_HOME}/RunCommandTester"
export COMMAND_TESTER_DELAY=60

if [ ! -d "{APP_BASE_PATH}" ]
then
	mkdir --parents "${APP_BASE_PATH}"
fi

cd "${APP_HOME}"

sleep ${STARTUP_DELAY}

if [ -f "${COMMAND_TESTER}" ]
then
	${APP_PYTHON} -m telemetry_obd.obd_command_tester \
		--cycle "${APP_TEST_CYCLES}" \
		--base_path "${APP_BASE_PATH}"

	rm -f "${COMMAND_TESTER}"
	sleep "${COMMAND_TESTER_DELAY}"
fi

${APP_PYTHON} -m telemetry_obd.obd_logger \
	--config_file "${APP_CONFIG_FILE}" \
	--config_dir "${APP_CONFIG_DIR}" \
	--full_cycles "${APP_FULL_CYCLES}" \
	"${APP_BASE_PATH}"
