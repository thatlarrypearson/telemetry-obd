# obd_logger.sh
#
# Runs OBD Tester to test all known possible OBD commands

# Need time for the system to startup the Bluetooth connection
export STARTUP_DELAY=10

export APP_HOME="/home/$(whoami)/telemetry-obd"
export APP_TMP_DIR="${APP_HOME}/tmp"
export APP_BASE_PATH="${APP_HOME}/data"
export APP_LOG_FILE="telemetry-$(date '+%Y%m%d_%H%M%S').log"
export APP_TEST_CYCLES=5
export APP_PYTHON=python3.11

# uncomment to turn off stdin
# 0<&-

# uncomment to redirect all stdout and stderr to file
# exec &> "${APP_TMP_DIR}/${APP_LOG_FILE}"

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

export RtnVal="$?"
echo
echo obd_command_tester returns "${RtnVal}"
date '+%Y/%m/%d %H:%M:%S'
