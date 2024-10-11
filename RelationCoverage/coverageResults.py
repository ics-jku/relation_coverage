import os

import configuration
import addressTranslation
import coverageStructure
import relationCoverage

HW_RIP_COUNT = [0 for i in range(0x7FFFFF)]
SW_PC_COUNT = [0 for i in range(0x7FFFFF)]

def branchHitCount(fileName, type, line, column):
    lib = None
    offset = 0
    if type=="HW":
        lib = addressTranslation.HW_DWARF_INFO
    elif type == "SW":
        lib = addressTranslation.SW_DWARF_INFO
    for info in lib:
        if info[0] == fileName and info[1] == int(line) and info[2] == (int(column)-offset):
            if type == "HW":
                if addressTranslation.HW_BRANCHES[info[3]] != [-1,-1]:
                    return addressTranslation.HW_BRANCHES[info[3]]
            elif type == "SW":
                if addressTranslation.SW_BRANCHES[info[3]] != [-1,-1]:
                    return addressTranslation.SW_BRANCHES[info[3]]
    return None

def lineToHitCount(fileName, type, line):
    global HW_RIP_COUNT
    global SW_PC_COUNT
    lib = None
    hitCount = -1
    if type=="HW":
        lib = addressTranslation.HW_DWARF_INFO
    elif type == "SW":
        lib = addressTranslation.SW_DWARF_INFO
    for info in lib:
        if info[0] == fileName and info[1] == int(line):
            if type == "HW":
                if hitCount < HW_RIP_COUNT[info[3]]:
                    hitCount = HW_RIP_COUNT[info[3]]
            elif type == "SW":
                if hitCount < SW_PC_COUNT[info[3]]:
                    hitCount = SW_PC_COUNT[info[3]]
    return hitCount

def calculateBranchesRecursive(fileName, type, node, branches_covered, branches_valid):
    branch = node.condition.split(":")
    branchHits = branchHitCount(fileName, type, branch[0], branch[1])
    if branchHits != None and node.condFalse != None and node.condTrue != None:
        branches_valid += 2
        if branchHits[0] > 0:
            branches_covered += 1
        if branchHits[1] > 0:
            branches_covered += 1
    if node.condFalse != None:
        branches_covered, branches_valid = calculateBranchesRecursive(fileName, type, node.condFalse, branches_covered, branches_valid)
    if node.condTrue != None:
        branches_covered, branches_valid = calculateBranchesRecursive(fileName, type, node.condTrue, branches_covered, branches_valid)
    return branches_covered, branches_valid

def calculateLinesRecursive(file, type, content):
    lines_covered = 0
    lines_valid = 0
    branches_covered = 0
    branches_valid = 0
    for inner in content:
        if inner.Type == "Line":
            count = lineToHitCount(file, type, inner.Name)
            if count >= 0:
                if count > 0:
                    lines_covered += 1
                lines_valid += 1 
        elif inner.Type == "Method":
            for branch in inner.Branches:
                branches_covered, branches_valid = calculateBranchesRecursive(file, type, branch, branches_covered, branches_valid)
        
        lines_covered_tmp, lines_valid_tmp, branches_covered_tmp, branches_valid_tmp = calculateLinesRecursive(file, type, inner.Content)
        lines_covered += lines_covered_tmp
        lines_valid += lines_valid_tmp
        branches_covered += branches_covered_tmp
        branches_valid += branches_valid_tmp
    return lines_covered, lines_valid, branches_covered, branches_valid

def lineContainsBranches(content, line):
    contains = False
    if content.condition.split(":")[0] == str(line):
        if content.condTrue != None or content.condFalse != None:
            contains = True
    if content.condTrue != None:
        if lineContainsBranches(content.condTrue, line):
            contains = True
    if content.condFalse != None:
        if lineContainsBranches(content.condFalse, line):
            contains = True
    return contains

