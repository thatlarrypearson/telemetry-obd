# add_commands.py
# https://python-obd.readthedocs.io/en/latest/Custom%20Commands/
import logging
from obd import OBDCommand, ECU
from obd.decoders import percent, count, raw_string, pid, encoded_string
from pint import UnitRegistry

# from pint.facets.plain import ScaleConverter
# from pint.facets.plain import UnitDefinition
# from obd.UnitsAndScaling import Unit as ureg

logger = logging.getLogger(__name__)

# ureg.define(UnitDefinition('percent', 'percent', (), ScaleConverter(1 / 100.0)))
# ureg.define("ppm = count / 1000000 = PPM = parts_per_million")

ureg = UnitRegistry()
ureg.define("percent = [] = %")
ureg.define("ratio = []")
ureg.define("gps = gram / second = GPS = grams_per_second")
ureg.define("lph = liter / hour = LPH = liters_per_hour")
ureg.define("ppm = count / 1000000 = PPM = parts_per_million")


# useful code insert for debugging decoders
# place immediately after the function declaration:
# def decoder_function(messages):
#   logging.debug(f"messages type {type(messages)}")
#   for index, message in enumerate(messages):
#       logging.debug(f"messages[{index}] {message}")
#       if not message.parsed():
#           logging.debug(f"messages[{index}] not parsed ")
#       logging.debug(f"messages[{index}].data length {len(message.data)}")
#       for midx, b in enumerate(message.data):
#           logging.debug(f"messages[{index}].data[{midx}] {hex(int(b))}")
#       logging.debug(f"messages[{index}].frames type {type(message.frames)}")
#       for fidx, frame in enumerate(message.frames):
#           logging.debug(f"messages[{index}].frames[{fidx}].raw length {len(frame.raw)}")
#           logging.debug(f"messages[{index}].frames[{fidx}].raw type {type(frame.raw)}")
#           logging.debug(f"messages[{index}].frames[{fidx}].raw {frame.raw}")
#
# key takeaways from using this code:
#   messages[i].frames[j].raw == "NO DATA\r" when the message contains no response.

def no_data(messages:list) -> bool:
    """
    Returns False if the OBD raw interface provides some semblance
    of valid data.
    """
    # Look for frames without embedded "NO DATA" strings
    for message in messages:
        for frame in message.frames:
            if "NO DATA" not in frame.raw:
                return False

    # zero length responses are another form of no data
    return bool(len(messages[0].data[2:]))


# custom decoders
def torque_percent(messages):
    if no_data(messages):
        return None

    d = messages[0].data[2:]
    v = d[0]
    v = v - 125
    return v * ureg.percent

def reference_torque(messages):
    if no_data(messages):
        return None

    d = messages[0].data[2:]
    a = int(d[0])
    b = int(d[1])
    v = ((a * 256.0) + b)
    return v * ureg.newton * ureg.meter

def percent_torque(messages):
    if no_data(messages):
        return None

    d = messages[0].data[2:]

    return [
        (int(d[0]) - 125) * ureg.percent,        # Idle
        (int(d[1]) - 125) * ureg.percent,        # Engine Point 1
        (int(d[2]) - 125) * ureg.percent,        # Enging Point 2
        (int(d[3]) - 125) * ureg.percent,        # Engine Point 3
        (int(d[4]) - 125) * ureg.percent,        # Engine Point 4
    ]

def mass_air_flow_sensor(messages):
    if no_data(messages):
        return None

    d = messages[0].data[2:]

    sensor_a = (((256.0 * d[1]) + d[2]) / 32.0) * ureg.gram / ureg.second if d[0] & 1 else None
    sensor_b = (((256.0 * d[3]) + d[4]) / 32.0) * ureg.gram / ureg.second if d[0] & 2 else None

    return [sensor_a, sensor_b, ]

def engine_temperature(messages):
    if no_data(messages):
        return None

    d = messages[0].data[2:]

    sensor_a = ureg.Quantity(int(d[1] - 40), ureg.celsius) if d[0] & 1 else None
    sensor_b = ureg.Quantity(int(d[2] - 40), ureg.celsius) if d[0] & 2 else None

    # ureg.celsius is non-multiplicative unit
    return [sensor_a, sensor_b]

def fuel_rate_2(messages):
    if no_data(messages):
        return None

    d = messages[0].data[2:]

    engine_fuel_rate = (((256.0 * d[0]) + d[1]) / 50.0) * ureg.gram / ureg.second
    vehicle_fuel_rate = (((256.0 * d[2]) + d[3]) / 50.0) * ureg.gram / ureg.second
    return [engine_fuel_rate, vehicle_fuel_rate, ]

def exhaust_flow_rate(messages):
    if no_data(messages):
        return None

    d = messages[0].data[2:]
    a = int(d[0])
    b = int(d[1])
    return (((a * 256.0) + b) / 5) * ureg.kilograms / ureg.second

