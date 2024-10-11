import sys

from elftools.dwarf.descriptions import describe_form_class
from elftools.elf.elffile import ELFFile
from elftools.dwarf.locationlists import (LocationEntry, LocationExpr, LocationParser)

from pathlib import Path

import configuration
import coverageStructure
import relationCoverage

HW_DWARF_INFO = []
SW_DWARF_INFO = []

PC_LINE_ADDRESS = 0
RECORDING_ADDRESS = 0

HW_BRANCHES = [[-1,-1] for i in range(0x7FFFFF)]
SW_BRANCHES = [[-1,-1] for i in range(0x7FFFFF)]

def exportHWBranchRecursive(address_file, fileName, branch):
    global HW_BRANCHES
    true = "??"
    false = "??"
    
    if branch.condTrue != None:
        true = branch.condTrue.condition
        exportHWBranchRecursive(address_file, fileName, branch.condTrue)
    if branch.condFalse != None:
        false = branch.condFalse.condition
        exportHWBranchRecursive(address_file, fileName, branch.condFalse)
    if branch.condTrue != None and branch.condFalse != None:
        loc = branch.condition.split(":")
        loc_true = true.split(":")
        loc_false = false.split(":")
        address = 0
        true_addr = 0
        false_addr = 0
        for hw_info in HW_DWARF_INFO:
            if hw_info[0] == fileName and hw_info[1] == int(loc[0]) and hw_info[2] == int(loc[1]):
                address = hw_info[3]
            if hw_info[0] == fileName and hw_info[1] == int(loc_true[0]) and hw_info[2] == int(loc_true[1]):
                true_addr = hw_info[3]
            if hw_info[0] == fileName and hw_info[1] == int(loc_false[0]) and hw_info[2] == int(loc_false[1]):
                false_addr = hw_info[3]
        
        if address != 0 and false_addr == 0:
            false_loc = int(loc_false[0])
            numLines = sum(1 for _ in open(fileName))

            while(false_addr == 0 and false_loc < numLines):
                false_loc += + 1
                for hw_info in HW_DWARF_INFO:
                    if hw_info[0] == fileName and hw_info[1] == false_loc:
                        false_addr = hw_info[3]
                        break
            while false_addr == 0:
                for hw_info in HW_DWARF_INFO:
                    if hw_info[0] == fileName and hw_info[1] < int(loc[1]) and hw_info[3] > address: # some kind of endlessloop
                        false_addr = hw_info[3]
                

        if address != 0 and true_addr == 0:
            for hw_info in HW_DWARF_INFO:
                if hw_info[0] == fileName and hw_info[1] == int(loc_true[0]):
                    true_addr = hw_info[3]
            if true_addr == 0:
                true_addr = address
        if address == 0 or true_addr == 0 or false_addr == 0:
            print("HW: Possible Dead Code or unsupported statement detected for " + fileName + ":" + branch.condition)
        else:
            HW_BRANCHES[address] = [0,0]
            address_file.write("1:" + str(address) + ":" + str(true_addr) + ":" + str(false_addr) + "\n")