def exportBranchesRecursive(cobertura, fileName, type, node, conditionNumber, idents):
    branches_covered = 0
    branches_valid = 0
    branch = node.condition.split(":")
    branchHits = branchHitCount(fileName, type, branch[0], branch[1])

    if branchHits != None and node.condFalse != None and node.condTrue != None:
        conditionNumber += 1
        branches_valid += 2
        if branchHits[0] > 0:
            branches_covered += 1
        if branchHits[1] > 0:
            branches_covered += 1
        cobertura.write(idents + '\t\t\t<condition number="' + str(conditionNumber) + '" type="jump" coverage="' + str(branches_covered/branches_valid*100) + '%"/>\n')
    if node.condFalse != None:
        conditionNumber = exportBranchesRecursive(cobertura, fileName, type, node.condFalse, conditionNumber, idents)
    if node.condTrue != None:
        conditionNumber = exportBranchesRecursive(cobertura, fileName, type, node.condTrue, conditionNumber, idents)
    return conditionNumber


def exportMethodLines(cobertura, fileName, type, contents, branches, idents):
    for content in contents:
        if content.Type == "Line":
            hitcount = lineToHitCount(fileName, type, content.Name)
            if hitcount != -1:
                containsBranch = False
                branches_covered = 0
                branches_valid = 0
                for branch in branches:
                    if lineContainsBranches(branch, content.Name):
                        branches_covered, branches_valid = calculateBranchesRecursive(fileName, type, branch, branches_covered, branches_valid)
                        containsBranch = True
                if containsBranch:
                    cobertura.write(idents + '\t<line number="' + str(content.Name) + '" hits="' + str(hitcount) + '" branch="true" ')
                    condition_coverage = 0
                    if branches_valid != 0:
                        condition_coverage = branches_covered/branches_valid*100
                    cobertura.write('condition-coverage="' + str(condition_coverage) + '% (' + str(branches_covered) + '/' + str(branches_valid) + ')"')
                    cobertura.write('>\n')
                    cobertura.write(idents + '\t\t<conditions>\n')
                    conditions = -1
                    for branch in branches:
                        if lineContainsBranches(branch, content.Name):
                            conditions = exportBranchesRecursive(cobertura, fileName, type, branch, conditions, idents)
                    cobertura.write(idents + '\t\t</conditions>\n')
                    cobertura.write(idents + '\t</line>\n')
                else:
                    cobertura.write(idents + '\t<line number="' + str(content.Name) + '" hits="' + str(hitcount) + '" branch="false"/>\n')
    

def exportMethods(cobertura, fileName, type, contents):
    for content in contents:
        if content.Type == "Method":
            line_rate = 0.0
            branch_rate = 0.0
            lines_covered, lines_valid, branches_covered, branches_valid = calculateLinesRecursive(fileName, type, content.Content)
            if lines_valid > 0:
                line_rate = lines_covered/lines_valid
            if branches_valid > 0:
                branch_rate = branches_covered/branches_valid
            methodName = content.Name.replace("&", "&amp;")
            cobertura.write('\t\t\t\t\t\t<method name="' + methodName + '" signature="(...)" line-rate="' + str(line_rate) + '" branch-rate="' + str(branch_rate) + '">\n')
            cobertura.write('\t\t\t\t\t\t\t<lines>\n')
            exportMethodLines(cobertura, fileName, type, content.Content, content.Branches, '\t\t\t\t\t\t\t')
            cobertura.write('\t\t\t\t\t\t\t</lines>\n')
            cobertura.write('\t\t\t\t\t\t</method>\n')
        if content.Type == "class" or content.Type == "namespace" or content.Type == "struct":
            exportMethods(cobertura, fileName, type, content.Content)
    
def exportClassLines(cobertura, fileName, type, contents):
    for content in contents:
        if content.Type == "Method":
            exportMethodLines(cobertura, fileName, type, content.Content, content.Branches, '\t\t\t\t\t')
        if content.Type == "class" or content.Type == "namespace" or content.Type == "struct":
            exportClassLines(cobertura, fileName, type, content.Content)

