CFG_TYPE = ""
CFG_CHANNEL = ""
CFG_RECORDING_TRIGGER = ""
CFG_HARDWARE = ""
CFG_HARDWARE_PARAMETERS = []
CFG_HARDWARE_BUILD_SYSTEM = ""
CFG_HARDWARE_MAIN_FOLDER = ""
CFG_HARDWARE_MAIN_ENTRY = ""
CFG_HARDWARE_COVERAGE_WHITELIST = []
CFG_SOFTWARE = ""
CFG_SOFTWARE_BUILD_SYSTEM = ""
CFG_SOFTWARE_MAIN_FOLDER = ""
CFG_SOFTWARE_MAIN_ENTRY = ""
CFG_SOFTWARE_COVERAGE_WHITELIST = []
CFG_MODULE = ""
CFG_MODULE_MAIN_FOLDER = ""
CFG_MODULE_MAIN_ENTRY = ""

CFG_ADDRESS_TABLE = ""
CFG_COVERAGE_RESULT = ""
CFG_RELATIONS = ""

CFG_PC = ""

def parseConfig(config_file):

    global CFG_TYPE
    global CFG_CHANNEL
    global CFG_RECORDING_TRIGGER
    global CFG_HARDWARE
    global CFG_HARDWARE_PARAMETERS
    global CFG_HARDWARE_BUILD_SYSTEM
    global CFG_HARDWARE_MAIN_FOLDER
    global CFG_HARDWARE_MAIN_ENTRY
    global CFG_HARDWARE_COVERAGE_WHITELIST
    global CFG_SOFTWARE
    global CFG_SOFTWARE_BUILD_SYSTEM
    global CFG_SOFTWARE_MAIN_FOLDER
    global CFG_SOFTWARE_MAIN_ENTRY
    global CFG_SOFTWARE_COVERAGE_WHITELIST

    global CFG_ADDRESS_TABLE
    global CFG_COVERAGE_RESULT
    global CFG_RELATIONS
    global CFG_PC

    with open(config_file, "r") as config:
        for line in config:
            line = line.rstrip()
            if "TYPE:" in line:
                CFG_TYPE = line.split(":")[1]
            if "CHANNEL:" in line:
                CFG_CHANNEL = line.split(":")[1]
            if "RECORDING_TRIGGER:" in line:
                CFG_RECORDING_TRIGGER = line.split(":")[1:]
            if "HARDWARE:" in line:
                CFG_HARDWARE = line.split(":")[1]
            if "HARDWARE_PARAMETER:" in line:
                CFG_HARDWARE_PARAMETERS.append(line.split(":")[1].replace("\n", ""))
            if "HARDWARE_BUILD_SYSTEM:" in line:
                CFG_HARDWARE_BUILD_SYSTEM = line.split(":")[1]
            if "HARDWARE_MAIN_FOLDER:" in line:
                CFG_HARDWARE_MAIN_FOLDER = line.split(":")[1]
            if "HARDWARE_MAIN_ENTRY:" in line:
                CFG_HARDWARE_MAIN_ENTRY = hardware_main_entry = line.split(":")[1]
            if "HARDWARE_COVERAGE_WHITELIST" in line:
                CFG_HARDWARE_COVERAGE_WHITELIST.append(line.split(":")[1])
            if "SOFTWARE:" in line:
                CFG_SOFTWARE = line.split(":")[1]
            if "SOFTWARE_BUILD_SYSTEM:" in line:
                CFG_SOFTWARE_BUILD_SYSTEM = line.split(":")[1]
            if "SOFTWARE_MAIN_FOLDER:" in line:
                CFG_SOFTWARE_MAIN_FOLDER = line.split(":")[1]
            if "SOFTWARE_MAIN_ENTRY:" in line:
                CFG_SOFTWARE_MAIN_ENTRY = line.split(":")[1]
            if "SOFTWARE_COVERAGE_WHITELIST" in line:
                CFG_SOFTWARE_COVERAGE_WHITELIST.append(line.split(":")[1])
            if "ADDRESS_TABLE:" in line:
                CFG_ADDRESS_TABLE = line.split(":")[1]
            # if "MODULE:" in line:
            #     CFG_MODULE = line.split(":")[1]
            # if "MODULE_MAIN_FOLDER" in line:
            #     CFG_MODULE_MAIN_FOLDER = line.split(":")[1]
            # if "MODULE_MAIN_ENTRY:" in line:
            #     CFG_MODULE_MAIN_ENTRY = line.split(":")[1]
            if "COVERAGE_RESULT:" in line:
                CFG_COVERAGE_RESULT = line.split(":")[1]
            if "RELATIONS:" in line:
                CFG_RELATIONS = line.split(":")[1]
            if "PC:" in line:
                CFG_PC = line.split(":")[1].replace("\n", "")