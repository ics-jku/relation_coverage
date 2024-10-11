import configuration

class Relation:
    def __init__(self, Type, Name, Lhs, Rhs):
        self.Type = Type
        self.Name = Name
        self.Lhs = Lhs
        self.Rhs = Rhs

RELATIONS=[]

def generateReport():
    EQU = 0
    EQU_C = 0
    GE = 0
    GE_C = 0
    ACC = 0
    ACC_C = 0

    with open(configuration.CFG_COVERAGE_RESULT.replace(".trc", ".cover"), "w") as relation_report:
        for relation in RELATIONS:
            if relation.Type == "EQU":
                EQU += 1
                lhscount = int(relation.Lhs.split(":")[3])
                rhscount = int(relation.Rhs.split(":")[3])
                relation_report.write(relation.Type + ":" + relation.Name + ":")
                if lhscount != 0 and rhscount != 0 and lhscount == rhscount:
                    relation_report.write("Covered")
                    EQU_C += 1
                else:
                    relation_report.write("NotCovered")
                relation_report.write("\n")
            if relation.Type == "GE":
                GE += 1
                lhscount = int(relation.Lhs.split(":")[3])
                rhscount = int(relation.Rhs.split(":")[3])
                relation_report.write(relation.Type + ":" + relation.Name + ":")
                if lhscount != 0 and rhscount != 0 and lhscount >= rhscount:
                    relation_report.write("Covered")
                    GE_C += 1
                else:
                    relation_report.write("NotCovered")
                relation_report.write("\n")
            if relation.Type == "ACC":
                ACC += 1
                lhscount = int(relation.Lhs.split(":")[3])
                rhscount = 0
                covered = True
                for rhs in relation.Rhs:
                    rhssinglecount = int(rhs.split(":")[3])
                    if rhssinglecount > 0:
                        rhscount += rhssinglecount
                    else: 
                        covered = False
                relation_report.write(relation.Type + ":" + relation.Name + ":")
                if covered and lhscount != 0 and rhscount != 0 and lhscount == rhscount:
                    relation_report.write("Covered")
                    ACC_C += 1
                else:
                    relation_report.write("NotCovered")
                relation_report.write("\n")
        relation_report.write("\n")
        ALL = EQU + GE + ACC
        ALL_C = EQU_C + GE_C + ACC_C
        relation_report.write("-------------------------------------------------------------\n")
        relation_report.write("| TYPE         | #            | Covered      | Coverage     |\n")     
        relation_report.write("-------------------------------------------------------------\n")    
        if EQU > 0:   
            relation_report.write("| EQU Coverage | " + str(EQU)  + "            | " + str(EQU_C) + "            | " + str(round(EQU_C/EQU * 100, 0)) + "         |\n")
        if GE > 0:
            relation_report.write("| GE  Coverage | " + str(GE)   + "            | " + str(GE_C)  + "            | " + str(round(GE_C/GE * 100, 0)) + "         |\n")
        if ACC > 0:
            relation_report.write("| ACC Coverage | " + str(ACC)  + "            | " + str(ACC_C) + "            | " + str(round(ACC_C/ACC * 100, 0)) + "         |\n")
        if ALL > 0:
            relation_report.write("-------------------------------------------------------------\n")
            relation_report.write("| REL Coverage | " + str(ALL)  + "            | " + str(ALL_C) + "            | " + str(round(ALL_C/ALL * 100, 0)) + "         |\n")
            relation_report.write("-------------------------------------------------------------\n")
def parseRelationsFile(relations_file):
    global RELATIONS
    hw = ""
    sw = ""
    with open(relations_file, "r") as read_relations:
        for line in read_relations:
            line = line.rstrip()
            if line.startswith("HW:"):
                hw = line.split(":")[1]
            elif line.startswith("SW:"):
                sw = line.split(":")[1]
            else:
                tokens = line.split(":")
                if tokens[0] == "EQU":
                    lhs = ""
                    rhs = ""
                    if tokens[2] == "HW":
                        lhs = hw
                    else:
                        lhs = sw
                    lhs = lhs + ":" + tokens[3]
                    if tokens[4] == "HW":
                        rhs = hw
                    else:
                        rhs = sw
                    rhs = rhs + ":" + tokens[5]
                    RELATIONS.append(Relation(tokens[0], tokens[1], lhs, rhs))
                elif tokens[0] == "GE":
                    lhs = ""
                    rhs = ""
                    if tokens[2] == "HW":
                        lhs = hw
                    else:
                        lhs = sw
                    lhs = lhs + ":" + tokens[3]
                    if tokens[4] == "HW":
                        rhs = hw
                    else:
                        rhs = sw
                    rhs = rhs + ":" + tokens[5]
                    RELATIONS.append(Relation(tokens[0], tokens[1], lhs, rhs))
                elif tokens[0] == "ACC":
                    lhs = ""
                    rhs = []
                    if tokens[2] == "HW":
                        lhs = hw
                    else:
                        lhs = sw
                    lhs = lhs + ":" + tokens[3]
                    index = 4
                    while(index < len(tokens)):
                        item = "" 
                        if tokens[index] == "HW":
                            item = hw
                        else:
                            item = sw
                        rhs.append(item + ":" + tokens[index+1])
                        index += 2
                    RELATIONS.append(Relation(tokens[0], tokens[1], lhs, rhs))
            