def exportSWBranchRecursive(address_file, fileName, branch):
    global SW_BRANCHES
    true = "??"
    false = "??"
    if branch.condTrue != None:
        true = branch.condTrue.condition
        exportSWBranchRecursive(address_file, fileName, branch.condTrue)
    if branch.condFalse != None:
        false = branch.condFalse.condition
        exportSWBranchRecursive(address_file, fileName, branch.condFalse)
    if branch.condTrue != None and branch.condFalse != None:
        loc = branch.condition.split(":")
        loc_true = true.split(":")
        loc_false = false.split(":")
        address = 0
        true_addr = 0
        false_addr = 0
        for sw_info in SW_DWARF_INFO:
            if sw_info[0] == fileName and sw_info[1] == int(loc[0]) and sw_info[2] == int(loc[1]):
                address = sw_info[3]
            if sw_info[0] == fileName and sw_info[1] == int(loc_true[0]):
                true_addr = sw_info[3]
            if sw_info[0] == fileName and sw_info[1] == int(loc_false[0]):
                false_addr = sw_info[3]
        if address != 0 and false_addr == 0:
            false_loc = int(loc_false[0])
            numLines = sum(1 for _ in open(fileName))

            while(false_addr == 0 and false_loc < numLines):
                false_loc += + 1
                for sw_info in SW_DWARF_INFO:
                    if sw_info[0] == fileName and sw_info[1] == false_loc:
                        false_addr = sw_info[3]
                        break
            while false_addr == 0:
                for sw_info in SW_DWARF_INFO:
                    if sw_info[0] == fileName and sw_info[1] < int(loc[1]) and sw_info[3] > address: # some kind of endlessloop
                        false_addr = sw_info[3]
                

        if address != 0 and true_addr == 0:
            for sw_info in SW_DWARF_INFO:
                if sw_info[0] == fileName and sw_info[1] == int(loc_true[0]):
                    true_addr = sw_info[3]
            if true_addr == 0:
                true_addr = address
        if address == 0 or true_addr == 0 or false_addr == 0:
            print("SW: Possible Dead Code or unsupported statement detected for " + fileName + ":" + branch.condition)
        else:
            SW_BRANCHES[address] = [0,0]
            address_file.write("3:" + str(address) + ":" + str(true_addr) + ":" + str(false_addr) + "\n")


def updateRelations(position,address):
    for relation in relationCoverage.RELATIONS:
        if relation.Lhs == position:
            relation.Lhs = relation.Lhs + ":" + address + ":0"
        if relation.Type != "ACC":
            if relation.Rhs == position:
                relation.Rhs = relation.Rhs + ":" + address + ":0"
        else:
            for i, rhs in enumerate(relation.Rhs):
                if rhs == position:
                   relation.Rhs[i] = relation.Rhs[i] + ":" + address + ":0"

def fillPCMap(dwarfinfo, type):
    global SW_DWARF_INFO
    global HW_DWARF_INFO
    global PC_LINE_ADDRESS
    global RECORDING_ADDRESS

    binary_path = ""
    if type == "SW":
        binary_path = configuration.CFG_SOFTWARE
    elif type == "HW":
        binary_path = configuration.CFG_HARDWARE

    for CU in dwarfinfo.iter_CUs():
        lineprog = dwarfinfo.line_program_for_CU(CU)
        delta = 1 if lineprog.header.version < 5 else 0
        prevstate = None
        for entry in lineprog.get_entries():
            if entry.state is None:
                continue
            if prevstate:
                address = prevstate.address
                path = str(lineprog["include_directory"][lineprog['file_entry'][prevstate.file - delta]["dir_index"]].decode("utf-8"))
                if path.startswith("../../"):
                    path = path.replace("../../", str(Path(binary_path).resolve().parent.parent.parent.absolute()))
                elif path.startswith("../"):
                    path = path.replace("../", str(Path(binary_path).resolve().parent.parent.absolute()) + "/")
                filename = str(lineprog['file_entry'][prevstate.file - delta].name.decode('utf-8'))
                line = prevstate.line
                column = prevstate.column
                if type == "SW":
                    append = True
                    if len(configuration.CFG_SOFTWARE_COVERAGE_WHITELIST) > 0:
                        append = False
                        for whitelist_file in configuration.CFG_SOFTWARE_COVERAGE_WHITELIST:
                            if str(Path(path + "/" + filename).absolute().resolve()) == whitelist_file:
                                append = True
                    if append:
                        SW_DWARF_INFO.append([str(Path(path + "/" + filename).absolute().resolve()), line, column-1, address])
                        updateRelations(str(Path(path + "/" + filename).absolute().resolve()) + ":" + str(line), str(address))
                elif type == "HW":
                    pc_line_info = coverageStructure.PC_LINE.split(":")
                    if str(Path(path + "/" + filename).absolute().resolve()) == pc_line_info[0] and line == int(pc_line_info[1]):
                        if address > PC_LINE_ADDRESS:
                            PC_LINE_ADDRESS = address
                    if configuration.CFG_RECORDING_TRIGGER and str(Path(path + "/" + filename).absolute().resolve()) == configuration.CFG_RECORDING_TRIGGER[0] and line == int(configuration.CFG_RECORDING_TRIGGER[1]):
                        if RECORDING_ADDRESS == 0:
                            RECORDING_ADDRESS = address
                    if len(configuration.CFG_HARDWARE_COVERAGE_WHITELIST) > 0:
                        for whitelist_file in configuration.CFG_HARDWARE_COVERAGE_WHITELIST:
                            if str(Path(path + "/" + filename).absolute().resolve()) == whitelist_file:
                                HW_DWARF_INFO.append([str(Path(path + "/" + filename).absolute().resolve()), line, column-1, address])
                                updateRelations(str(Path(path + "/" + filename).absolute().resolve()) + ":" + str(line), str(address))
                    else:
                        HW_DWARF_INFO.append([str(Path(path + "/" + filename).absolute().resolve()), line, column-1, address])
                        updateRelations(str(Path(path + "/" + filename).absolute().resolve()) + ":" + str(line), str(address))
            if entry.state.end_sequence:
                prevstate = None
            else:
                prevstate = entry.state

