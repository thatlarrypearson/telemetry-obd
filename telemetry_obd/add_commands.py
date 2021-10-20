# add_commands.py
# https://python-obd.readthedocs.io/en/latest/Custom%20Commands/
from obd import OBDCommand, ECU
from obd.decoders import percent, pid, raw_string, encoded_string
from pint import UnitRegistry 
from pint.unit import ScaleConverter
from pint.unit import UnitDefinition

ureg = UnitRegistry()
ureg.define(UnitDefinition('percent', 'percent', (), ScaleConverter(1 / 100.0)))

# custom decoders
def torque_percent(messages):
    d = messages[0].data[2:]
    v = d[0]
    v = v - 125
    return v * ureg.percent

def reference_torque(messages):
    d = messages[0].data[2:]
    a = int(d[0])
    b = int(d[1])
    v = ((a * 256.0) + b)
    return v * ureg.newton * ureg.meter

def percent_torque(messages):
    d = messages[0].data[2:]

    return [
        (int(d[0]) - 125) * ureg.percent,        # Idle
        (int(d[1]) - 125) * ureg.percent,        # Engine Point 1
        (int(d[2]) - 125) * ureg.percent,        # Enging Point 2
        (int(d[3]) - 125) * ureg.percent,        # Engine Point 3
        (int(d[4]) - 125) * ureg.percent,        # Engine Point 4
    ]

def mass_air_flow_sensor(messages):
    d = messages[0].data[2:]

    sensor_a = (((256.0 * d[1]) + d[2]) / 32.0) * ureg.gram / ureg.second if d[0] & 1 else None
    sensor_b = (((256.0 * d[3]) + d[4]) / 32.0) * ureg.gram / ureg.second if d[0] & 2 else None

    return [sensor_a, sensor_b, ]

def engine_temperature(messages):
    d = messages[0].data[2:]

    sensor_a = (d[1] - 40) * ureg.celsius if d[0] & 1 else None
    sensor_b = (d[2] - 40) * ureg.celsius if d[0] & 2 else None

    return [sensor_a, sensor_b, ]

def fuel_rate_2(messages):
    d = messages[0].data[2:]

    sensor_a = (((256.0 * d[0]) + d[1]) / 50.0) * ureg.gram / ureg.second if d[0] & 1 else None

def exhaust_flow_rate(messages):
    d = messages[0].data[2:]
    a = int(d[0])
    b = int(d[1])
    return (((a * 256.0) + b) / 5) * ureg.kilograms / ureg.second

