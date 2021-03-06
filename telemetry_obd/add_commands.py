# add_commands.py
# https://python-obd.readthedocs.io/en/latest/Custom%20Commands/
from obd import OBDCommand, ECU
from obd.decoders import pid, raw_string

NEW_COMMANDS = [
    # name, description, cmd, bytes, decoder, ECU, fast
    # OBDCommand("name", "description", b"01XX", 0, raw_string, ECU.ENGINE, True),
    OBDCommand("PID_D", "PIDs supported [61 - 80]", b"0160", 6, pid, ECU.ENGINE, True),

    OBDCommand("TORQUE_DEMAND", "Driver's demand engine torque - percent", b"0161", 1, raw_string, ECU.ENGINE, True),
    OBDCommand("TORQUE", "Actual engine torque - percent", b"0162", 1, raw_string, ECU.ENGINE, True),
    OBDCommand("REFERENCE_TORQUE", "Engine reference torque", b"0163", 2, raw_string, ECU.ENGINE, True),
    OBDCommand("PERCENT_TORQUE", "Engine percent torque", b"0164", 5, raw_string, ECU.ENGINE, True),
    OBDCommand("AUXILIARY_IO_SUPPORT", "Auxiliary input/output supported", b"0165", 2, raw_string, ECU.ENGINE, True),
    OBDCommand("MASS_AIRFLOW_SENSOR", "Mass airflow sensor", b"0166", 5, raw_string, ECU.ENGINE, True),
    OBDCommand("ENGINE_COOLANT_TEMPERATURE", "Engine coolant temperature", b"0167", 3, raw_string, ECU.ENGINE, True),
    OBDCommand("INTAKE_AIR_TEMPERATURE_SENSOR", "Intake air temperature sensor", b"0168", 7, raw_string, ECU.ENGINE, True),
    OBDCommand("EGR_DEMAND", "Commanded EGR and EGR error", b"0169", 7, raw_string, ECU.ENGINE, True),
    OBDCommand("DIESEL_AIR_INTAKE_DEMAND", "Commanded Diesel intake air flow control and relative intake air flow position", b"016A", 5, raw_string, ECU.ENGINE, True),
    OBDCommand("EXHAUST_GAS_RECIRCULATION_TEMP", "Exhaust recirculation temperature", b"016B", 5, raw_string, ECU.ENGINE, True),
    OBDCommand("THROTTLE_DEMAND", "Commanded throttle actuator demand and relative throttle position", b"016C", 5, raw_string, ECU.ENGINE, True),
    OBDCommand("FUEL_PRESSURE_CONTROL_SYSTEM", "Fuel pressure control system", b"016D", 6, raw_string, ECU.ENGINE, True),
    OBDCommand("INJECTION_PRESSURE_CONTROL_SYSTEM", "Injection pressure control system", b"016E", 5, raw_string, ECU.ENGINE, True),
    OBDCommand("TURBO_COMPRESSOR_IN_PRESSURE", "Turbocharger compressor inlet pressure", b"016F", 3, raw_string, ECU.ENGINE, True),
    OBDCommand("BOOST_PRESSURE_CONTROL", "Boost pressure control", b"0170", 9, raw_string, ECU.ENGINE, True),
    OBDCommand("VGT_CONTROL", "Variable geometry turbocharger (VGT) control", b"0171", 5, raw_string, ECU.ENGINE, True),
    OBDCommand("WASTEGATE_CONTROL", "Wastegate control", b"0172", 5, raw_string, ECU.ENGINE, True),
    OBDCommand("EXHAUST_PRESSURE", "Exhaust pressure", b"0173", 5, raw_string, ECU.ENGINE, True),
    OBDCommand("TURBO_RPM", "Turbocharger RPM", b"0174", 5, raw_string, ECU.ENGINE, True),
    OBDCommand("TURBO_TEMP_1", "Turbocharger temperature 1", b"0175", 7, raw_string, ECU.ENGINE, True),
    OBDCommand("TURBO_TEMP_2", "Turbocharger temperature 2", b"0176", 7, raw_string, ECU.ENGINE, True),
    OBDCommand("CACT", "Charge air cooler temperature (CACT)", b"0177", 5, raw_string, ECU.ENGINE, True),
    OBDCommand("EGT_1", "Exhaust gas temperature (EGT) bank 1", b"0178", 9, raw_string, ECU.ENGINE, True),
    OBDCommand("EGT_2", "Exhaust gas temperature (EGT) bank 2", b"0179", 9, raw_string, ECU.ENGINE, True),
    OBDCommand("DPF_1", "Diesel particulate filter (DPF) 1", b"017A", 7, raw_string, ECU.ENGINE, True),
    OBDCommand("DPF_2", "Diesel particulate filter (DPF) 2", b"017B", 7, raw_string, ECU.ENGINE, True),
    OBDCommand("DPF_TEMP", "Diesel particulate filter (DPF) temperature", b"017C", 9, raw_string, ECU.ENGINE, True),
    OBDCommand("NOX_NTE_STATUS", "NOx not-to-exceed (NTE) control area status", b"017D", 1, raw_string, ECU.ENGINE, True),
    OBDCommand("PM_NTE_STATUS", "Partiiculate Matter (PM) not-to-exceed (NTE) control area status", b"017E", 1, raw_string, ECU.ENGINE, True),
    OBDCommand("RUN_TIME", "Engine run time", b"017F", 13, raw_string, ECU.ENGINE, True),

    OBDCommand("PID_E", "PIDs supported [81 - A0]", b"0180", 6, pid, ECU.ENGINE, True),
    OBDCommand("AECD_RUNTIME_1", "Auxiliary emissions control device (AECD) runtime 1", b"0181", 21, raw_string, ECU.ENGINE, True),
    OBDCommand("AECD_RUNTIME_2", "Auxiliary emissions control device (AECD) runtime 2", b"0182", 21, raw_string, ECU.ENGINE, True),
    OBDCommand("NOX_SENSOR", "NOx sensor", b"0183", 5, raw_string, ECU.ENGINE, True),
    OBDCommand("MANIFOLD_SURFACE_SENSOR", "Manifold surface temperature", b"0184", 1, raw_string, ECU.ENGINE, True),
    OBDCommand("NOX_REAGENT_SYSTEM", "NOx Reagent System", b"0185", 10, raw_string, ECU.ENGINE, True),
    OBDCommand("PM_SENSOR", "Particulate matter (PM) sensor", b"0186", 5, raw_string, ECU.ENGINE, True),
    OBDCommand("INTAKE_MANIFOLD_PRESSURE", "Intake manifold absolute pressure", b"0187", 5, raw_string, ECU.ENGINE, True),
    OBDCommand("SCR_INDUCE_SYSTEM", "SCR induce system", b"0188", 13, raw_string, ECU.ENGINE, True),
    OBDCommand("AECD_RUNTIME_11_15", "Auxiliary emissions control device #11 - #15 runtime", b"0189", 41, raw_string, ECU.ENGINE, True),
    OBDCommand("AECD_RUNTIME_16_20", "Auxiliary emissions control device #16 - #20 runtime", b"018A", 41, raw_string, ECU.ENGINE, True),
    OBDCommand("DIESEL_AFTER_TREATMENT", "Diesel after treatment", b"018B", 7, raw_string, ECU.ENGINE, True),
    OBDCommand("WIDE_RANGE_O2_SENSOR", "Wide range O2 sensor", b"018C", 16, raw_string, ECU.ENGINE, True),
    OBDCommand("THROTTLE_POSITION_G", "Throttle position G", b"018D", 1, raw_string, ECU.ENGINE, True),
    OBDCommand("ENGINE_FRICTION_PERCENT_TORQUE", "Engine friction percent torque", b"018E", 1, raw_string, ECU.ENGINE, True),
    OBDCommand("PM_SENSOR_BANK_1_2", "Particulate matter (PM) sensor bank 1 and 2", b"018F", 5, raw_string, ECU.ENGINE, True),
    OBDCommand("WWHOBD_SYS_INFO_1", "World wide harmonized on-board diagnostics (WWH-OBD) system information 1", b"0190", 3, raw_string, ECU.ENGINE, True),
    OBDCommand("WWHOBD_SYS_INFO_2", "World wide harmonized on-board diagnostics (WWH-OBD) system information 1", b"0191", 5, raw_string, ECU.ENGINE, True),
    OBDCommand("FUEL_SYS_CONTROL", "Fuel system control", b"0192", 2, raw_string, ECU.ENGINE, True),
    OBDCommand("WWHOBD_COUNTER_SUPPORT", "World wide harmonized on-board diagnostics (WWH-OBD) counter support", b"0193", 3, raw_string, ECU.ENGINE, True),
    OBDCommand("NOX_WARNING_SYSTEM", "NOx warning and inducement system", b"0194", 12, raw_string, ECU.ENGINE, True),
    OBDCommand("EGT_SENSOR_1", "Exhaust gas temperature (EGT) sensor 1", b"0198", 9, raw_string, ECU.ENGINE, True),
    OBDCommand("EGT_SENSOR_2", "Exhaust gas temperature (EGT) sensor 2", b"0199", 9, raw_string, ECU.ENGINE, True),
    OBDCommand("HYBRID_EV_SYS_DATA", "Hybrid/EV vehicle system data, battery, voltage", b"019A", 6, raw_string, ECU.ENGINE, True),
    OBDCommand("DEF_SENSOR", "Diesel exhaust fluid (DEF) sensor data", b"019B", 4, raw_string, ECU.ENGINE, True),
    OBDCommand("O2_SENSOR_DATA", "O2 sensor data", b"019C", 17, raw_string, ECU.ENGINE, True),
    OBDCommand("ENGINE_FUEL_RATE", "Engine fuel rate", b"019D", 4, raw_string, ECU.ENGINE, True),
    OBDCommand("ENGINE_EXHAUST_FLOW_RATE", "Engine exhaust flow rate", b"019E", 2, raw_string, ECU.ENGINE, True),
    OBDCommand("FUEL_SYS_PCT_USE", "Fuel system percentage use", b"019F", 9, raw_string, ECU.ENGINE, True),

    OBDCommand("PID_F", "PIDs supported [A1 - C0]", b"01A0", 6, pid, ECU.ENGINE, True),
    OBDCommand("NOX_SENSOR_CORRECTED_DATA", "NOx sensor corrected data", b"01A1", 9, raw_string, ECU.ENGINE, True),
    OBDCommand("CYLENDER_FUEL_RATE", "Cylender fuel rate", b"01A2", 2, raw_string, ECU.ENGINE, True),
    OBDCommand("EVAP_SYS_VAPOR_PRESSURE", "Evaporative system vapor pressure", b"01A3", 9, raw_string, ECU.ENGINE, True),
    OBDCommand("TRANNY_GEAR", "Transmission actual gear", b"01A4", 4, raw_string, ECU.ENGINE, True),
    OBDCommand("DEF_DOSING", "Diesel exhaust fluid (DEF) dosing", b"01A5", 4, raw_string, ECU.ENGINE, True),
    OBDCommand("ODOMETER", "Odometer", b"01A6", 4, raw_string, ECU.ENGINE, True),
    OBDCommand("UNKNOWN_01A7", "Unknown description 01A7", b"01A7", 0, raw_string, ECU.ALL, True),
    OBDCommand("UNKNOWN_01A8", "Unknown description 01A8", b"01A8", 0, raw_string, ECU.ALL, True),
    OBDCommand("UNKNOWN_01A9", "Unknown description 01A9", b"01A9", 0, raw_string, ECU.ALL, True),
    OBDCommand("UNKNOWN_01AA", "Unknown description 01AA", b"01AA", 0, raw_string, ECU.ALL, True),
    OBDCommand("UNKNOWN_01AB", "Unknown description 01AB", b"01AB", 0, raw_string, ECU.ALL, True),
    OBDCommand("UNKNOWN_01AC", "Unknown description 01AC", b"01AC", 0, raw_string, ECU.ALL, True),
    OBDCommand("UNKNOWN_01AD", "Unknown description 01AD", b"01AD", 0, raw_string, ECU.ALL, True),
    OBDCommand("UNKNOWN_01AE", "Unknown description 01AE", b"01AE", 0, raw_string, ECU.ALL, True),
    OBDCommand("UNKNOWN_01AF", "Unknown description 01AF", b"01AF", 0, raw_string, ECU.ALL, True),
    OBDCommand("UNKNOWN_01B0", "Unknown description 01B0", b"01B0", 0, raw_string, ECU.ALL, True),
    OBDCommand("UNKNOWN_01B1", "Unknown description 01B1", b"01B1", 0, raw_string, ECU.ALL, True),
    OBDCommand("UNKNOWN_01B2", "Unknown description 01B2", b"01B2", 0, raw_string, ECU.ALL, True),
    OBDCommand("UNKNOWN_01B3", "Unknown description 01B3", b"01B3", 0, raw_string, ECU.ALL, True),
    OBDCommand("UNKNOWN_01B4", "Unknown description 01B4", b"01B4", 0, raw_string, ECU.ALL, True),
    OBDCommand("UNKNOWN_01B5", "Unknown description 01B5", b"01B5", 0, raw_string, ECU.ALL, True),
    OBDCommand("UNKNOWN_01B6", "Unknown description 01B6", b"01B6", 0, raw_string, ECU.ALL, True),
    OBDCommand("UNKNOWN_01B7", "Unknown description 01B7", b"01B7", 0, raw_string, ECU.ALL, True),
    OBDCommand("UNKNOWN_01B8", "Unknown description 01B8", b"01B8", 0, raw_string, ECU.ALL, True),
    OBDCommand("UNKNOWN_01B9", "Unknown description 01B9", b"01B9", 0, raw_string, ECU.ALL, True),
    OBDCommand("UNKNOWN_01BA", "Unknown description 01BA", b"01BA", 0, raw_string, ECU.ALL, True),
    OBDCommand("UNKNOWN_01BB", "Unknown description 01BB", b"01BB", 0, raw_string, ECU.ALL, True),
    OBDCommand("UNKNOWN_01BC", "Unknown description 01BC", b"01BC", 0, raw_string, ECU.ALL, True),
    OBDCommand("UNKNOWN_01BD", "Unknown description 01BD", b"01BD", 0, raw_string, ECU.ALL, True),
    OBDCommand("UNKNOWN_01BE", "Unknown description 01BE", b"01BE", 0, raw_string, ECU.ALL, True),
    OBDCommand("UNKNOWN_01BF", "Unknown description 01BF", b"01BF", 0, raw_string, ECU.ALL, True),


    OBDCommand("PID_G", "PIDs supported [C1 - E0]", b"01C0", 6, pid, ECU.ENGINE, True),
    OBDCommand("UNKNOWN_01C1", "Unknown description 01C1", b"01C1", 0, raw_string, ECU.ALL, True),
    OBDCommand("UNKNOWN_01C2", "Unknown description 01C2", b"01C2", 0, raw_string, ECU.ALL, True),
    OBDCommand("UNKNOWN_01C3", "Unknown description 01C3", b"01C3", 0, raw_string, ECU.ALL, True),
    OBDCommand("UNKNOWN_01C4", "Unknown description 01C4", b"01C4", 0, raw_string, ECU.ALL, True),
    OBDCommand("UNKNOWN_01C5", "Unknown description 01C5", b"01C5", 0, raw_string, ECU.ALL, True),
    OBDCommand("UNKNOWN_01C6", "Unknown description 01C6", b"01C6", 0, raw_string, ECU.ALL, True),
    OBDCommand("UNKNOWN_01C7", "Unknown description 01C7", b"01C7", 0, raw_string, ECU.ALL, True),
    OBDCommand("UNKNOWN_01C8", "Unknown description 01C8", b"01C8", 0, raw_string, ECU.ALL, True),
    OBDCommand("UNKNOWN_01C9", "Unknown description 01C9", b"01C9", 0, raw_string, ECU.ALL, True),
    OBDCommand("UNKNOWN_01CA", "Unknown description 01CA", b"01CA", 0, raw_string, ECU.ALL, True),
    OBDCommand("UNKNOWN_01CB", "Unknown description 01CB", b"01CB", 0, raw_string, ECU.ALL, True),
    OBDCommand("UNKNOWN_01CC", "Unknown description 01CC", b"01CC", 0, raw_string, ECU.ALL, True),
    OBDCommand("UNKNOWN_01CD", "Unknown description 01CD", b"01CD", 0, raw_string, ECU.ALL, True),
    OBDCommand("UNKNOWN_01CE", "Unknown description 01CE", b"01CE", 0, raw_string, ECU.ALL, True),
    OBDCommand("UNKNOWN_01CF", "Unknown description 01CF", b"01CF", 0, raw_string, ECU.ALL, True),
    OBDCommand("UNKNOWN_01D0", "Unknown description 01D0", b"01D0", 0, raw_string, ECU.ALL, True),
    OBDCommand("UNKNOWN_01D1", "Unknown description 01D1", b"01D1", 0, raw_string, ECU.ALL, True),
    OBDCommand("UNKNOWN_01D2", "Unknown description 01D2", b"01D2", 0, raw_string, ECU.ALL, True),
    OBDCommand("UNKNOWN_01D3", "Unknown description 01D3", b"01D3", 0, raw_string, ECU.ALL, True),
    OBDCommand("UNKNOWN_01D4", "Unknown description 01D4", b"01D4", 0, raw_string, ECU.ALL, True),
    OBDCommand("UNKNOWN_01D5", "Unknown description 01D5", b"01D5", 0, raw_string, ECU.ALL, True),
    OBDCommand("UNKNOWN_01D6", "Unknown description 01D6", b"01D6", 0, raw_string, ECU.ALL, True),
    OBDCommand("UNKNOWN_01D7", "Unknown description 01D7", b"01D7", 0, raw_string, ECU.ALL, True),
    OBDCommand("UNKNOWN_01D8", "Unknown description 01D8", b"01D8", 0, raw_string, ECU.ALL, True),
    OBDCommand("UNKNOWN_01D9", "Unknown description 01D9", b"01D9", 0, raw_string, ECU.ALL, True),
    OBDCommand("UNKNOWN_01DA", "Unknown description 01DA", b"01DA", 0, raw_string, ECU.ALL, True),
    OBDCommand("UNKNOWN_01DB", "Unknown description 01DB", b"01DB", 0, raw_string, ECU.ALL, True),
    OBDCommand("UNKNOWN_01DC", "Unknown description 01DC", b"01DC", 0, raw_string, ECU.ALL, True),
    OBDCommand("UNKNOWN_01DD", "Unknown description 01DD", b"01DD", 0, raw_string, ECU.ALL, True),
    OBDCommand("UNKNOWN_01DE", "Unknown description 01DE", b"01DE", 0, raw_string, ECU.ALL, True),
    OBDCommand("UNKNOWN_01DF", "Unknown description 01DF", b"01DF", 0, raw_string, ECU.ALL, True),

]