def exportClasses(cobertura, type, files):
    cobertura.write('\t\t\t<classes>\n')
    for file in files:
        line_rate = 0.0
        branch_rate = 0.0
        lines_covered, lines_valid, branches_covered, branches_valid = calculateLinesRecursive(file.Name, type, file.Content)
        if lines_valid > 0:
            line_rate = lines_covered/lines_valid
        if branches_valid > 0:
            branch_rate = branches_covered/branches_valid
        className = os.path.basename(file.Name).replace(".h", "").replace(".cpp", "").replace(".hpp", "").replace(".c", "")
        cobertura.write('\t\t\t\t<class name="' + className + '" filename="' + file.Name + '" line-rate="' + str(line_rate) + '" branch-rate="' + str(branch_rate) + '" complexity="0.0">\n')
        cobertura.write('\t\t\t\t\t<methods>\n')
        exportMethods(cobertura, file.Name, type, file.Content)
        cobertura.write('\t\t\t\t\t</methods>\n')
        cobertura.write('\t\t\t\t\t<lines>\n')
        exportClassLines(cobertura, file.Name, type, file.Content)
        cobertura.write('\t\t\t\t\t</lines>\n')
        cobertura.write('\t\t\t\t</class>\n')
    cobertura.write('\t\t\t</classes>\n')

def exportPackages(cobertura):

    cobertura.write('\t<packages>\n')

    for hw in coverageStructure.COVERAGE_STRUCTURE.HWLibraries:
        lines_covered = 0
        lines_valid = 0
        branches_covered = 0
        branches_valid = 0
        line_rate = 0.0
        branch_rate = 0.0
        for file in hw.Files:
            lines_covered_tmp, lines_valid_tmp, branches_covered_tmp, branches_valid_tmp = calculateLinesRecursive(file.Name, "HW", file.Content)
            lines_covered += lines_covered_tmp
            lines_valid += lines_valid_tmp
            branches_covered += branches_covered_tmp
            branches_valid += branches_valid_tmp
        if lines_valid > 0:
            line_rate = lines_covered/lines_valid
        if branches_valid > 0:
            branch_rate = branches_covered/branches_valid
        cobertura.write('\t\t<package name="HW:' + hw.Name + '" line-rate="' + str(line_rate) + '" branch-rate="' + str(branch_rate) + '" complexity="0.0">\n')
        exportClasses(cobertura, "HW", hw.Files)                
        cobertura.write('\t\t</package>\n')
    for sw in coverageStructure.COVERAGE_STRUCTURE.SWLibraries:
        lines_covered = 0
        lines_valid = 0
        branches_covered = 0
        branches_valid = 0
        line_rate = 0.0
        branch_rate = 0.0
        for file in sw.Files:
            lines_covered_tmp, lines_valid_tmp, branches_covered_tmp, branches_valid_tmp = calculateLinesRecursive(file.Name, "SW", file.Content)
            lines_covered += lines_covered_tmp
            lines_valid += lines_valid_tmp
            branches_covered += branches_covered_tmp
            branches_valid += branches_valid_tmp
        if lines_valid > 0:
            line_rate = lines_covered/lines_valid
        if branches_valid > 0:
            branch_rate = branches_covered/branches_valid
        cobertura.write('\t\t<package name="SW:' + sw.Name + '" line-rate="' + str(line_rate) + '" branch-rate="' + str(branch_rate) + '" complexity="0.0">\n')
        exportClasses(cobertura, "SW", sw.Files)                
        cobertura.write('\t\t</package>\n')
    cobertura.write('\t</packages>\n')