GEARS = ['neutral', '1/reverse', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', '13', '14', '15']

def transmission_actual_gear(messages):
    if no_data(messages):
        return None

    d = messages[0].data[2:]

    gear = int(d[1] >> 4) if d[0] & 1 else None
    gear_ratio = (((256.0 * d[2]) + d[3]) / 1000.0) if d[0] & 2 else None

    return [gear, gear_ratio, ]

def odometer(messages):
    if no_data(messages):
        return None

    d = messages[0].data[2:]

    return (((((int(d[0]) << 8) + int(d[1]) << 8) + int(d[2])) << 8) + int(d[3]) / 10.0) * ureg.kilometer

def cylinder_fuel_rate(messages):
    # returns milligrams per stroke
    # two RPM's per stroke
    if no_data(messages):
        return None

    d = messages[0].data[2:]
    a = int(d[0])
    b = int(d[1])
    return (((a * 256.0) + b) / 32) * ureg.milligrams

def engine_run_time(messages):
    if no_data(messages):
        return None

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
    if no_data(messages):
        return None

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

RECOMMENDED_TRANSMISSION_GEAR = [
    'neutral',
    '1',
    '2',
    '3',
    '4',
    '5',
    '6',
    '7',
    '8',
    '9',
    '10',
    '11',
    '12',
    '13',
    '14',
    '15'
]

def auxiliary_in_out_status(messages):
    if no_data(messages):
        return None

    a = messages[0].data[2]
    b = messages[0].data[3]

    pto_output_status_supported = a & 1
    automatic_transmission_neutral_drive_status_supported = a & (1 << 1)
    manual_transmission_neutral_drive_status_supported = a & (1 << 2)
    glow_plug_lamp_status_supported = a & (1 << 3)
    recommended_transmission_gear_supported = a & (1 << 4)

    pto_output_status = b & 1
    automatic_transmission_neutral_drive_status = b & (1 << 1)
    manual_transmission_neutral_drive_status = b & (1 << 2)
    glow_plug_lamp_status = b & (1 << 3)
    recommended_transmission_gear = b >> 4

    return [
        pto_output_status,
        automatic_transmission_neutral_drive_status_supported,
        manual_transmission_neutral_drive_status_supported,
        glow_plug_lamp_status_supported,
        recommended_transmission_gear_supported,
        pto_output_status,
        automatic_transmission_neutral_drive_status,
        manual_transmission_neutral_drive_status,
        glow_plug_lamp_status,
        recommended_transmission_gear,
    ]

def commanded_egr_2(messages):
    if no_data(messages):
        return None

    a = messages[0].data[2]
    b = messages[0].data[3]
    c = messages[0].data[4]
    d = messages[0].data[5]
    e = messages[0].data[6]
    f = messages[0].data[7]
    g = messages[0].data[8]

    commanded_egr_a_duty_cycle_supported = a & 1
    actual_egr_a_duty_cycle_supported = a & (1 << 1)
    egr_a_error_supported = a & (1 << 2)
    commanded_egr_b_duty_cycle_supported = a & (1 << 3)
    actual_egr_b_duty_cycle_supported = a & (1 << 4)
    egr_b_error_supported = a & (1 << 5)

    commanded_egr_a_duty_cycle = ureg('percent') * float(b) * 100.0 / 255.0  
    actual_egr_a_duty_cycle = ureg('percent') * float(c) * 100.0 / 255.0
    egr_a_error = ureg('percent') * (float(d) * 100.0 / 128.0) - 100.0
    commanded_egr_b_duty_cycle = ureg('percent') * float(e) * 100.0 / 255.0
    actual_egr_b_duty_cycle = ureg('percent') * float(f) * 100.0 / 255.0
    egr_b_error = ureg('percent') * (float(g) * 100.0 / 128.0) - 100.0

    return [
        commanded_egr_a_duty_cycle_supported,
        actual_egr_a_duty_cycle_supported,
        egr_a_error_supported,
        commanded_egr_b_duty_cycle_supported,
        actual_egr_b_duty_cycle_supported,
        egr_b_error_supported,
        commanded_egr_a_duty_cycle,
        actual_egr_a_duty_cycle,
        egr_a_error,
        commanded_egr_b_duty_cycle,
        actual_egr_b_duty_cycle,
        egr_b_error
    ]

def commanded_diesel_air_intake(messages):
    if no_data(messages):
        return None

    a = messages[0].data[2]
    b = messages[0].data[3]
    c = messages[0].data[4]
    d = messages[0].data[5]
    e = messages[0].data[6]

    commanded_intake_air_flow_a_control_supported = a & 1
    relative_intake_air_flow_a_position_supported = a & (1 << 1)
    commanded_intake_air_flow_b_control_supported = a & (1 << 2)
    relative_intake_air_flow_b_position_supported = a & (1 << 3)
    commanded_intake_air_flow_a_control = ureg('percent') * float(b) * 100.0 / 255.0
    relative_intake_air_flow_a_position = ureg('percent') * float(c) * 100.0 / 255.0
    commanded_intake_air_flow_b_control = ureg('percent') * float(d) * 100.0 / 255.0
    relative_intake_air_flow_b_position = ureg('percent') * float(e) * 100.0 / 255.0

    return [
        commanded_intake_air_flow_a_control_supported,
        relative_intake_air_flow_a_position_supported,
        commanded_intake_air_flow_b_control_supported,
        relative_intake_air_flow_b_position_supported,
        commanded_intake_air_flow_a_control,
        relative_intake_air_flow_a_position,
        commanded_intake_air_flow_b_control,
        relative_intake_air_flow_b_position
    ]

def egr_temp_scale(temp):
    return ureg.Quantity((temp - 40), ureg.celsius)

def egr_temp_wide_range_scale(temp):
    temp = (temp * 4) - 40
    return ureg.Quantity(temp, ureg.celsius)

def egr_temp(messages):
    if no_data(messages):
        return None

    a = messages[0].data[2]
    b = messages[0].data[3]
    c = messages[0].data[4]
    d = messages[0].data[5]
    e = messages[0].data[6]

    egr_temp_bank_1_sensor_1_supported = a & 1
    egr_temp_bank_1_sensor_2_supported = a & (1 << 1)
    egr_temp_bank_2_sensor_1_supported = a & (1 << 2)
    egr_temp_bank_2_sensor_2_supported = a & (1 << 3)
    egr_temp_bank_1_sensor_1_wide_range_supported = a & (1 << 4)
    egr_temp_bank_1_sensor_2_wide_range_supported = a & (1 << 5)
    egr_temp_bank_2_sensor_1_wide_range_supported = a & (1 << 6)
    egr_temp_bank_2_sensor_2_wide_range_supported = a & (1 << 7)

    if egr_temp_bank_1_sensor_1_supported:
        egr_temp_bank_1_sensor_1 = egr_temp_scale(b)
    else:
        egr_temp_bank_1_sensor_1 = None

    if egr_temp_bank_1_sensor_2_supported:
        egr_temp_bank_1_sensor_2 = egr_temp_scale(c)
    else:
        egr_temp_bank_1_sensor_2 = None

    if egr_temp_bank_2_sensor_1_supported:
        egr_temp_bank_2_sensor_1 = egr_temp_scale(d)
    else:
        egr_temp_bank_2_sensor_1 = None

    if egr_temp_bank_2_sensor_2_supported:
        egr_temp_bank_2_sensor_2 = egr_temp_scale(e)
    else:
        egr_temp_bank_2_sensor_2 = None

    if egr_temp_bank_1_sensor_1_wide_range_supported:
        egr_temp_bank_1_sensor_1_wide_range = egr_temp_wide_range_scale(b)
    else:
        egr_temp_bank_1_sensor_1_wide_range = None

    if egr_temp_bank_1_sensor_2_wide_range_supported:
        egr_temp_bank_1_sensor_2_wide_range = egr_temp_wide_range_scale(c)
    else:
        egr_temp_bank_1_sensor_2_wide_range = None

    if egr_temp_bank_2_sensor_1_wide_range_supported:
        egr_temp_bank_2_sensor_1_wide_range = egr_temp_wide_range_scale(d)
    else:
        egr_temp_bank_2_sensor_1_wide_range = None

    if egr_temp_bank_2_sensor_2_wide_range_supported:
        egr_temp_bank_2_sensor_2_wide_range = egr_temp_wide_range_scale(e)
    else:
        egr_temp_bank_2_sensor_2_wide_range = None

    return [
        egr_temp_bank_1_sensor_1_supported,
        egr_temp_bank_1_sensor_2_supported,
        egr_temp_bank_2_sensor_1_supported,
        egr_temp_bank_2_sensor_2_supported,
        egr_temp_bank_1_sensor_1_wide_range_supported,
        egr_temp_bank_1_sensor_2_wide_range_supported,
        egr_temp_bank_2_sensor_1_wide_range_supported,
        egr_temp_bank_2_sensor_2_wide_range_supported,
        egr_temp_bank_1_sensor_1,
        egr_temp_bank_1_sensor_2,
        egr_temp_bank_2_sensor_1,
        egr_temp_bank_2_sensor_2,
        egr_temp_bank_1_sensor_1_wide_range,
        egr_temp_bank_1_sensor_2_wide_range,
        egr_temp_bank_2_sensor_1_wide_range,
        egr_temp_bank_2_sensor_2_wide_range
    ]

def throttle(messages):
    if no_data(messages):
        return None

    a = messages[0].data[2]
    b = messages[0].data[3]
    c = messages[0].data[4]
    d = messages[0].data[5]
    e = messages[0].data[6]

    commanded_throttle_actuator_a_control_supported = a & 1
    relative_throttle_a_position_supported = a & (1 << 1)
    commanded_throttle_actuator_b_control_supported = a & (1 << 2)
    relative_throttle_b_position_supported = a & (1 << 3)

    if commanded_throttle_actuator_a_control_supported:
        commanded_throttle_actuator_a_control = (100.0/255.0) * b * ureg.percent
    else:
        commanded_throttle_actuator_a_control = None
    
    if relative_throttle_a_position_supported:
        relative_throttle_a_position = (100.0/255.0) * c * ureg.percent
    else:
        relative_throttle_a_position = None

    if commanded_throttle_actuator_b_control_supported:
        commanded_throttle_actuator_b_control = (100.0/255.0) * d * ureg.percent
    else:
        commanded_throttle_actuator_b_control = None
    
    if relative_throttle_b_position_supported:
        relative_throttle_b_position = (100.0/255.0) * e * ureg.percent
    else:
        relative_throttle_b_position = None

    return [
        commanded_throttle_actuator_a_control_supported,
        relative_throttle_a_position_supported,
        commanded_throttle_actuator_b_control_supported,
        relative_throttle_b_position_supported,
        commanded_throttle_actuator_a_control,
        relative_throttle_a_position,
        commanded_throttle_actuator_b_control,
        relative_throttle_b_position
    ]

def fuel_pressure_control(messages):
    if no_data(messages):
        return None

    a = messages[0].data[2]
    b = messages[0].data[3]
    c = messages[0].data[4]
    d = messages[0].data[5]
    e = messages[0].data[6]
    f = messages[0].data[7]
    g = messages[0].data[8]
    h = messages[0].data[9]
    i = messages[0].data[10]
    j = messages[0].data[11]
    k = messages[0].data[12]

    commanded_fuel_rail_pressure_a_supported = a & 1
    fuel_rail_pressure_a_supported = a & (1 << 1)
    fuel_temperature_a_supported = a & (1 << 2)
    commanded_fuel_rail_pressure_b_supported = a & (1 << 3)
    fuel_rail_pressure_b_supported = a & (1 << 4)
    fuel_temperature_b_supported = a & (1 << 5)

    if commanded_fuel_rail_pressure_a_supported:
        commanded_fuel_rail_pressure_a = ((256.0 * b) + c) * 10.0 * ureg.kPa
    else:
        commanded_fuel_rail_pressure_a = None

    if fuel_rail_pressure_a_supported:
        fuel_rail_pressure_a = ((256.0 * d) + e) * 10.0 * ureg.kPa
    else:
        fuel_rail_pressure_a = None
    
    if fuel_temperature_a_supported:
        fuel_temperature_a = ureg.Quantity((f - 40.0), ureg.celsius)
    else:
        fuel_temperature_a = None

    if commanded_fuel_rail_pressure_b_supported:
        commanded_fuel_rail_pressure_b = ((256.0 * g) + h) * 10.0 * ureg.kPa
    else:
        commanded_fuel_rail_pressure_b = None

    if fuel_rail_pressure_b_supported:
        fuel_rail_pressure_b = ((256.0 * i) + j) * 10.0 * ureg.kPa
    else:
        fuel_rail_pressure_b = None
    
    if fuel_temperature_b_supported:
        fuel_temperature_b = ureg.Quantity((k - 40.0), ureg.celsius)
    else:
        fuel_temperature_b = None

    return [
        commanded_fuel_rail_pressure_a_supported,
        fuel_rail_pressure_a_supported,
        fuel_temperature_a_supported,
        commanded_fuel_rail_pressure_b_supported,
        fuel_rail_pressure_b_supported,
        fuel_temperature_b_supported,
        commanded_fuel_rail_pressure_a,
        fuel_rail_pressure_a,
        fuel_temperature_a,
        commanded_fuel_rail_pressure_b,
        fuel_rail_pressure_b,
        fuel_temperature_b
    ]

def injection_pressure_control(messages):
    if no_data(messages):
        return None

    a = messages[0].data[2]
    b = messages[0].data[3]
    c = messages[0].data[4]
    d = messages[0].data[5]
    e = messages[0].data[6]
    f = messages[0].data[7]
    g = messages[0].data[8]
    h = messages[0].data[9]
    i = messages[0].data[10]

    commanded_injection_control_pressure_a_supported = a & 1
    injection_control_pressure_a_supported = a & (1 << 1)
    commanded_injection_control_pressure_b_supported = a & (1  << 2)
    injection_control_pressure_b_supported = a & (1 << 3)

    if commanded_injection_control_pressure_a_supported:
        commanded_injection_control_pressure_a = ((256.0 * g) + h) * 10.0 * ureg.kPa
    else:
        commanded_injection_control_pressure_a = None
    
    if injection_control_pressure_a_supported:
        injection_control_pressure_a = ((256.0 * g) + h) * 10.0 * ureg.kPa
    else:
        injection_control_pressure_a = None

    if commanded_injection_control_pressure_b_supported:
        commanded_injection_control_pressure_b = ((256.0 * g) + h) * 10.0 * ureg.kPa
    else:
        commanded_injection_control_pressure_b = None

    if injection_control_pressure_b_supported:
        injection_control_pressure_b = ((256.0 * g) + h) * 10.0 * ureg.kPa
    else:
        injection_control_pressure_b = None
    
    return [
        commanded_injection_control_pressure_a_supported,
        injection_control_pressure_a_supported,
        commanded_injection_control_pressure_b_supported,
        injection_control_pressure_b_supported,
        commanded_injection_control_pressure_a,
        injection_control_pressure_a,
        commanded_injection_control_pressure_b,
        injection_control_pressure_b
    ]

def turbo_inlet_pressure(messages):
    if no_data(messages):
        return None

    a = messages[0].data[2]
    b = messages[0].data[3]
    c = messages[0].data[4]

    turbocharger_inlet_pressure_sensor_a_supported = a & 1
    turbocharger_inlet_pressure_sensor_b_supported = a & (1 << 1)
    turbocharger_inlet_pressure_sensor_a_wide_range_supported = a & (1 << 2)
    turbocharger_inlet_pressure_sensor_b_wide_range_supported = a & (1 << 3)

    turbocharger_inlet_pressure_sensor_a = None
    turbocharger_inlet_pressure_sensor_b = None
    turbocharger_inlet_pressure_sensor_a_wide_range = None
    turbocharger_inlet_pressure_sensor_b_wide_range = None

    if turbocharger_inlet_pressure_sensor_a_supported:
        turbocharger_inlet_pressure_sensor_a = b * ureg.kPa
    if turbocharger_inlet_pressure_sensor_b_supported:
        turbocharger_inlet_pressure_sensor_b = c * ureg.kPa
    if turbocharger_inlet_pressure_sensor_a_wide_range_supported:
        turbocharger_inlet_pressure_sensor_a_wide_range = b * 8 * ureg.kPa
    if turbocharger_inlet_pressure_sensor_b_wide_range_supported:
        turbocharger_inlet_pressure_sensor_a_wide_range = c * 8 * ureg.kPa

    return [
        turbocharger_inlet_pressure_sensor_a_supported,
        turbocharger_inlet_pressure_sensor_b_supported,
        turbocharger_inlet_pressure_sensor_a_wide_range_supported,
        turbocharger_inlet_pressure_sensor_b_wide_range_supported,
        turbocharger_inlet_pressure_sensor_a,
        turbocharger_inlet_pressure_sensor_b,
        turbocharger_inlet_pressure_sensor_a_wide_range,
        turbocharger_inlet_pressure_sensor_b_wide_range
    ]

BOOST_PRESSURE_CONTROL_STATUS = {
    0: 'reserved, not defined',
    1: 'Boost Control Open Loop (no fault present)',
    2: 'Boost Control Closed Loop (no fault present)',
    3: 'Boost Control Fault (fault present, boost data unreliable)',
}


def boost_pressure(messages):
    if no_data(messages):
        return None

    a = messages[0].data[2]
    b = messages[0].data[3]
    c = messages[0].data[4]
    d = messages[0].data[5]
    e = messages[0].data[6]
    f = messages[0].data[7]
    g = messages[0].data[8]
    h = messages[0].data[9]
    i = messages[0].data[10]
    j = messages[0].data[11]

    commanded_boost_pressure_a_supported = a & 1
    boost_pressure_sensor_a_supported = a & (1 << 1)
    boost_pressure_a_control_status_supported = a & (1 << 2)
    commanded_boost_pressure_b_supported = a & (1 << 3)
    boost_pressure_sensor_b_supported = a & (1 << 4)
    boost_pressure_b_control_status_supported = a & (1 << 5)

    commanded_boost_pressure_a = None
    boost_pressure_sensor_a = None
    commanded_boost_pressure_b = None
    boost_pressure_sensor_b = None
    boost_pressure_a_control_status = None
    boost_pressure_b_control_status = None

    if commanded_boost_pressure_a_supported:
        commanded_boost_pressure_a = float((256.0 * b) + c) * 0.03125 * ureg.kPa
    if boost_pressure_sensor_a_supported:
        boost_pressure_sensor_a = float((256.0 * d) + e) * 0.03125 * ureg.kPa
    if commanded_boost_pressure_b_supported:
        commanded_boost_pressure_b = float((256.0 * f) + g) * 0.03125 * ureg.kPa
    if boost_pressure_sensor_b_supported:
        boost_pressure_sensor_b = float((256.0 * h) + i) * 0.03125 * ureg.kPa
    if boost_pressure_a_control_status_supported:
        boost_pressure_a_control_status = BOOST_PRESSURE_CONTROL_STATUS[j & ((1 << 1) + 1)]
    if boost_pressure_b_control_status_supported:
        boost_pressure_b_control_status = BOOST_PRESSURE_CONTROL_STATUS[(j & ((1 << 2) + (1 << 3)) >> 2)]

    return [
        commanded_boost_pressure_a_supported,
        boost_pressure_sensor_a_supported,
        boost_pressure_a_control_status_supported,
        commanded_boost_pressure_b_supported,
        boost_pressure_sensor_b_supported,
        boost_pressure_b_control_status_supported,
        commanded_boost_pressure_a,
        boost_pressure_sensor_a,
        commanded_boost_pressure_b,
        boost_pressure_sensor_b,
        boost_pressure_a_control_status,
        boost_pressure_b_control_status
    ]

VGT_CONTROL_STATUS = {
    0: 'reserved, not defined',
    1: 'VGT Open Loop (no fault present)',
    2: 'VGT Closed Loop (no fault present)',
    3: 'VGT Fault (fault present, boost data unreliable)',
}


def vg_turbo_control(messages):
    if no_data(messages):
        return None

    a = messages[0].data[2]
    b = messages[0].data[3]
    c = messages[0].data[4]
    d = messages[0].data[5]
    e = messages[0].data[6]
    f = messages[0].data[7]

    commanded_vgt_a_position_supported = a &  1
    vgt_a_position_supported = a & (1 << 1)
    vgt_a_control_status_supported = a & (1 << 2)
    commanded_vgt_b_position_supported = a &  (1 << 3)
    vgt_b_position_supported = a & (1 << 4)
    vgt_b_control_status_supported = a & (1 << 5)

    commanded_vgt_a_position = None
    vgt_a_position = None
    commanded_vgt_b_position = None
    vgt_b_position = None
    vgt_a_control_status = None
    vgt_b_control_status = None

    if commanded_vgt_a_position_supported:
        commanded_vgt_a_position = (b * 100.0 / 255.0) * ureg.percent
    if vgt_a_position_supported:
        vgt_a_position = (c * 100.0 / 255.0) * ureg.percent
    if commanded_vgt_b_position_supported:
        commanded_vgt_b_position = (d * 100.0 / 255.0) * ureg.percent
    if vgt_b_position_supported:
        vgt_b_position = (e * 100.0 / 255.0) * ureg.percent
    if vgt_a_control_status_supported:
        vgt_a_control_status = VGT_CONTROL_STATUS[f & ((1 << 1) +  1)]
    if vgt_b_control_status_supported:
        vgt_b_control_status = VGT_CONTROL_STATUS[(f >> 2) & ((1 << 1) +  1)]

    return [
        commanded_vgt_a_position_supported,
        vgt_a_position_supported,
        vgt_a_control_status_supported,
        commanded_vgt_b_position_supported,
        vgt_b_position_supported,
        vgt_b_control_status_supported,
        commanded_vgt_a_position,
        vgt_a_position,
        commanded_vgt_b_position,
        vgt_b_position,
        vgt_a_control_status,
        vgt_b_control_status,
    ]

def wastegate_control(messages):
    if no_data(messages):
        return None

    a = messages[0].data[2]
    b = messages[0].data[3]
    c = messages[0].data[4]
    d = messages[0].data[5]
    e = messages[0].data[6]

    commanded_wastegate_a_position_supported = a & 1
    wastegate_a_position_supported = a & (1 << 1)
    commanded_wastegate_b_position_supported = a & (1 << 2)
    wastegate_b_position_supported = a & (1 << 3)

    commanded_wastegate_a_position = None
    wastegate_a_position = None
    commanded_wastegate_b_position = None
    wastegate_b_position = None
   
    if commanded_wastegate_a_position_supported:
       commanded_wastegate_a_position = (b * 100.0 / 255.0) * ureg.percent
    if wastegate_a_position_supported:
        wastegate_a_position = (c * 100.0 / 255.0) * ureg.percent
    if commanded_wastegate_b_position_supported:
        commanded_wastegate_b_position = (d * 100.0 / 255.0) * ureg.percent
    if wastegate_b_position_supported:
        wastegate_b_position = (e * 100.0 / 255.0) * ureg.percent

    return [
        commanded_wastegate_a_position_supported,
        wastegate_a_position_supported,
        commanded_wastegate_b_position_supported,
        wastegate_b_position_supported,
        commanded_wastegate_a_position,
        wastegate_a_position,
        commanded_wastegate_b_position,
        wastegate_b_position
    ]

def exhaust_pressure(messages):
    if no_data(messages):
        return None

    a = messages[0].data[2]
    b = messages[0].data[3]
    c = messages[0].data[4]
    d = messages[0].data[5]
    e = messages[0].data[6]

    exhaust_pressure_sensor_bank_1_supported = a & 1
    exhaust_pressure_sensor_bank_2_supported = a & (1 << 1)
    exhaust_pressure_sensor_bank_1 = None
    exhaust_pressure_sensor_bank_2 = None

    if exhaust_pressure_sensor_bank_1_supported:
        exhaust_pressure_sensor_bank_1 = float((256.0 * b) + c) * 0.01 * ureg.kPa
    if exhaust_pressure_sensor_bank_2_supported:
        exhaust_pressure_sensor_bank_2 = float((256.0 * b) + c) * 0.01 * ureg.kPa

    return [
        exhaust_pressure_sensor_bank_1_supported,
        exhaust_pressure_sensor_bank_2_supported,
        exhaust_pressure_sensor_bank_1,
        exhaust_pressure_sensor_bank_2,
    ]

def turbo_rpm(messages):
    if no_data(messages):
        return None

    a = messages[0].data[2]
    b = messages[0].data[3]
    c = messages[0].data[4]
    d = messages[0].data[5]
    e = messages[0].data[6]

    turbo_a_rpm_supported = a & 1
    turbo_b_rpm_supported = a & (1 << 1)
    turbo_a_rpm = None
    turbo_b_rpm = None

    if turbo_a_rpm_supported:
        turbo_a_rpm = ((256 * b) + c) * 10 * ureg.revolutions_per_minute
    if turbo_b_rpm_supported:
        turbo_b_rpm = ((256 * d) + e) * 10 * ureg.revolutions_per_minute

    return [
        turbo_a_rpm_supported,
        turbo_b_rpm_supported,
        turbo_a_rpm,
        turbo_b_rpm
    ]

def turbo_temp(messages):
    if no_data(messages):
        return None

    a = messages[0].data[2]
    b = messages[0].data[3]
    c = messages[0].data[4]
    d = messages[0].data[5]
    e = messages[0].data[6]
    f = messages[0].data[7]
    g = messages[0].data[8]

    turbo_compressor_inlet_temperature_supported = a & 1
    turbo_compressor_outlet_temperature_supported = a & (1 << 1)
    turbo_turbine_inlet_temperature_supported = a & (1 << 2)
    turbo_turbine_outlet_temperature_supported = a & (1 << 3)
    turbo_compressor_inlet_temperature = None
    turbo_compressor_outlet_temperature = None
    turbo_turbine_inlet_temperature = None
    turbo_turbine_outlet_temperature = None

    if turbo_compressor_inlet_temperature_supported:
        turbo_compressor_inlet_temperature = ureg.Quantity((b - 40), ureg.celsius)
    if turbo_compressor_outlet_temperature_supported:
        turbo_compressor_outlet_temperature = ureg.Quantity((c - 40), ureg.celsius)
    if turbo_turbine_inlet_temperature_supported:
        turbo_turbine_inlet_temperature = ureg.Quantity(((((256 * d) + e) * 0.1) - 40), ureg.celsius)
    if turbo_turbine_outlet_temperature_supported:
        turbo_turbine_outlet_temperature = ureg.Quantity(((((256 * f) + g) * 0.1) - 40), ureg.celsius)

    return [
        turbo_compressor_inlet_temperature_supported,
        turbo_compressor_outlet_temperature_supported,
        turbo_turbine_inlet_temperature_supported,
        turbo_turbine_outlet_temperature_supported,
        turbo_compressor_inlet_temperature,
        turbo_compressor_outlet_temperature,
        turbo_turbine_inlet_temperature,
        turbo_turbine_outlet_temperature
    ]

def cact(messages):
    if no_data(messages):
        return None

    a = messages[0].data[2]
    b = messages[0].data[3]
    c = messages[0].data[4]
    d = messages[0].data[5]
    e = messages[0].data[6]

    cact_bank_1_sensor_1_supported = a & 1
    cact_bank_1_sensor_2_supported = a & (1 << 1)
    cact_bank_2_sensor_1_supported = a & (1 << 2)
    cact_bank_2_sensor_2_supported = a & (1 << 3)
    cact_bank_1_sensor_1 = None
    cact_bank_1_sensor_2 = None
    cact_bank_2_sensor_1 = None
    cact_bank_2_sensor_2 = None

    if cact_bank_1_sensor_1_supported:
        cact_bank_1_sensor_1 = ureg.Quantity((b - 40), ureg.celsius)
    if cact_bank_1_sensor_2_supported:
        cact_bank_1_sensor_2 = ureg.Quantity((c - 40), ureg.celsius)
    if cact_bank_2_sensor_1_supported:
        cact_bank_2_sensor_1 = ureg.Quantity((d - 40), ureg.celsius)
    if cact_bank_2_sensor_2_supported:
        cact_bank_2_sensor_2 = ureg.Quantity((e - 40), ureg.celsius)

    return [
        cact_bank_1_sensor_1_supported,
        cact_bank_1_sensor_2_supported,
        cact_bank_2_sensor_1_supported,
        cact_bank_2_sensor_2_supported,
        cact_bank_1_sensor_1,
        cact_bank_1_sensor_2,
        cact_bank_2_sensor_1,
        cact_bank_2_sensor_2
    ]

def egt_bank_temp(messages):
    if no_data(messages):
        return None

    a = messages[0].data[2]
    b = messages[0].data[3]
    c = messages[0].data[4]
    d = messages[0].data[5]
    e = messages[0].data[6]
    f = messages[0].data[7]
    g = messages[0].data[8]
    h = messages[0].data[9]
    i = messages[0].data[10]

    egt_sensor_1_supported = a & 1
    egt_sensor_2_supported = a & (1 << 1)
    egt_sensor_3_supported = a & (1 << 2)
    egt_sensor_4_supported = a & (1 << 3)
    egt_sensor_1 = None
    egt_sensor_2 = None
    egt_sensor_3 = None
    egt_sensor_4 = None

    if egt_sensor_1_supported:
        egt_sensor_1 = ureg.Quantity(((((256 * b) + c) * 0.1) - 40.0), ureg.celsius)
    if egt_sensor_2_supported:
        egt_sensor_2 = ureg.Quantity(((((256 * d) + e) * 0.1) - 40.0), ureg.celsius)
    if egt_sensor_3_supported:
        egt_sensor_3 = ureg.Quantity(((((256 * f) + g) * 0.1) - 40.0), ureg.celsius)
    if egt_sensor_4_supported:
        egt_sensor_4 = ureg.Quantity(((((256 * h) + i) * 0.1) - 40.0), ureg.celsius)

    return [
        egt_sensor_1_supported,
        egt_sensor_2_supported,
        egt_sensor_3_supported,
        egt_sensor_4_supported,
        egt_sensor_1,
        egt_sensor_2,
        egt_sensor_3,
        egt_sensor_4
    ]

def dpf_bank(messages):
    if no_data(messages):
        return None

    a = messages[0].data[2]
    b = messages[0].data[3]
    c = messages[0].data[4]
    d = messages[0].data[5]
    e = messages[0].data[6]
    f = messages[0].data[7]
    g = messages[0].data[8]

    delta_pressure_supported = a & 1
    inlet_pressure_supported = a & (1 << 1)
    outlet_pressure_supported = a & (1 << 2)
    delta_pressure = None
    inlet_pressure = None
    outlet_pressure = None

    if delta_pressure_supported:
        delta_pressure = float((256.0 * (b & 0xEF)) + c) * 0.01 * ureg.kPa
        if (a >> 7):
            # delta_pressure is negative
            delta_pressure = -1.0 * delta_pressure
    if inlet_pressure_supported:
        inlet_pressure = float((256.0 * d) + e) * 0.01 * ureg.kPa
    if outlet_pressure_supported:
        outlet_pressure = float((256.0 * f) + g) * 0.01 * ureg.kPa

    return [
        delta_pressure_supported,
        inlet_pressure_supported,
        outlet_pressure_supported,
        delta_pressure,
        inlet_pressure,
        outlet_pressure,
    ]

def dpf_temp(messages):
    if no_data(messages):
        return None

    a = messages[0].data[2]
    b = messages[0].data[3]
    c = messages[0].data[4]
    d = messages[0].data[5]
    e = messages[0].data[6]
    f = messages[0].data[7]
    g = messages[0].data[8]
    h = messages[0].data[9]
    i = messages[0].data[10]

    dpf_bank_1_inlet_temp_supported = a & 1
    dpf_bank_1_outlet_temp_supported = a & (1 << 1)
    dpf_bank_2_inlet_temp_supported = a & (1 << 2)
    dpf_bank_2_outlet_temp_supported = a & (1 << 3)
    dpf_bank_1_inlet_temp = None
    dpf_bank_1_outlet_temp = None
    dpf_bank_2_inlet_temp = None
    dpf_bank_2_outlet_temp = None

    if dpf_bank_1_inlet_temp_supported:
        dpf_bank_1_inlet_temp = ureg.Quantity(float((256.0 * b) + c) * 0.1, ureg.celsius)
    if dpf_bank_1_outlet_temp_supported:
        dpf_bank_1_outlet_temp = ureg.Quantity(float((256.0 * d) + e) * 0.1, ureg.celsius)
    if dpf_bank_2_inlet_temp_supported:
        dpf_bank_2_inlet_temp = ureg.Quantity(float((256.0 * f) + g) * 0.1, ureg.celsius)
    if dpf_bank_2_outlet_temp_supported:
        dpf_bank_2_outlet_temp = ureg.Quantity(float((256.0 * h) + i) * 0.1, ureg.celsius)

    return [
        dpf_bank_1_inlet_temp_supported,
        dpf_bank_1_outlet_temp_supported,
        dpf_bank_2_inlet_temp_supported,
        dpf_bank_2_outlet_temp_supported,
        dpf_bank_1_inlet_temp,
        dpf_bank_1_outlet_temp,
        dpf_bank_2_inlet_temp,
        dpf_bank_2_outlet_temp
    ]

def nte_status(messages):
    if no_data(messages):
        return None

    a = messages[0].data[2]

    inside_control_area = a & 1
    outside_control_area = a & (1 << 1)
    inside_mgfr_nte_carve_out_area = a & (1 << 2)
    active_area_nte_deficiency = a & (1 << 3)

    return [
        inside_control_area,
        outside_control_area,
        inside_mgfr_nte_carve_out_area,
        active_area_nte_deficiency
    ]

def run_time_calculator(d):
    return (((((int(d[0]) << 8) + int(d[1]) << 8) + int(d[2])) << 8) + int(d[3])) * ureg.second

def engine_run_time_aecd(messages):
    if no_data(messages):
        return None

    a = messages[0].data[2]
    total_run_time_with_ei_aecd_1_active_supported = a & 1
    total_run_time_with_ei_aecd_2_active_supported = a & (1 << 1)
    total_run_time_with_ei_aecd_3_active_supported = a & (1 << 2)
    total_run_time_with_ei_aecd_4_active_supported = a & (1 << 3)
    total_run_time_with_ei_aecd_5_active_supported = a & (1 << 4)
    total_run_time_with_ei_aecd_1_active_timer_1 = None
    total_run_time_with_ei_aecd_1_active_timer_2 = None
    total_run_time_with_ei_aecd_2_active_timer_1 = None
    total_run_time_with_ei_aecd_2_active_timer_2 = None
    total_run_time_with_ei_aecd_3_active_timer_1 = None
    total_run_time_with_ei_aecd_3_active_timer_2 = None
    total_run_time_with_ei_aecd_4_active_timer_1 = None
    total_run_time_with_ei_aecd_4_active_timer_2 = None
    total_run_time_with_ei_aecd_5_active_timer_1 = None
    total_run_time_with_ei_aecd_5_active_timer_2 = None

    if total_run_time_with_ei_aecd_1_active_supported:
        total_run_time_with_ei_aecd_1_active_timer_1 = run_time_calculator(messages[0].data[3:7])
        total_run_time_with_ei_aecd_1_active_timer_2 = run_time_calculator(messages[0].data[7:11])

    if total_run_time_with_ei_aecd_2_active_supported:
        total_run_time_with_ei_aecd_2_active_timer_1 = run_time_calculator(messages[0].data[11:15])
        total_run_time_with_ei_aecd_2_active_timer_2 = run_time_calculator(messages[0].data[15:19])

    if total_run_time_with_ei_aecd_3_active_supported:
        total_run_time_with_ei_aecd_3_active_timer_1 = run_time_calculator(messages[0].data[19:23])
        total_run_time_with_ei_aecd_3_active_timer_2 = run_time_calculator(messages[0].data[23:27])

    if total_run_time_with_ei_aecd_4_active_supported:
        total_run_time_with_ei_aecd_4_active_timer_1 = run_time_calculator(messages[0].data[27:31])
        total_run_time_with_ei_aecd_4_active_timer_2 = run_time_calculator(messages[0].data[31:35])

    if total_run_time_with_ei_aecd_5_active_supported:
        total_run_time_with_ei_aecd_5_active_timer_1 = run_time_calculator(messages[0].data[35:39])
        total_run_time_with_ei_aecd_5_active_timer_2 = run_time_calculator(messages[0].data[39:43])

    return [
        total_run_time_with_ei_aecd_1_active_supported,
        total_run_time_with_ei_aecd_2_active_supported,
        total_run_time_with_ei_aecd_3_active_supported,
        total_run_time_with_ei_aecd_4_active_supported,
        total_run_time_with_ei_aecd_5_active_supported,
        total_run_time_with_ei_aecd_1_active_timer_1,
        total_run_time_with_ei_aecd_1_active_timer_2,
        total_run_time_with_ei_aecd_2_active_timer_1,
        total_run_time_with_ei_aecd_2_active_timer_2,
        total_run_time_with_ei_aecd_3_active_timer_1,
        total_run_time_with_ei_aecd_3_active_timer_2,
        total_run_time_with_ei_aecd_4_active_timer_1,
        total_run_time_with_ei_aecd_4_active_timer_2,
        total_run_time_with_ei_aecd_5_active_timer_1,
        total_run_time_with_ei_aecd_5_active_timer_2,
    ]

def nox_sensor(messages):
    if no_data(messages):
        return None

    a = messages[0].data[2]
    b = messages[0].data[3]
    c = messages[0].data[4]
    d = messages[0].data[5]
    e = messages[0].data[6]
    f = messages[0].data[7]
    g = messages[0].data[8]
    h = messages[0].data[9]
    i = messages[0].data[10]

    concentration_bank_1_sensor_1_supported = a & 1
    concentration_bank_1_sensor_2_supported = a & (1 << 1)
    concentration_bank_2_sensor_1_supported = a & (1 << 2)
    concentration_bank_2_sensor_2_supported = a & (1 << 3)
    concentration_bank_1_sensor_1_data_availability = None
    concentration_bank_1_sensor_2_data_availability = None
    concentration_bank_2_sensor_1_data_availability = None
    concentration_bank_2_sensor_2_data_availability = None
    concentration_bank_1_sensor_1_data = None
    concentration_bank_1_sensor_2_data = None
    concentration_bank_2_sensor_1_data = None
    concentration_bank_2_sensor_2_data = None

    if concentration_bank_1_sensor_1_supported:
        concentration_bank_1_sensor_1_data_availability = a & (1 << 4)
    if concentration_bank_1_sensor_2_supported:
        concentration_bank_1_sensor_2_data_availability = a & (1 << 5)
    if concentration_bank_2_sensor_1_supported:
        concentration_bank_2_sensor_1_data_availability = a & (1 << 6)
    if concentration_bank_2_sensor_2_supported:
        concentration_bank_2_sensor_2_data_availability = a & (1 << 7)

    if concentration_bank_1_sensor_1_data_availability:
        concentration_bank_1_sensor_1_data = ((256 * b) + c) * ureg.ppm
    if concentration_bank_1_sensor_2_data_availability:
        concentration_bank_1_sensor_2_data = ((256 * d) + e) * ureg.ppm
    if concentration_bank_2_sensor_1_data_availability:
        concentration_bank_2_sensor_1_data = ((256 * f) + g) * ureg.ppm
    if concentration_bank_2_sensor_2_data_availability:
        concentration_bank_2_sensor_2_data = ((256 * h) + i) * ureg.ppm

    return [
        concentration_bank_1_sensor_1_supported,
        concentration_bank_1_sensor_2_supported,
        concentration_bank_2_sensor_1_supported,
        concentration_bank_2_sensor_2_supported,
        concentration_bank_1_sensor_1_data_availability,
        concentration_bank_1_sensor_2_data_availability,
        concentration_bank_2_sensor_1_data_availability,
        concentration_bank_2_sensor_2_data_availability,
        concentration_bank_1_sensor_1_data,
        concentration_bank_1_sensor_2_data,
        concentration_bank_2_sensor_1_data,
        concentration_bank_2_sensor_2_data,
    ]

def nox_control_system(messages):
    if no_data(messages):
        return None

    a = messages[0].data[2]
    b = messages[0].data[3]
    c = messages[0].data[4]
    d = messages[0].data[5]
    e = messages[0].data[6]
    f = messages[0].data[7]
    g = messages[0].data[8]
    h = messages[0].data[9]
    i = messages[0].data[10]
    j = messages[0].data[11]

    average_reagent_consumption_support = a & 1
    average_demanded_reagent_consumption_support = a & (1 << 1)
    reagent_tank_level_supported = a & (1 << 2)
    minutes_engine_run_while_nox_warning_mode_is_activated_support = a & (1 << 3)
    average_reagent_consumption = None
    average_demanded_reagent_consumption = None
    reagent_tank_level = None
    minutes_engine_run_while_nox_warning_mode_is_activated = None

    if average_reagent_consumption_support:
        average_reagent_consumption = float((b * 256) + c) * 0.05 * ureg.lph
    if average_demanded_reagent_consumption_support:
        average_demanded_reagent_consumption = float((d * 256) + e) * 0.05 * ureg.lph
    if reagent_tank_level_supported:
        reagent_tank_level = ((f * 100.0) / 255.0) * ureg.percent
    if minutes_engine_run_while_nox_warning_mode_is_activated_support:
        minutes_engine_run_while_nox_warning_mode_is_activated = ((256 * ((256 * ((256 * g) + h)) + i)) + j) * ureg.second

    return [
        average_reagent_consumption_support,
        average_demanded_reagent_consumption_support,
        reagent_tank_level_supported,
        minutes_engine_run_while_nox_warning_mode_is_activated_support,
        average_reagent_consumption,
        average_demanded_reagent_consumption,
        reagent_tank_level,
        minutes_engine_run_while_nox_warning_mode_is_activated,
    ]

def particulate_matter_support(messages):
    if no_data(messages):
        return None

    a = messages[0].data[2]
    b = messages[0].data[3]
    c = messages[0].data[4]
    d = messages[0].data[5]
    e = messages[0].data[6]

    mass_concentration_bank_1_sensor_1_supported = a & 1
    mass_concentration_bank_2_sensor_1_supported = a & (1 << 1)
    mass_concentration_bank_1_sensor_1 = None
    mass_concentration_bank_2_sensor_1 = None

    if mass_concentration_bank_1_sensor_1_supported:
        mass_concentration_bank_1_sensor_1 = float((256 * b) + c) * 0.0125 * ureg['mg/meter**3']
    if mass_concentration_bank_2_sensor_1_supported:
        mass_concentration_bank_2_sensor_1 = float((256 * d) + e) * 0.0125 * ureg['mg/meter**3']

    return [
        mass_concentration_bank_1_sensor_1_supported,
        mass_concentration_bank_2_sensor_1_supported,
        mass_concentration_bank_1_sensor_1,
        mass_concentration_bank_2_sensor_1,
    ]

def intake_manifold_pressure(messages):
    if no_data(messages):
        return None

    a = messages[0].data[2]
    b = messages[0].data[3]
    c = messages[0].data[4]
    d = messages[0].data[5]
    e = messages[0].data[6]

    pressure_a_supported = a & 1
    pressure_b_supported = a & (1 << 1)
    pressure_a = None
    pressure_b = None

    if pressure_a_supported:
        pressure_a = float((256 * b) + c) * 0.03125 * ureg.kPa
    if pressure_b_supported:
        pressure_b = float((256 * d) + e) * 0.03125 * ureg.kPa
    
    return [
        pressure_a_supported,
        pressure_b_supported,
        pressure_a,
        pressure_b,
    ]

def scr_inducement_system(messages):
    if no_data(messages):
        return None

    a = messages[0].data[2]
    b = messages[0].data[3]
    c = messages[0].data[4]
    d = messages[0].data[5]
    e = messages[0].data[6]
    f = messages[0].data[7]
    g = messages[0].data[8]
    h = messages[0].data[9]
    i = messages[0].data[10]
    j = messages[0].data[11]
    k = messages[0].data[12]
    l = messages[0].data[13]
    m = messages[0].data[14]

    empty_reagent_tank_actual_state = a & 1
    incorrect_reagent_actual_state = a & (1 << 1)
    deviation_of_reagent_consumption_actual_state = a & (1 << 2)
    nox_emission_too_high_actual_state = a & (1 << 3)
    inducement_system_active_actual_state = a & (1 << 7)
    history_10k_reagent_level_low = b & 1
    history_10k_incorrect_reagent = b & (1 << 1)
    history_10k_reagent_consumption_deviation = b & (1 << 2)
    history_10k_nox_emissions_too_high = b & (1 << 3)
    history_20k_reagent_level_low = b & (1 << 4)
    history_20k_incorrect_reagent = b & (1 << 5)
    history_20k_reagent_consumption_deviation = b & (1 << 6)
    history_20k_nox_emissions_too_high = b & (1 << 7)
    history_30k_reagent_level_low = c & 1
    history_30k_incorrect_reagent = c & (1 << 1)
    history_30k_reagent_consumption_deviation = c & (1 << 2)
    history_30k_nox_emissions_too_high = c & (1 << 3)
    history_40k_reagent_level_low = c & (1 << 4)
    history_40k_incorrect_reagent = c & (1 << 5)
    history_40k_reagent_consumption_deviation = c & (1 << 6)
    history_40k_nox_emissions_too_high = c & (1 << 7)
    current_10k_block_inducement_system_active_distance = ((256 * d) + e) * ureg.kilometer
    current_10k_block_distance = ((256 * f) + g) * ureg.kilometer
    current_20k_block_inducement_system_active_distance = ((256 * h) + i) * ureg.kilometer
    current_30k_block_inducement_system_active_distance = ((256 * j) + k) * ureg.kilometer
    current_40k_block_inducement_system_active_distance = ((256 * l) + m) * ureg.kilometer

    return [
        empty_reagent_tank_actual_state,
        incorrect_reagent_actual_state,
        deviation_of_reagent_consumption_actual_state,
        nox_emission_too_high_actual_state,
        inducement_system_active_actual_state,
        history_10k_reagent_level_low,
        history_10k_incorrect_reagent,
        history_10k_reagent_consumption_deviation,
        history_10k_nox_emissions_too_high,
        history_20k_reagent_level_low,
        history_20k_incorrect_reagent,
        history_20k_reagent_consumption_deviation,
        history_20k_nox_emissions_too_high,
        history_30k_reagent_level_low,
        history_30k_incorrect_reagent,
        history_30k_reagent_consumption_deviation,
        history_30k_nox_emissions_too_high,
        history_40k_reagent_level_low,
        history_40k_incorrect_reagent,
        history_40k_reagent_consumption_deviation,
        history_40k_nox_emissions_too_high,
        current_10k_block_inducement_system_active_distance,
        current_10k_block_distance,
        current_20k_block_inducement_system_active_distance,
        current_30k_block_inducement_system_active_distance,
        current_40k_block_inducement_system_active_distance,
    ]

def aftertreatment_status(messages):
    if no_data(messages):
        return None

    a = messages[0].data[2]
    b = messages[0].data[3]
    c = messages[0].data[4]
    d = messages[0].data[5]
    e = messages[0].data[6]
    f = messages[0].data[7]
    g = messages[0].data[8]

    particulate_filter_regeneration_status_supported = a & 1
    particulate_filter_regeneration_type_supported = a & (1 << 1)
    nox_absorber_regeneration_status_supported = a & (1 << 2)
    nox_absorber_desulfurization_status_supported = a & (1 << 3)
    particulate_filter_regeneration_normalized_trigger_supported = a & (1 << 4)
    particulate_filter_regeneration_average_time_supported = a & (1 << 5)
    particulate_filter_regeneration_average_distance_supported = a & (1 << 6)
    particulate_filter_regeneration_status = None
    particulate_filter_regeneration_type = None
    nox_absorber_regeneration_status = None
    nox_absorber_desulfurization_type = None
    particulate_filter_regeneration_normalized_trigger = None
    particulate_filter_regeneration_average_time = None
    particulate_filter_regeneration_average_distance = None

    if particulate_filter_regeneration_status_supported:
        particulate_filter_regeneration_status = b & 1
    if particulate_filter_regeneration_type_supported:
        particulate_filter_regeneration_type = b & (1 << 1)
    if nox_absorber_regeneration_status_supported:
        nox_absorber_regeneration_status = b & (1 << 2)
    if nox_absorber_desulfurization_status_supported:
        nox_absorber_desulfurization_type = b & (1 << 3)

    if particulate_filter_regeneration_normalized_trigger_supported:
        particulate_filter_regeneration_normalized_trigger = ((c * 100.0) / 255.0) * ureg.percent
    if particulate_filter_regeneration_average_time_supported:
        particulate_filter_regeneration_average_time = ((256 * d) + e) * ureg.minute
    if particulate_filter_regeneration_average_distance_supported:
        particulate_filter_regeneration_average_distance = ((256 * f) + g) * ureg.kilometer

    return [
        particulate_filter_regeneration_status_supported,
        particulate_filter_regeneration_type_supported,
        nox_absorber_regeneration_status_supported,
        nox_absorber_desulfurization_status_supported,
        particulate_filter_regeneration_normalized_trigger_supported,
        particulate_filter_regeneration_average_time_supported,
        particulate_filter_regeneration_average_distance_supported,
        particulate_filter_regeneration_status,
        particulate_filter_regeneration_type,
        nox_absorber_regeneration_status,
        nox_absorber_desulfurization_type,
        particulate_filter_regeneration_normalized_trigger,
        particulate_filter_regeneration_average_time,
        particulate_filter_regeneration_average_distance,
    ]


def o2_sensor_wide(messages):
    if no_data(messages):
        return None

    a = messages[0].data[2]
    b = messages[0].data[3]
    c = messages[0].data[4]
    d = messages[0].data[5]
    e = messages[0].data[6]
    f = messages[0].data[7]
    g = messages[0].data[8]
    h = messages[0].data[9]
    i = messages[0].data[10]
    j = messages[0].data[11]
    k = messages[0].data[12]
    l = messages[0].data[13]
    m = messages[0].data[14]
    n = messages[0].data[15]
    o = messages[0].data[16]
    p = messages[0].data[17]
    q = messages[0].data[18]

    o2_sensor_concentration_bank_1_sensor_1_supported = a & 1
    o2_sensor_concentration_bank_1_sensor_2_supported = a & (1 << 1)
    o2_sensor_concentration_bank_2_sensor_1_supported = a & (1 << 2)
    o2_sensor_concentration_bank_2_sensor_2_supported = a & (1 << 3)
    o2_sensor_lambda_bank_1_sensor_1_supported = a & (1 << 4)
    o2_sensor_lambda_bank_1_sensor_2_supported = a & (1 << 5)
    o2_sensor_lambda_bank_2_sensor_1_supported = a & (1 << 6)
    o2_sensor_lambda_bank_2_sensor_2_supported = a & (1 << 7)

    o2_sensor_concentration_bank_1_sensor_1 = None
    o2_sensor_concentration_bank_1_sensor_2 = None
    o2_sensor_concentration_bank_2_sensor_1 = None
    o2_sensor_concentration_bank_2_sensor_2 = None
    o2_sensor_lambda_bank_1_sensor_1 = None
    o2_sensor_lambda_bank_1_sensor_2 = None
    o2_sensor_lambda_bank_2_sensor_1 = None
    o2_sensor_lambda_bank_2_sensor_2 = None

    if o2_sensor_concentration_bank_1_sensor_1_supported:
        o2_sensor_concentration_bank_1_sensor_1 = float((256 * b) + c) * 0.001526 * ureg.percent
    if o2_sensor_concentration_bank_1_sensor_2_supported:
        o2_sensor_concentration_bank_1_sensor_2 = float((256 * d) + e) * 0.001526 * ureg.percent
    if o2_sensor_concentration_bank_2_sensor_1_supported:
        o2_sensor_concentration_bank_2_sensor_1 = float((256 * f) + g) * 0.001526 * ureg.percent
    if o2_sensor_concentration_bank_2_sensor_2_supported:
        o2_sensor_concentration_bank_2_sensor_2 = float((256 * h) + i) * 0.001526 * ureg.percent
    if o2_sensor_lambda_bank_1_sensor_1_supported:
        o2_sensor_lambda_bank_1_sensor_1 = float((256 * j) + k) * 0.000122 * ureg.ratio
    if o2_sensor_lambda_bank_1_sensor_2_supported:
        o2_sensor_lambda_bank_1_sensor_2 = float((256 * l) + m) * 0.000122 * ureg.ratio
    if o2_sensor_lambda_bank_2_sensor_1_supported:
        o2_sensor_lambda_bank_2_sensor_1 = float((256 * n) + o) * 0.000122 * ureg.ratio
    if o2_sensor_lambda_bank_2_sensor_2_supported:
        o2_sensor_lambda_bank_2_sensor_2 = float((256 * p) + q) * 0.000122 * ureg.ratio

    return [
        o2_sensor_concentration_bank_1_sensor_1_supported,
        o2_sensor_concentration_bank_1_sensor_2_supported,
        o2_sensor_concentration_bank_2_sensor_1_supported,
        o2_sensor_concentration_bank_2_sensor_2_supported,
        o2_sensor_lambda_bank_1_sensor_1_supported,
        o2_sensor_lambda_bank_1_sensor_2_supported,
        o2_sensor_lambda_bank_2_sensor_1_supported,
        o2_sensor_lambda_bank_2_sensor_2_supported,
        o2_sensor_concentration_bank_1_sensor_1,
        o2_sensor_concentration_bank_1_sensor_2,
        o2_sensor_concentration_bank_2_sensor_1,
        o2_sensor_concentration_bank_2_sensor_2,
        o2_sensor_lambda_bank_1_sensor_1,
        o2_sensor_lambda_bank_1_sensor_2,
        o2_sensor_lambda_bank_2_sensor_1,
        o2_sensor_lambda_bank_2_sensor_2,
    ]

def pm_sensor_output(messages):
    if no_data(messages):
        return None

    a = messages[0].data[2]
    b = messages[0].data[3]
    c = messages[0].data[4]
    d = messages[0].data[5]
    e = messages[0].data[6]
    f = messages[0].data[7]
    g = messages[0].data[8]

    operating_status_bank_1_sensor_1_supported = a & 1
    signal_bank_1_sensor_1_supported = a & (1 << 1)
    operating_status_bank_2_sensor_1_supported = a & (1 << 2)
    signal_bank_1_sensor_2_supported = a & (1 << 3)
    active_status_bank_1_sensor_1 = b & 1
    regen_status_bank_1_sensor_1 = b & (1 << 1)
    active_status_bank_2_sensor_1 = e & 1
    regen_status_bank_2_sensor_1 = e & (1 << 1)
    normalized_output_value_bank_1_sensor_1 = None
    normalized_output_value_bank_2_sensor_1 = None

    if active_status_bank_1_sensor_1:
        normalized_output_value_bank_1_sensor_1 = float((256 * c) + d) * 0.01 * ureg.percent
    if active_status_bank_2_sensor_1:
        normalized_output_value_bank_2_sensor_1 = float((256 * f) + g) * 0.01 * ureg.percent

    return [
        operating_status_bank_1_sensor_1_supported,
        signal_bank_1_sensor_1_supported,
        operating_status_bank_2_sensor_1_supported,
        signal_bank_1_sensor_2_supported,
        active_status_bank_1_sensor_1,
        regen_status_bank_1_sensor_1,
        active_status_bank_2_sensor_1,
        regen_status_bank_2_sensor_1,
        normalized_output_value_bank_1_sensor_1,
        normalized_output_value_bank_2_sensor_1,
    ]

def wwh_obd_system_info(messages):
    if no_data(messages):
        return None

    a = messages[0].data[2]
    b = messages[0].data[3]
    c = messages[0].data[4]

    display_strategy = (a & 1) + (a & 2)
    malfunction_indicator_status = ((a & (1 << 2)) + (a & (1 << 3)) + (a & (1 << 4)) + (a & (1 << 5))) >> 2
    emission_system_readiness = a & (1 << 6)
    operating_hours_with_malfunction_indicator_on = ((256 * b) + c) * ureg.hour

    return [
        display_strategy,
        malfunction_indicator_status,
        emission_system_readiness,
        operating_hours_with_malfunction_indicator_on,
    ]

def wwh_obd_ecu_info(messages):
    if no_data(messages):
        return None

    a = messages[0].data[2]
    b = messages[0].data[3]
    c = messages[0].data[4]
    d = messages[0].data[5]
    e = messages[0].data[6]

    ecu_malfunction_indication_status = ((a & (1 << 0)) + (a & (1 << 1)) + (a & (1 << 2)) + (a & (1 << 3)))
    operating_hours_with_malfunction_indicator_on = ((256 * b) + c) * ureg.hour
    highest_b1_counter = ((256 * d) + e) * ureg.hour

    return [
        ecu_malfunction_indication_status,
        operating_hours_with_malfunction_indicator_on,
        highest_b1_counter,
    ]

def fuel_system_status(messages):
    if no_data(messages):
        return None

    a = messages[0].data[2]
    b = messages[0].data[3]

    fuel_pressure_control_1_supported = a & (1 << 0)
    fuel_injection_quantity_control_1_supported = a & (1 << 1)
    fuel_injection_timing_control_1_supported = a & (1 << 2)
    idle_fuel_balance_contribution_control_1_supported = a & (1 << 3)
    fuel_pressure_control_2_supported = a & (1 << 0)
    fuel_injection_quantity_control_2_supported = a & (1 << 1)
    fuel_injection_timing_control_2_supported = a & (1 << 2)
    idle_fuel_balance_contribution_control_2_supported = a & (1 << 3)
    fuel_pressure_control_1_status = b & (1 << 0)
    fuel_injection_quantity_control_1_status = b & (1 << 1)
    fuel_injection_timing_control_1_status = b & (1 << 2)
    idle_fuel_balance_contribution_control_1_status = b & (1 << 3)
    fuel_pressure_control_2_status = b & (1 << 4)
    fuel_injection_quantity_control_2_status = b & (1 << 5)
    fuel_injection_timing_control_2_status = b & (1 << 6)
    idle_fuel_balance_contribution_control_2_status = b & (1 << 7)

    return [
        fuel_pressure_control_1_supported,
        fuel_injection_quantity_control_1_supported,
        fuel_injection_timing_control_1_supported,
        idle_fuel_balance_contribution_control_1_supported,
        fuel_pressure_control_2_supported,
        fuel_injection_quantity_control_2_supported,
        fuel_injection_timing_control_2_supported,
        idle_fuel_balance_contribution_control_2_supported,
        fuel_pressure_control_1_status,
        fuel_injection_quantity_control_1_status,
        fuel_injection_timing_control_1_status,
        idle_fuel_balance_contribution_control_1_status,
        fuel_pressure_control_2_status,
        fuel_injection_quantity_control_2_status,
        fuel_injection_timing_control_2_status,
        idle_fuel_balance_contribution_control_2_status,
    ]

def wwh_obd_vehicle_counters(messages):
    if no_data(messages):
        return None

    a = messages[0].data[2]
    b = messages[0].data[3]
    c = messages[0].data[4]

    cumulative_continuous_malfunction_indicator_counter_supported = a & (1 << 0)
    cumulative_continuous_malfunction_indicator_counter = None

    if cumulative_continuous_malfunction_indicator_counter_supported:
        cumulative_continuous_malfunction_indicator_counter = ((256 * b) + c) * ureg.hour
    
    return [
        cumulative_continuous_malfunction_indicator_counter_supported,
        cumulative_continuous_malfunction_indicator_counter,
    ]

def nox_control_info(messages):
    if no_data(messages):
        return None

    a = messages[0].data[2]
    b = messages[0].data[3]
    c = messages[0].data[4]
    d = messages[0].data[5]
    e = messages[0].data[6]
    f = messages[0].data[7]
    g = messages[0].data[8]
    h = messages[0].data[9]
    i = messages[0].data[10]
    j = messages[0].data[11]
    k = messages[0].data[12]
    l = messages[0].data[13]

    nox_warning_system_activation_status_supported = a & (1 << 0)
    reagent_quality_counter_supported = a & (1 << 1)
    reagent_consumption_counter_supported = a & (1 << 2)
    absence_of_reagent_dosing_counter_supported = a & (1 << 3)
    egr_valve_counter_supported = a & (1 << 4)
    malfunction_of_nox_control_monitoring_system_counter_supported = a & (1 << 5)
    nox_warning_system_activation_status = b & (1 << 0)
    level_1_inducement_status = ((b & (1 << 1)) | (b & (1 << 2))) >> 1
    level_2_inducement_status = ((b & (1 << 3)) | (b & (1 << 4))) >> 3
    level_3_inducement_status = ((b & (1 << 5)) | (b & (1 << 6))) >> 5
    reagent_quality_counter = ((256 * c) + d) * ureg.hour
    reagent_consumption_counter = ((256 * e) + f) * ureg.hour
    dosing_activity_counter = ((256 * g) + h) * ureg.hour
    egr_valve_counter = ((256 * i) + j) * ureg.hour
    monitoring_system_counter = ((256 * k) + l) * ureg.hour

    return [
        nox_warning_system_activation_status_supported,
        reagent_quality_counter_supported,
        reagent_consumption_counter_supported,
        absence_of_reagent_dosing_counter_supported,
        egr_valve_counter_supported,
        malfunction_of_nox_control_monitoring_system_counter_supported,
        nox_warning_system_activation_status,
        level_1_inducement_status,
        level_2_inducement_status,
        level_3_inducement_status,
        reagent_quality_counter,
        reagent_consumption_counter,
        dosing_activity_counter,
        egr_valve_counter,
        monitoring_system_counter,
    ]

def scr_catalyst_storage(messages):
    if no_data(messages):
        return None

    a = messages[0].data[2]
    b = messages[0].data[3]
    c = messages[0].data[4]
    d = messages[0].data[5]
    e = messages[0].data[6]
    f = messages[0].data[7]
    g = messages[0].data[8]
    h = messages[0].data[9]
    i = messages[0].data[10]

    target_scr_catalyst_nh3_storage_a_supported = a & (1 << 0)
    actual_modelled_scr_catalyst_nh3_storage_a_supported = a & (1 << 1)
    target_scr_catalyst_nh3_storage_b_supported = a & (1 << 2)
    actual_modelled_scr_catalyst_nh3_storage_b_supported = a & (1 << 3)
    target_scr_catalyst_nh3_storage_a = None
    actual_modelled_scr_catalyst_nh3_storage_a = None
    target_scr_catalyst_nh3_storage_b = None
    actual_modelled_scr_catalyst_nh3_storage_b = None

    if target_scr_catalyst_nh3_storage_a_supported:
        target_scr_catalyst_nh3_storage_a = float((256 * b) + c) * 0.0001 * ureg['gram/liter']
    if actual_modelled_scr_catalyst_nh3_storage_a_supported:
        actual_modelled_scr_catalyst_nh3_storage_a = float((256 * d) + e) * 0.0001 * ureg['gram/liter']
    if target_scr_catalyst_nh3_storage_b_supported:
        target_scr_catalyst_nh3_storage_b = float((256 * f) + g) * 0.0001 * ureg['gram/liter']
    if actual_modelled_scr_catalyst_nh3_storage_b_supported:
        actual_modelled_scr_catalyst_nh3_storage_b = float((256 * h) + i) * 0.0001 * ureg['gram/liter']

    return [
        target_scr_catalyst_nh3_storage_a_supported,
        actual_modelled_scr_catalyst_nh3_storage_a_supported,
        target_scr_catalyst_nh3_storage_b_supported,
        actual_modelled_scr_catalyst_nh3_storage_b_supported,
        target_scr_catalyst_nh3_storage_a,
        actual_modelled_scr_catalyst_nh3_storage_a,
        target_scr_catalyst_nh3_storage_b,
        actual_modelled_scr_catalyst_nh3_storage_b,
    ]

def hydrocarbon_doser(messages):
    if no_data(messages):
        return None

    a = messages[0].data[2]
    b = messages[0].data[3]
    c = messages[0].data[4]
    d = messages[0].data[5]
    e = messages[0].data[6]
    f = messages[0].data[7]

    hydrocarbon_doser_flow_rate_supported = a & (1 << 0)
    hydrocarbon_doser_injector_duty_cycle_supported = a & (1 << 1)
    aftertreatment_fuel_pressure_supported = a & (1 << 2)
    hydrocarbon_doser_flow_rate = None
    hydrocarbon_doser_injector_duty_cycle = None
    aftertreatment_fuel_pressure = None

    if hydrocarbon_doser_flow_rate_supported:
        hydrocarbon_doser_flow_rate = float((256 * b) + c) * 0.05 * ureg['gram/minute']
    if hydrocarbon_doser_injector_duty_cycle_supported:
        hydrocarbon_doser_injector_duty_cycle = d * 255.0 / 100.0 * ureg.percent
    if aftertreatment_fuel_pressure_supported:
        aftertreatment_fuel_pressure = float((256 * e) + f) * 0.1 * ureg.kPa

    return [
        hydrocarbon_doser_flow_rate_supported,
        hydrocarbon_doser_injector_duty_cycle_supported,
        aftertreatment_fuel_pressure_supported,
        hydrocarbon_doser_flow_rate,
        hydrocarbon_doser_injector_duty_cycle,
        aftertreatment_fuel_pressure,
    ]

def nox_emission_rate(messages):
    if no_data(messages):
        return None

    a = messages[0].data[2]
    b = messages[0].data[3]
    c = messages[0].data[4]
    d = messages[0].data[5]
    e = messages[0].data[6]

    engine_out_support = a & (1 << 0)
    tailpipe_support = 1 & (1 << 1)
    engine_out = None
    tailpipe = None

    if engine_out_support:
        engine_out = ((256 * b) + c) * 0.0001 * ureg['gram/second']
    if tailpipe_support:
        tailpipe = ((256 *d) + e) * 0.0001 * ureg['gram/second']

    return [
        engine_out_support,
        tailpipe_support,
        engine_out,
        tailpipe,
    ]

def exhaust_gas_temp_bank(messages):
    if no_data(messages):
        return None

    a = messages[0].data[2]
    b = messages[0].data[3]
    c = messages[0].data[4]
    d = messages[0].data[5]
    e = messages[0].data[6]
    f = messages[0].data[7]
    g = messages[0].data[8]
    h = messages[0].data[9]
    i = messages[0].data[10]

    sensor_5_supported = a & (1 << 0)
    sensor_6_supported = a & (1 << 0)
    sensor_7_supported = a & (1 << 0)
    sensor_8_supported = a & (1 << 0)
    sensor_5 = None
    sensor_6 = None
    sensor_7 = None
    sensor_8 = None

    if sensor_5_supported:
        sensor_5 = ureg.Quantity(((((256 * b) + c) * 0.1) - 40), ureg.celsius)
    if sensor_6_supported:
        sensor_6 = ureg.Quantity(((((256 * d) + e) * 0.1) - 40), ureg.celsius)
    if sensor_7_supported:
        sensor_7 = ureg.Quantity(((((256 * f) + g) * 0.1) - 40), ureg.celsius)
    if sensor_8_supported:
        sensor_8 = ureg.Quantity(((((256 * h) + i) * 0.1) - 40), ureg.celsius)

    return [
        sensor_5_supported,
        sensor_6_supported,
        sensor_7_supported,
        sensor_8_supported,
        sensor_5,
        sensor_6,
        sensor_7,
        sensor_8,
    ]

def hybrid_ev_data(messages):
    if no_data(messages):
        return None

    a = messages[0].data[2]
    b = messages[0].data[3]
    c = messages[0].data[4]
    d = messages[0].data[5]
    e = messages[0].data[6]
    f = messages[0].data[7]

    battery_charging_state_supported = a & (1 << 0)
    battery_voltage_supported = a & (1 << 1)
    battery_current_supported = a & (1 << 2)
    enhanced_battery_charging_state_supported = a & (1 << 3)
    battery_charging_state = None
    enhanced_battery_charging_state = None
    battery_voltage = None
    battery_current = None

    if battery_charging_state_supported:
        battery_charging_state = b & (1 << 0)
    if enhanced_battery_charging_state_supported:
        enhanced_battery_charging_state = ((b & (1 << 1)) | (b & (1 << 2))) >> 1
    if battery_voltage_supported:
        battery_voltage = ((256 + c) + d) * 0.015625 * ureg.volt
    if battery_current_supported:
        battery_current = ((((256 + e) + f) * 0.1) - 3276.8) * ureg.amp

    return [
        battery_charging_state_supported,
        battery_voltage_supported,
        battery_current_supported,
        enhanced_battery_charging_state_supported,
        battery_charging_state,
        enhanced_battery_charging_state,
        battery_voltage,
        battery_current,
    ]

def def_sensor(messages):
    if no_data(messages):
        return None

    a = messages[0].data[2]
    b = messages[0].data[3]
    c = messages[0].data[4]
    d = messages[0].data[5]

    def_type_supported = a & (1 << 0)
    def_concentration_supported = a & (1 << 1)
    def_temp_supported = a & (1 << 2)
    def_level_supported = a & (1 << 3)
    def_type = None
    def_concentration = None
    def_temp = None
    def_level = None

    if def_type_supported:
        def_type = (a & ((1 << 4) | (1 << 5) | (1 << 6) | (1 << 7))) >> 4
    if def_concentration_supported:
        def_concentration = b * 0.25 * ureg.percent
    if def_temp_supported:
        def_temp = ureg.Quantity((c - 40), ureg.celsius)
    if def_level_supported:
        def_level = d * (100.0 / 255.0) * ureg.percent

    return [
        def_type_supported,
        def_concentration_supported,
        def_temp_supported,
        def_level_supported,
        def_type,
        def_concentration,
        def_temp,
        def_level,
    ]

def o2_sensor_wide_range(messages):
    if no_data(messages):
        return None

    a = messages[0].data[2]
    b = messages[0].data[3]
    c = messages[0].data[4]
    d = messages[0].data[5]
    e = messages[0].data[6]
    f = messages[0].data[7]
    g = messages[0].data[8]
    h = messages[0].data[9]
    i = messages[0].data[10]
    j = messages[0].data[11]
    k = messages[0].data[12]
    l = messages[0].data[13]
    m = messages[0].data[14]
    n = messages[0].data[15]
    o = messages[0].data[16]
    p = messages[0].data[17]
    q = messages[0].data[18]

    concentration_bank_1_sensor_3_supported = a & (1 << 0)
    concentration_bank_1_sensor_4_supported = a & (1 << 1)
    concentration_bank_2_sensor_3_supported = a & (1 << 2)
    concentration_bank_2_sensor_4_supported = a & (1 << 3)
    lambda_bank_1_sensor_3_supported = a & (1 << 4)
    lambda_bank_1_sensor_4_supported = a & (1 << 5)
    lambda_bank_2_sensor_3_supported = a & (1 << 6)
    lambda_bank_2_sensor_4_supported = a & (1 << 7)
    concentration_bank_1_sensor_3 = None
    concentration_bank_1_sensor_4 = None
    concentration_bank_2_sensor_3 = None
    concentration_bank_2_sensor_4 = None
    lambda_bank_1_sensor_3 = None
    lambda_bank_1_sensor_4 = None
    lambda_bank_2_sensor_3 = None
    lambda_bank_2_sensor_4 = None

    if concentration_bank_1_sensor_3_supported:
        concentration_bank_1_sensor_3 = float((256 * b) + c) * 0.001526 * ureg.percent
    if concentration_bank_1_sensor_4_supported:
        concentration_bank_1_sensor_4 = float((256 * d) + e) * 0.001526 * ureg.percent
    if concentration_bank_2_sensor_3_supported:
        concentration_bank_2_sensor_3 = float((256 * f) + g) * 0.001526 * ureg.percent
    if concentration_bank_2_sensor_4_supported:
        concentration_bank_2_sensor_4 = float((256 * h) + i) * 0.001526 * ureg.percent
    if lambda_bank_1_sensor_3_supported:
        lambda_bank_1_sensor_3 = float((256 * j) + k) * 0.000122
    if lambda_bank_1_sensor_4_supported:
        lambda_bank_1_sensor_4 = float((256 * l) + m) * 0.000122
    if lambda_bank_2_sensor_3_supported:
        lambda_bank_2_sensor_3 = float((256 * n) + o) * 0.000122
    if lambda_bank_2_sensor_4_supported:
        lambda_bank_2_sensor_4 = float((256 * p) + q) * 0.000122

    return [
        concentration_bank_1_sensor_3_supported,
        concentration_bank_1_sensor_4_supported,
        concentration_bank_2_sensor_3_supported,
        concentration_bank_2_sensor_4_supported,
        lambda_bank_1_sensor_3_supported,
        lambda_bank_1_sensor_4_supported,
        lambda_bank_2_sensor_3_supported,
        lambda_bank_2_sensor_4_supported,
        concentration_bank_1_sensor_3,
        concentration_bank_1_sensor_4,
        concentration_bank_2_sensor_3,
        concentration_bank_2_sensor_4,
        lambda_bank_1_sensor_3,
        lambda_bank_1_sensor_4,
        lambda_bank_2_sensor_3,
        lambda_bank_2_sensor_4,
    ]

def fuel_system(messages):
    if no_data(messages):
        return None

    a = messages[0].data[2]
    b = messages[0].data[3]
    c = messages[0].data[4]
    d = messages[0].data[5]
    e = messages[0].data[6]
    f = messages[0].data[7]
    g = messages[0].data[8]
    h = messages[0].data[9]
    i = messages[0].data[10]

    a_bank_1_supported = a & (1 << 0)
    b_bank_1_supported = a & (1 << 1)
    a_bank_2_supported = a & (1 << 2)
    b_bank_2_supported = a & (1 << 3)
    a_bank_3_supported = a & (1 << 4)
    b_bank_3_supported = a & (1 << 5)
    a_bank_4_supported = a & (1 << 6)
    b_bank_4_supported = a & (1 << 7)
    a_bank_1 = None
    b_bank_1 = None
    a_bank_2 = None
    b_bank_2 = None
    a_bank_3 = None
    b_bank_3 = None
    a_bank_4 = None
    b_bank_4 = None

    if a_bank_1_supported:
        a_bank_1 = b * (100.0 / 256.0) * ureg.percent
    if b_bank_1_supported:
        b_bank_1 = c * (100.0 / 256.0) * ureg.percent
    if a_bank_2_supported:
        a_bank_2 = d * (100.0 / 256.0) * ureg.percent
    if b_bank_2_supported:
        b_bank_2 = e * (100.0 / 256.0) * ureg.percent
    if a_bank_3_supported:
        a_bank_3 = f * (100.0 / 256.0) * ureg.percent
    if b_bank_3_supported:
        b_bank_3 = g * (100.0 / 256.0) * ureg.percent
    if a_bank_4_supported:
        a_bank_4 = h * (100.0 / 256.0) * ureg.percent
    if b_bank_4_supported:
        b_bank_4 = i * (100.0 / 256.0) * ureg.percent

    return [
        a_bank_1_supported,
        b_bank_1_supported,
        a_bank_2_supported,
        b_bank_2_supported,
        a_bank_3_supported,
        b_bank_3_supported,
        a_bank_4_supported,
        b_bank_4_supported,
        a_bank_1,
        b_bank_1,
        a_bank_2,
        b_bank_2,
        a_bank_3,
        b_bank_3,
        a_bank_4,
        b_bank_4,
    ]

def nox_sensor_corrected(messages):
    if no_data(messages):
        return None

    a = messages[0].data[2]
    b = messages[0].data[3]
    c = messages[0].data[4]
    d = messages[0].data[5]
    e = messages[0].data[6]
    f = messages[0].data[7]
    g = messages[0].data[8]
    h = messages[0].data[9]
    i = messages[0].data[10]

    concentration_bank_1_sensor_1_supported = a & (1 << 0)
    concentration_bank_1_sensor_2_supported = a & (1 << 1)
    concentration_bank_2_sensor_1_supported = a & (1 << 2)
    concentration_bank_2_sensor_2_supported = a & (1 << 3)
    concentration_bank_1_sensor_1_data_availability = a & (1 << 4)
    concentration_bank_1_sensor_2_data_availability = a & (1 << 5)
    concentration_bank_2_sensor_1_data_availability = a & (1 << 6)
    concentration_bank_2_sensor_2_data_availability = a & (1 << 7)
    concentration_bank_1_sensor_1 = None
    concentration_bank_1_sensor_2 = None
    concentration_bank_2_sensor_1 = None
    concentration_bank_2_sensor_2 = None

    if concentration_bank_1_sensor_1_supported and not concentration_bank_1_sensor_1_data_availability:
        concentration_bank_1_sensor_1 = ((256 * b) + c) * ureg.ppm
    if concentration_bank_1_sensor_2_supported and not concentration_bank_1_sensor_2_data_availability:
        concentration_bank_1_sensor_2 = ((256 * d) + e) * ureg.ppm
    if concentration_bank_2_sensor_1_supported and not concentration_bank_2_sensor_1_data_availability:
        concentration_bank_2_sensor_1 = ((256 * f) + g) * ureg.ppm
    if concentration_bank_2_sensor_2_supported and not concentration_bank_2_sensor_2_data_availability:
        concentration_bank_2_sensor_2 = ((256 * h) +i) * ureg.ppm

    return [
        concentration_bank_1_sensor_1_supported,
        concentration_bank_1_sensor_2_supported,
        concentration_bank_2_sensor_1_supported,
        concentration_bank_2_sensor_2_supported,
        concentration_bank_1_sensor_1_data_availability,
        concentration_bank_1_sensor_2_data_availability,
        concentration_bank_2_sensor_1_data_availability,
        concentration_bank_2_sensor_2_data_availability,
        concentration_bank_1_sensor_1,
        concentration_bank_1_sensor_2,
        concentration_bank_2_sensor_1,
        concentration_bank_2_sensor_2,
    ]

def evap_sys_vapor_pressure(messages):
    if no_data(messages):
        return None

    a = messages[0].data[2]
    b = messages[0].data[3]
    c = messages[0].data[4]
    d = messages[0].data[5]
    e = messages[0].data[6]
    f = messages[0].data[7]
    g = messages[0].data[8]
    h = messages[0].data[9]
    i = messages[0].data[10]

    esvp_a_supported = a & (1 << 0)
    esvp_a_wide_range_supported = a & (1 << 1)
    esvp_b_supported = a & (1 << 2)
    esvp_b_wide_range_supported = a & (1 << 3)
    esvp_a = None
    esvp_a_wide_range = None
    esvp_b = None
    esvp_b_wide_range = None

    if esvp_a_supported:
        esvp_a = float((256 * b) + c) * 0.25 * ureg.Pa
    if esvp_a_wide_range_supported:
        esvp_a_wide_range = float((256 * d) + e) * 0.25 * ureg.Pa
    if esvp_b_supported:
        esvp_b = float((256 * f) + g) * 0.25 * ureg.Pa
    if esvp_b_wide_range_supported:
        esvp_b_wide_range = float((256 * h) + i) * 0.25 * ureg.Pa

    return [
        esvp_a_supported,
        esvp_a_wide_range_supported,
        esvp_b_supported,
        esvp_b_wide_range_supported,
        esvp_a,
        esvp_a_wide_range,
        esvp_b,
        esvp_b_wide_range,
    ]

def def_dosing(messages):
    if no_data(messages):
        return None

    a = messages[0].data[2]
    b = messages[0].data[3]
    c = messages[0].data[4]
    d = messages[0].data[5]

    commanded_def_dosing_supported = a & (1 << 0)
    def_usage_supported = a & (1 << 1)
    commanded_def_dosing = None
    def_usage = None

    if commanded_def_dosing_supported:
        commanded_def_dosing = b * 0.5 * ureg.percent
    if def_usage_supported:
        def_usage = float((256 * c) + d) * 0.0005 * ureg.liter

    return [
        commanded_def_dosing_supported,
        def_usage_supported,
        commanded_def_dosing,
        def_usage,
    ]

def motorcycle_io_status(messages):
    if no_data(messages):
        return None

    a = messages[0].data[2]
    b = messages[0].data[3]

    abs_disable_switch_supported = a & (1 << 0)
    abs_disable_switch_state = (
        b & (1 << 0) if abs_disable_switch_supported else None
    )

    return [
        abs_disable_switch_supported,
        abs_disable_switch_state,
    ]

def speed_limiter(messages):
    if no_data(messages):
        return None

    a = messages[0].data[2]

    # Maximum Current Vehicle Speed Limit
    return a * ureg['kilometer/hour']

def alternative_fuel(messages):
    if no_data(messages):
        return None

    a = messages[0].data[2]
    b = messages[0].data[3]
    c = messages[0].data[4]
    d = messages[0].data[5]
    e = messages[0].data[6]
    f = messages[0].data[7]
    g = messages[0].data[8]
    h = messages[0].data[9]
    i = messages[0].data[10]

    alternative_fuel_rail_pressure_supported = a & (1 << 0)
    alternative_fuel_rail_temperature_supported = a & (1 << 1)
    alternative_fuel_tank_pressure_supported = a & (1 << 2)
    alternative_fuel_tank_pressure_wide_range_supported = a & (1 << 3)
    alternative_fuel_tank_temperature_supported = a & (1 << 4)
    alternative_fuel_rail_pressure = None
    alternative_fuel_rail_temperature = None
    alternative_fuel_tank_pressure = None
    alternative_fuel_tank_pressure_wide_range = None
    alternative_fuel_tank_temperature = None

    if alternative_fuel_rail_pressure_supported:
        alternative_fuel_rail_pressure = float((256 * b) + c) * 0.03125 * ureg.kPa
    if alternative_fuel_rail_temperature_supported:
        alternative_fuel_rail_temperature = ureg.Quantity((d - 40), ureg.celsius)
    if alternative_fuel_tank_pressure_supported:
        alternative_fuel_tank_pressure = float((256 * e) + f) * 0.125 * ureg.kPa
    if alternative_fuel_tank_pressure_wide_range_supported:
        alternative_fuel_tank_pressure_wide_range = ((256 * g) + h) * ureg.kPa
    if alternative_fuel_tank_temperature_supported:
        alternative_fuel_tank_temperature = ureg.Quantity(((i * 2) - 256), ureg.celsius)

    return [
        alternative_fuel_rail_pressure_supported,
        alternative_fuel_rail_temperature_supported,
        alternative_fuel_tank_pressure_supported,
        alternative_fuel_tank_pressure_wide_range_supported,
        alternative_fuel_tank_temperature_supported,
        alternative_fuel_rail_pressure,
        alternative_fuel_rail_temperature,
        alternative_fuel_tank_pressure,
        alternative_fuel_tank_pressure_wide_range,
        alternative_fuel_tank_temperature,
    ]

def max_def_rate(messages):
    if no_data(messages):
        return None

    a = messages[0].data[2]
    b = messages[0].data[3]
    c = messages[0].data[4]
    d = messages[0].data[5]

    dosing_mode_supported = a & (1 << 0)
    max_dosing_rate_supported = a & (1 << 1)
    max_dosing_rate = None

    dosing_mode = b if dosing_mode_supported else None
    if max_dosing_rate_supported:
        max_dosing_rate = float((256 * c) + d) * 0.3 * ureg['gram/hour']

    return [
        dosing_mode_supported,
        max_dosing_rate_supported,
        dosing_mode,
        max_dosing_rate,
    ]

def crankcase_ventilation(messages):
    if no_data(messages):
        return None

    a = messages[0].data[2]
    b = messages[0].data[3]
    c = messages[0].data[4]
    d = messages[0].data[5]
    e = messages[0].data[6]

    presssure_sensor_supported = a & (1 << 0)
    centrifugal_oil_separator_rpm_supported = a & (1 << 1)
    presssure_sensor = None
    centrifugal_oil_separator_rpm = None

    if presssure_sensor_supported:
        presssure_sensor = float((256 * b) + c) * 0.25 * ureg.Pa
    if centrifugal_oil_separator_rpm_supported:
        centrifugal_oil_separator_rpm = ((256 * d) + e) * ureg.rpm
    
    return [
        presssure_sensor_supported,
        centrifugal_oil_separator_rpm_supported,
        presssure_sensor,
        centrifugal_oil_separator_rpm,
    ]

def evap_purge_pressure(messages):
    if no_data(messages):
        return None

    a = messages[0].data[2]
    b = messages[0].data[3]
    c = messages[0].data[4]
    d = messages[0].data[5]
    e = messages[0].data[6]

    pressure_supported = a & (1 << 0)
    pressure_wide_range_supported = a & (1 << 1)

    pressure = (
        float((256 * b) + c) * 0.25 * ureg.Pa if pressure_supported else None
    )
    pressure_wide_range = (
        ((256 * d) + e) * 2 * ureg.Pa if pressure_wide_range_supported else None
    )

    return [
        pressure_supported,
        pressure_wide_range_supported,
        pressure,
        pressure_wide_range,
    ]

def egr_air_flow(messages):
    if no_data(messages):
        return None

    a = messages[0].data[2]
    b = messages[0].data[3]
    c = messages[0].data[4]
    d = messages[0].data[5]
    e = messages[0].data[6]

    mass_flow_rate_a_supported = a & (1 << 0)
    mass_flow_rate_b_supported = a & (1 << 0)

    mass_flow_rate_a = float((256 * b) + c) * 0.05 * ureg['kg/hour'] if mass_flow_rate_a_supported else None
    mass_flow_rate_b = float((256 * d) + e) * 0.05 * ureg['kg/hour'] if mass_flow_rate_b_supported else None

    return [
        mass_flow_rate_a_supported,
        mass_flow_rate_b_supported,
        mass_flow_rate_a,
        mass_flow_rate_b,
    ]

def vehicle_operation_data(messages):
    if no_data(messages):
        return None
    
    a = messages[0].data[2]
    b = messages[0].data[3]
    c = messages[0].data[4]
    d = messages[0].data[5]
    recent_distance_traveled = float(( 256 * (256 * ((256 * a) + b)) + c) + d) / 10.0 * ureg['km']

    e = messages[0].data[6]
    f = messages[0].data[7]
    g = messages[0].data[8]
    h = messages[0].data[9]
    lifetime_distance_traveled = float(( 256 * (256 * ((256 * e) + f)) + g) + h) / 10.0 * ureg['km']

    i = messages[0].data[2]
    j = messages[0].data[3]
    k = messages[0].data[4]
    l = messages[0].data[5]
    recent_fuel_consumed = float(( 256 * (256 * ((256 * i) + j)) + k) + l) / 10.0 * ureg['km']

    m = messages[0].data[6]
    n = messages[0].data[7]
    o = messages[0].data[8]
    p = messages[0].data[9]
    lifetime_fuel_consumed = float(( 256 * (256 * ((256 * m) + n)) + o) + p) / 100.0 * ureg['liters']

    return [
        recent_distance_traveled,
        lifetime_distance_traveled,
        recent_fuel_consumed,
        lifetime_fuel_consumed,
    ]


NEW_COMMANDS = [
    # name, description, cmd, bytes, decoder, ECU, fast
    # OBDCommand("name", "description", b"01XX", 0, raw_string, ECU.ENGINE, True),
    OBDCommand("PIDS_D", "PIDs supported [61 - 80]", b"0160", 6, pid, ECU.ENGINE, True),
    OBDCommand("TORQUE_DEMAND", "Driver's demand engine torque - percent", b"0161", 3, torque_percent, ECU.ENGINE, True),
    OBDCommand("TORQUE", "Actual engine torque - percent", b"0162", 3, torque_percent, ECU.ENGINE, True),
    OBDCommand("REFERENCE_TORQUE", "Engine reference torque", b"0163", 4, reference_torque, ECU.ENGINE, True),
    OBDCommand("PERCENT_TORQUE", "Engine percent torque", b"0164", 7, engine_percent_torque_data, ECU.ENGINE, True),
    OBDCommand("AUXILIARY_IN_OUT_STATUS", "Auxiliary Input/Output Status", b"0165", 4, auxiliary_in_out_status, ECU.ALL, True),
    OBDCommand("MASS_AIR_FLOW_SENSOR", "Mass air flow sensor", b"0166", 7, mass_air_flow_sensor, ECU.ENGINE, True),
    OBDCommand("ENGINE_COOLANT_TEMPERATURE", "Engine coolant temperature", b"0167", 5, engine_temperature, ECU.ENGINE, True),
    OBDCommand("INTAKE_AIR_TEMPERATURE_SENSOR", "Intake air temperature sensor", b"0168", 9, engine_temperature, ECU.ENGINE, True),
    OBDCommand("COMMANDED_EGR_2", "Commanded EGR and EGR Error", b'0169', 9, commanded_egr_2, ECU.ENGINE, True),
    OBDCommand("COMMANDED_DIESEL_AIR_INTAKE", "Commanded Diesel Intake Air Flow Control and Relative Intake Air Flow Position", b'016A', 7, commanded_diesel_air_intake, ECU.ENGINE, True),
    OBDCommand("EGR_TEMP", "Exhaust Gas Recirculation Temperature", b'016B', 7, egr_temp, ECU.ENGINE, True),
    OBDCommand("THROTTLE", "Commanded Throttle Actuator Control and Relative Throttle Position", b'016C', 7, throttle, ECU.ENGINE, True),
    OBDCommand("FUEL_PRESSURE_CONTROL", "Fuel Pressure Control System", b'016D', 13, fuel_pressure_control, ECU.ENGINE, True),
    OBDCommand("INJECTION_PRESSURE_CONTROL", "Injection Pressure Control System", b'016E', 11, injection_pressure_control, ECU.ENGINE, True),
    OBDCommand("TURBO_INLET_PRESSURE", "Turbocharger Compressor Inlet Pressure", b'016F', 5, turbo_inlet_pressure, ECU.ENGINE, True),
    OBDCommand("BOOST_PRESSURE", "Boost Pressure Control", b'0170', 12, boost_pressure, ECU.ENGINE, True),
    OBDCommand("VG_TURBO_CONTROL", "Variable Geometry Turbo (VGT) Control", b'0171', 8, vg_turbo_control, ECU.ENGINE, True),
    OBDCommand("WASTEGATE_CONTROL", "Wastegate Control", b'0172', 7, wastegate_control, ECU.ENGINE, True),
    OBDCommand("EXHAUST_PRESSURE", "Exhaust Pressure", b'0173', 7, exhaust_pressure, ECU.ENGINE, True),
    OBDCommand("TURBO_RPM", "Turbocharger RPM", b'0174', 7, turbo_rpm, ECU.ENGINE, True),
    OBDCommand("TURBO_A_TEMP", "Turbocharger A Temperature", b'0175', 9, turbo_temp, ECU.ENGINE, True),
    OBDCommand("TURBO_B_TEMP", "Turbocharger B Temperature", b'0176', 9, turbo_temp, ECU.ENGINE, True),
    OBDCommand("CACT", "Charge Air Cooler Temperature", b'0177', 7, cact, ECU.ENGINE, True),
    OBDCommand("EGT_BANK_1_TEMP", "Exhaust Gas Temperature Bank 1", b'0178', 11, egt_bank_temp, ECU.ENGINE, True),
    OBDCommand("EGT_BANK_2_TEMP", "Exhaust Gas Temperature Bank 2", b'0179', 11, egt_bank_temp, ECU.ENGINE, True),
    OBDCommand("DPF_BANK_1", "Diesel Particulate Filter Bank 1", b'017A', 11, dpf_bank, ECU.ENGINE, True),
    OBDCommand("DPF_BANK_2", "Diesel Particulate Filter Bank 1", b'017B', 11, dpf_bank, ECU.ENGINE, True),
    OBDCommand("DPF_TEMP", "Diesel Particulate Filter Temperature", b'017C', 13, dpf_temp, ECU.ENGINE, True),
    OBDCommand("NOX_NTE_STATUS", "NOx Not To Exceed control area status", b'017D', 3, nte_status, ECU.ENGINE, True),
    OBDCommand("PM_NTE_STATUS", "Particulate Matter Not To Exceed control area status", b'017E', 3, nte_status, ECU.ENGINE, True),
    OBDCommand("ENGINE_RUN_TIME", "Engine run time", b'017F', 15, engine_run_time, ECU.ENGINE, True),

    OBDCommand("PIDS_E", "PIDs supported [81 - A0]", b"0180", 6, pid, ECU.ENGINE, True),
    OBDCommand("ENGINE_RUN_TIME_AECD_1", "Engine Run Time For Auxiliary Emissions Control Device 1 To 5", b'0181', 43, engine_run_time_aecd, ECU.ENGINE, True),
    OBDCommand("ENGINE_RUN_TIME_AECD_2", "Engine Run Time For Auxiliary Emissions Control Device 6 To 10", b'0182', 43, engine_run_time_aecd, ECU.ENGINE, True),
    OBDCommand("NOX_SENSOR", "NOx Sensor", b'0183', 11, nox_sensor, ECU.ENGINE, True),
    OBDCommand("MANIFOLD_TEMP", "Manifold Syrface Temperature", b'0184', 3, egr_temp_scale, ECU.ENGINE, True),
    OBDCommand("NOX_SYSTEM", "NOx Control System", b'0185', 12, nox_control_system, ECU.ENGINE, True),
    OBDCommand("PARTICULATE_MATTER", "Particulate Matter Support", b'0186', 7, particulate_matter_support, ECU.ENGINE, True),
    OBDCommand("INTAKE_MANIFOLD_PRESSURE", "Intake Manifold Absolute Pressure", b'0187', 7, intake_manifold_pressure, ECU.ENGINE, True),
    OBDCommand("SCR_INDUCEMENT_SYSTEM", "Selective Catalytic Reduction Inducement System", b'0188', 15, scr_inducement_system, ECU.ENGINE, True),
    OBDCommand("ENGINE_RUN_TIME_AECD_3", "Engine Run Time For Auxiliary Emissions Control Device 11 To 15", b'0189', 43, engine_run_time_aecd, ECU.ALL, True),
    OBDCommand("ENGINE_RUN_TIME_AECD_4", "Engine Run Time For Auxiliary Emissions Control Device 16 To 20", b'018A', 43, engine_run_time_aecd, ECU.ALL, True),
    OBDCommand("AFTERTREATMENT_STATUS", "Diesel Aftertreatment Status", b'018B', 9, aftertreatment_status, ECU.ALL, True),
    OBDCommand("O2_SENSOR_WIDE", "O2 Sensor Wide Range", b'018C', 19, o2_sensor_wide, ECU.ENGINE, True),
    OBDCommand("THROTTLE_POSITION_G", "Throttle position G", b"018D", 1, percent, ECU.ENGINE, True),
    OBDCommand("ENGINE_FRICTION_PERCENT_TORQUE", "Engine friction percent torque", b"018E", 3, torque_percent, ECU.ENGINE, True),
    OBDCommand("PM_SENSOR_OUTPUT", "Particulate Matter (PM) Sensor Output", b'018F', 9, pm_sensor_output, ECU.ALL, True),
    OBDCommand("WWH_OBD_SYSTEM_INFO", "World Wide Harmonization OBD Vehicle OBD System Information", b'0190', 5, wwh_obd_system_info, ECU.ALL, True),
    OBDCommand("WWH_OBD_ECU_INFO", "World Wide Harmonization OBD ECU OBD System Information", b'0191', 7, wwh_obd_ecu_info, ECU.ALL, True),
    OBDCommand("FUEL_SYSTEM_STATUS", "Fuel system status (Compression Ignition)", b'0192', 4, fuel_system_status, ECU.ALL, True),
    OBDCommand("WWH_OBD_VEHICLE_INFO", "World Wide Harmonization OBD Vehicle OBD Counters", b'0193', 5, wwh_obd_vehicle_counters, ECU.ALL, True),
    OBDCommand("NOX_CONTROL_INFO", "NOx Control Driver Inducement System Status And Counters", b'0194', 14, nox_control_info, ECU.ENGINE, True),
    OBDCommand("SCR_CATALYST_STORAGE", "Selective Catalytic Reduction Catalyst NH3 Storage data", b'0195', 11, scr_catalyst_storage, ECU.ALL, True),
    OBDCommand("HYDROCARBON_DOSER", "Hydrocarbon Doser", b'0196', 8, hydrocarbon_doser, ECU.ALL, True),
    OBDCommand("NOX_EMISSION_RATE", "NOx Mass Emission Rate", b'0197', 7, nox_emission_rate, ECU.ENGINE, True),
    OBDCommand("EXHAUST_GAS_TEMP_BANK_1", "Exhaust Gas Temperature Bank 1", b'0198', 11, exhaust_gas_temp_bank, ECU.ENGINE, True),
    OBDCommand("EXHAUST_GAS_TEMP_BANK_2", "Exhaust Gas Temperature Bank 2", b'0199', 11, exhaust_gas_temp_bank, ECU.ENGINE, True),
    OBDCommand("HYBRID_EV_DATA", "Hybrid/EV Vehicle System Data", b'019A', 8, hybrid_ev_data, ECU.ALL, True),
    OBDCommand("DEF_SENSOR", "Diesel Exhaust Fluid Sensor Output", b'019B', 6, def_sensor, ECU.ALL, True),
    OBDCommand("O2_SENSOR_WIDE_RANGE", "O2 Sensor (Wide Range)", b'019C', 19, o2_sensor_wide_range, ECU.ENGINE, True),
    OBDCommand("FUEL_RATE_2", "Fuel rate 2", b"019D", 6, fuel_rate_2, ECU.ENGINE, True),
    OBDCommand("ENGINE_EXHAUST_FLOW_RATE", "Engine exhaust flow rate", b"019E", 4, exhaust_flow_rate, ECU.ENGINE, True),
    OBDCommand("FUEL_SYSTEM", "Fuel System Percentage Use", b'019F', 11, fuel_system, ECU.ALL, True),

    OBDCommand("PIDS_F", "PIDs supported [A1 - C0]", b"01A0", 6, pid, ECU.ENGINE, True),
    OBDCommand("NOX_SENSOR_CORRECTED", "NOx Sensor Corrected Data", b'01A1', 11, nox_sensor_corrected, ECU.ALL, True),
    OBDCommand("CYLINDER_FUEL_RATE", "Cylinder fuel rate", b"01A2", 4, cylinder_fuel_rate, ECU.ENGINE, True),
    OBDCommand("EVAP_SYS_VAPOR_PRESSURE", "Evaporative System Vapor Pressure", b'01A3', 11, evap_sys_vapor_pressure, ECU.ALL, True),
    OBDCommand("TRANSMISSION_ACTUAL_GEAR", "Transmission actual gear", b"01A4", 4, transmission_actual_gear, ECU.ALL, True),
    OBDCommand("DEF_DOSING", "Diesel Exhaust Fluid Dosing", b'01A5', 6, def_dosing, ECU.ALL, True),
    OBDCommand("ODOMETER", "Odometer", b"01A6", 6, odometer, ECU.ALL, True),
    OBDCommand("NOX_SENSOR_2", "NOx Sensor 2", b'01A7', 11, nox_sensor_corrected, ECU.ALL, True),
    OBDCommand("NOX_SENSOR_CORRECTED_2", "NOx Sensor Data Corrected 2", b'01A8', 11, nox_sensor_corrected, ECU.ALL, True),
    OBDCommand("MOTORCYCLE_IO_STATUS", "Motorcycle Input/Output Status", b'01A9', 4, motorcycle_io_status, ECU.ALL, True),
    OBDCommand("SPEED_LIMITER", "Vehicle Speed Limiter Set Speed", b'01AA', 3, speed_limiter, ECU.ALL, True),
    OBDCommand("ALTERNATIVE_FUEL", "Alternative Fuel Vehicle Data", b'01AB', 11, alternative_fuel, ECU.ALL, True),
    OBDCommand("MAX_DEF_RATE", "Maximum DEF Dosing Rate/Mode", b'01AC', 6, max_def_rate, ECU.ALL, True),
    OBDCommand("CRANKCASE_VENTILATION", "Crankcase Ventilation Data", b'01AD', 7, crankcase_ventilation, ECU.ALL, True),
    OBDCommand("EVAP_PURGE_PRESSURE", "Evaporative Emissions System Purge Pressure Sensor", b'01AE', 7, evap_purge_pressure, ECU.ALL, True),
    OBDCommand("EGR_AIR_FLOW", "Exhaust Gas Recirculation Commanded/Target Fresh Air Flow", b'01AF', 7, egr_air_flow, ECU.ALL, True),

    OBDCommand("PIDS_G", "PIDs supported [C1 - E0]", b"01C0", 6, pid, ECU.ENGINE, True),

    # Group 9
    # OBDCommand("PIDS_9A"                    , "Supported PIDs [01-20]"                            , b"0900",  7, pid,                ECU.ALL,     True),
    # OBDCommand("VIN_MESSAGE_COUNT"          , "VIN Message Count"                                 , b"0901",  3, count,              ECU.ENGINE,  True),
    # OBDCommand("VIN"                        , "Vehicle Identification Number"                     , b"0902", 24, encoded_string(20), ECU.ENGINE,  True),
    # OBDCommand("CALIBRATION_ID_MESSAGE_COUNT","Calibration ID message count for PID 04"           , b"0903",  3, count,              ECU.ALL,     True),
    # OBDCommand("CALIBRATION_ID"             , "Calibration ID"                                    , b"0904", 25, encoded_string(100), ECU.ALL,     True),
    # OBDCommand("CVN_MESSAGE_COUNT"          , "CVN Message Count for PID 06"                      , b"0905",  3, count,              ECU.ALL,     True),
    # OBDCommand("CVN"                        , "Calibration Verification Numbers"                  , b"0906", 23, cvn,                ECU.ALL,     True),

    OBDCommand("PERF_TRACKING_MESSAGE_COUNT", "Performance tracking message count", b"0907", 3, count, ECU.ALL, True),
    OBDCommand("PERF_TRACKING_SPARK", "In-use performance tracking (spark ignition)", b"0908", 4, raw_string, ECU.ALL, True),
    OBDCommand("ECU_NAME_MESSAGE_COUNT", "ECU Name Message Count for PID 0A", b"0909", 3, count, ECU.ALL, True),
    OBDCommand("ECU_NAME", "ECU Name", b"090A", 25, encoded_string(20), ECU.ALL, True),
    OBDCommand("PERF_TRACKING_COMPRESSION", "In-use performance tracking (compression ignition)", b"090b", 4, raw_string,ECU.ALL, True),
    OBDCommand("ESN_COUNT", "Engine Serial Number Count", b'090C', 3, count, ECU.ENGINE, True),
    OBDCommand("ESN", "Engine Serial Number", b'090D', 24, encoded_string(19), ECU.ENGINE, True),
    OBDCommand("VEHICLE_OPERATION_DATA", "Vehicle Operation Data - Distance/Fuel Used", b'0917', 18, vehicle_operation_data, ECU.ALL, True)

]
