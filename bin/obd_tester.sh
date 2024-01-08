# obd_logger.sh
#
# Runs OBD Tester to test all known possible OBD commands

# Need time for the system to startup the Bluetooth connection
export STARTUP_DELAY=10

export APP_ID="obd"
export APP_HOME="/home/$(whoami)/telemetry-data"
export APP_TMP_DIR="${APP_HOME}/tmp"
export APP_BASE_PATH="${APP_HOME}/data"
export APP_TEST_CYCLES=5
export APP_PYTHON="/home/$(whoami)/.local/bin/python3.11"

# get next application startup counter
export APP_COUNT=$(${APP_PYTHON} -m tcounter.app_counter ${APP_ID})

# get current system startup counter
export BOOT_COUNT=$(${APP_PYTHON} -m tcounter.boot_counter --current_boot_count)

export APP_LOG_FILE="telemetry-${BOOT_COUNT}-${APP_ID}-${APP_COUNT}.log"

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
	--verbose --logging \
	"${APP_BASE_PATH}"

export RtnVal="$?"
echo
echo obd_command_tester returns "${RtnVal}"
date '+%Y/%m/%d %H:%M:%S'