GEARS = ['neutral', '1/reverse', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', '13', '14', '15']

def transmission_actual_gear(messages):
    d = messages[0].data[2:]

    gear = int(d[1] >> 4) if d[0] & 1 else None
    gear_ratio = (((256.0 * d[2]) + d[3]) / 1000.0) if d[0] & 2 else None

    return [gear, gear_ratio, ]

def odometer(messages):
    d = messages[0].data[2:]

    return (((((int(d[0]) << 8) + int(d[1]) << 8) + int(d[2])) << 8) + int(d[3]) / 10.0) * ureg.mile

def cylender_fuel_rate(messages):
    # returns milligrams per stroke
    # two RPM's per stroke
    d = messages[0].data[2:]
    a = int(d[0])
    b = int(d[1])
    return (((a * 256.0) + b) / 32) * ureg.milligrams

def engine_run_time(messages):
    total_engine_run_time = None
    total_idle_run_time = None
    total_pto_run_time = None

    d = messages[0].data[2:]
    total_engine_run_time_supported = bool(1 & d[0])
    total_idle_run_time_supported = bool((1 << 1) & d[0])
    total_pto_run_time_supported = bool((1 << 2) & d[0])
    if total_engine_run_time_supported:
        total_engine_run_time = (((((int(d[1]) << 8) | int(d[2])) << 8) | int(d[3])) << 8 ) | int(d[4])
    if total_idle_run_time_supported:
        total_idle_run_time = (((((int(d[5]) << 8) | int(d[6])) << 8) | int(d[7])) << 8 ) | int(d[8])
    if total_pto_run_time_supported:
        total_pto_run_time = (((((int(d[9]) << 8) | int(d[10])) << 8) | int(d[11])) << 8 ) | int(d[12])
    return [
            total_engine_run_time * ureg.second,
            total_idle_run_time * ureg.second,
            total_pto_run_time * ureg.second,
        ]

def engine_percent_torque_data(messages):
    d = messages[0].data[2:]
    engine_percent_torque_at_idle = int(d[0]) - 125
    engine_percent_torque_at_point_2 = int(d[1]) - 125
    engine_percent_torque_at_point_3 = int(d[2]) - 125
    engine_percent_torque_at_point_4 = int(d[3]) - 125
    engine_percent_torque_at_point_5 = int(d[4]) - 125

    return [
        engine_percent_torque_at_idle * ureg.percent,
        engine_percent_torque_at_point_2 * ureg.percent,
        engine_percent_torque_at_point_3 * ureg.percent,
        engine_percent_torque_at_point_4 * ureg.percent,
        engine_percent_torque_at_point_5 * ureg.percent,
    ]

NEW_COMMANDS = [
    # name, description, cmd, bytes, decoder, ECU, fast
    # OBDCommand("name", "description", b"01XX", 0, raw_string, ECU.ENGINE, True),
    # OBDCommand("PID_D", "PIDs supported [61 - 80]", b"0160", 6, pid, ECU.ENGINE, True),
    OBDCommand("TORQUE_DEMAND", "Driver's demand engine torque - percent", b"0161", 3, torque_percent, ECU.ENGINE, True),
    OBDCommand("TORQUE", "Actual engine torque - percent", b"0162", 3, torque_percent, ECU.ENGINE, True),
    OBDCommand("REFERENCE_TORQUE", "Engine reference torque", b"0163", 4, reference_torque, ECU.ENGINE, True),
    OBDCommand("PERCENT_TORQUE", "Engine percent torque", b"0164", 7, engine_percent_torque_data, ECU.ENGINE, True),
    OBDCommand("MASS_AIR_FLOW_SENSOR", "Mass air flow sensor", b"0166", 5, mass_air_flow_sensor, ECU.ENGINE, True),
    OBDCommand("ENGINE_COOLANT_TEMPERATURE", "Engine coolant temperature", b"0167", 3, engine_temperature, ECU.ENGINE, True),
    OBDCommand("INTAKE_AIR_TEMPERATURE_SENSOR", "Intake air temperature sensor", b"0168", 7, engine_temperature, ECU.ENGINE, True),
    OBDCommand("ENGINE_RUN_TIME", "Engine run time", b'017F', 15, engine_run_time, ECU.ENGINE, True),

    # OBDCommand("PID_E", "PIDs supported [81 - A0]", b"0180", 6, pid, ECU.ENGINE, True),
    OBDCommand("THROTTLE_POSITION_G", "Throttle position G", b"018D", 1, percent, ECU.ENGINE, True),
    OBDCommand("ENGINE_FRICTION_PERCENT_TORQUE", "Engine friction percent torque", b"018E", 3, torque_percent, ECU.ENGINE, True),
    OBDCommand("FUEL_RATE2", "Engine fuel rate", b"019D", 4, fuel_rate_2, ECU.ENGINE, True),
    OBDCommand("ENGINE_EXHAUST_FLOW_RATE", "Engine exhaust flow rate", b"019E", 2, exhaust_flow_rate, ECU.ENGINE, True),

    # OBDCommand("PID_F", "PIDs supported [A1 - C0]", b"01A0", 6, pid, ECU.ENGINE, True),
    OBDCommand("CYLENDER_FUEL_RATE", "Cylender fuel rate", b"01A2", 2, cylender_fuel_rate, ECU.ENGINE, True),
    OBDCommand("TRANSMISSION_ACTUAL_GEAR", "Transmission actual gear", b"01A4", 4, transmission_actual_gear, ECU.ENGINE, True),
    OBDCommand("ODOMETER", "Odometer", b"01A6", 4, odometer, ECU.ENGINE, True),

    # OBDCommand("PID_G", "PIDs supported [C1 - E0]", b"01C0", 6, pid, ECU.ENGINE, True),

    # Group 9
    OBDCommand("VIN", "Vehicle Identification Number", b"0802", 22, encoded_string(17), ECU.ENGINE,  True),

]