def exportHWStatement(address_file, fileName, content):
    for inner in content:
        if inner.Type == "Line":
            for hw_info in HW_DWARF_INFO:
                if hw_info[0] == fileName and hw_info[1] == int(inner.Name):
                    address_file.write("0:" + str(hw_info[3]) + "\n")
        elif inner.Type == "Method":
            for branch in inner.Branches:
                exportHWBranchRecursive(address_file, fileName, branch)
        exportHWStatement(address_file, fileName, inner.Content)

def exportSWStatement(address_file, fileName, content):
    for inner in content:
        if inner.Type == "Line":
            for sw_info in SW_DWARF_INFO:
                if sw_info[0] == fileName and sw_info[1] == int(inner.Name):
                    address_file.write("2:" + str(sw_info[3]) + "\n")
        elif inner.Type == "Method":
            for branch in inner.Branches:
                exportSWBranchRecursive(address_file, fileName, branch)
        exportSWStatement(address_file, fileName, inner.Content)

def readDWARFInfo(type):

    path = ""
    if type == "SW":
        path = configuration.CFG_SOFTWARE
    elif type == "HW":
        path = configuration.CFG_HARDWARE
    with open(path, "rb") as binary:
        elffile = ELFFile(binary)
        dwarfinfo = None
        if not elffile.has_dwarf_info:
            print("... Error: Binary " + path + " has no DWARF Information")
            sys.exit(0)
        try:
            dwarfinfo = elffile.get_dwarf_info()
        except:
            print("Error in DWARF!")
        if dwarfinfo != None:
            fillPCMap(dwarfinfo, type)

def exportAddressTable():
    global PC_LINE_ADDRESS
    global RECORDING_ADDRESS
    with open(configuration.CFG_ADDRESS_TABLE, "w") as address_file:
        address_file.write("4:" + str(PC_LINE_ADDRESS) + "\n")
        address_file.write("7:" + str(RECORDING_ADDRESS) + "\n")
        for hw in coverageStructure.COVERAGE_STRUCTURE.HWLibraries:
            for file in hw.Files:
                exportHWStatement(address_file, file.Name, file.Content)
        for sw in coverageStructure.COVERAGE_STRUCTURE.SWLibraries:
            for file in sw.Files:
                exportSWStatement(address_file, file.Name, file.Content)


def generateAddressTable():
    readDWARFInfo("HW")
    readDWARFInfo("SW")
    exportAddressTable()