def generateCoverage(cobertura):
    lines_covered = 0
    lines_valid = 0
    branches_covered = 0
    branches_valid = 0
    line_rate = 0.0
    branch_rate = 0.0
    complexity = 0

    for hw in coverageStructure.COVERAGE_STRUCTURE.HWLibraries:
        for file in hw.Files:
            lines_covered_tmp, lines_valid_tmp, branches_covered_tmp, branches_valid_tmp = calculateLinesRecursive(file.Name, "HW", file.Content)
            lines_covered += lines_covered_tmp
            lines_valid += lines_valid_tmp
            branches_covered += branches_covered_tmp
            branches_valid += branches_valid_tmp

    for sw in coverageStructure.COVERAGE_STRUCTURE.SWLibraries:
        for file in sw.Files:
            lines_covered_tmp, lines_valid_tmp, branches_covered_tmp, branches_valid_tmp = calculateLinesRecursive(file.Name, "SW", file.Content)
            lines_covered += lines_covered_tmp
            lines_valid += lines_valid_tmp
            branches_covered += branches_covered_tmp
            branches_valid += branches_valid_tmp
    if lines_valid > 0:
        line_rate = lines_covered/lines_valid
    if branches_valid > 0:
        branch_rate = branches_covered/branches_valid
    cobertura.write('<coverage line-rate="' + str(line_rate) + '" branch-rate="' + str(branch_rate) + '" lines-covered="' + str(lines_covered) + '" lines-valid="' + str(lines_valid) + '" branches-covered="' + str(branches_covered) + '" branches-valid="' + str(branches_valid) + '" complexity="0.0" version="1.0.0" timestamp="' + str(os.path.getmtime(configuration.CFG_COVERAGE_RESULT)) + '">\n')
    
    exportSources(cobertura)
    exportPackages(cobertura)    
    cobertura.write('</coverage>\n')    

def exportSources(cobertura):
    cobertura.write('\t<sources>\n')
    for hw in coverageStructure.COVERAGE_STRUCTURE.HWLibraries:
        for file in hw.Files:
            cobertura.write('\t\t<source>' + file.Name + '</source>\n')
    for sw in coverageStructure.COVERAGE_STRUCTURE.SWLibraries:
        for file in sw.Files:
            cobertura.write('\t\t<source>' + file.Name + '</source>\n')

    cobertura.write('\t</sources>\n')

def exportCoverageXML():
    with open(configuration.CFG_COVERAGE_RESULT.replace(".trc", ".xml"), "w") as cobertura:
        cobertura.write('<?xml version="1.0"?>\n')
        cobertura.write('<!DOCTYPE coverage SYSTEM "http://cobertura.sourceforge.net/xml/coverage-04.dtd">\n')
        cobertura.write('\n')
        generateCoverage(cobertura)

def updateRelationCounter(address, count):
    for i, relation in enumerate(relationCoverage.RELATIONS):
        lhs = relation.Lhs.split(":")
        if lhs[2] == str(address):
            relationCoverage.RELATIONS[i].Lhs = lhs[0] + ":" + lhs[1] + ":" + lhs[2] + ":" + str(count)
        if relation.Type != "ACC":
            rhs = relation.Rhs.split(":")
            if rhs[2] == str(address):
                relationCoverage.RELATIONS[i].Rhs = rhs[0] + ":" + rhs[1] + ":" + rhs[2] + ":"  + str(count)
        else:
            for j, rhs in enumerate(relation.Rhs):
                item = rhs.split(":")
                if item[2] == str(address):
                    relationCoverage.RELATIONS[i].Rhs[j] = item[0] + ":" + item[1] + ":" + lhs[2] + ":"  + str(count)

def readCoverageResults():
    global HW_RIP_COUNT
    global SW_PC_COUNT
    #global MOD_PC_COUNT
    with open(configuration.CFG_COVERAGE_RESULT, "rb") as buf:
        for i in range(0x2FFFFF):
            count = int.from_bytes(buf.read(8), "little")
            HW_RIP_COUNT[i] += count
            if (count != 0):
                updateRelationCounter(i, count)
        for i in range(0x2FFFFF):
            count = int.from_bytes(buf.read(8), "little")
            SW_PC_COUNT[i] += count
            if(count != 0):
                updateRelationCounter(i, count)
        for i in range(0x2FFFFF):
            true = int.from_bytes(buf.read(8), "little")
            false = int.from_bytes(buf.read(8), "little")
            if true != 0 or false != 0:
                addressTranslation.HW_BRANCHES[i] = [true, false]
        for i in range(0x2FFFFF):
            true = int.from_bytes(buf.read(8), "little")
            false = int.from_bytes(buf.read(8), "little")
            if true != 0 or false != 0:
                addressTranslation.SW_BRANCHES[i] = [true, false]

def processCoverageResults():
    readCoverageResults()
    exportCoverageXML()