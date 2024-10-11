import fileStructure
import configuration

class Content:
    def __init__(self, Type, Name, Content, Branches):
        self.Type = Type
        self.Name = Name
        self.Content = Content
        self.Branches = Branches

class File:
    def __init__(self, Name, Content):
        self.Name = Name
        self.Content = Content

class Library:
    def __init__(self, Path, Name, Files):
        self.Path = Path
        self.Name = Name
        self.Files = Files

class Coverage:
    def __init__(self):
        self.HWLibraries = []
        self.SWLibraries = []

class ConditionNode:
    def __init__(self, condition):
        self.condTrue = None
        self.condFalse = None
        self.condition = condition

COVERAGE_STRUCTURE = Coverage()
PC_LINE = ""

def findMethod(tokenized):
    openingPos = -1
    foundLamda = False
    for i, token in enumerate(reversed(tokenized)):
        token = token.replace("\t", " ").replace("\n", " ")
        if token.find(":") != -1 and token.find(":") != token.find("::") or token.find("=") != -1:
            openingPos = -1
        if token.rfind(")") < token.rfind(";"):
            break
        if token.rfind(")>") != -1:
            foundLamda = True
        
        if (token.find(" for") != -1 or token.startswith("for") or
        token.find(" if")  != -1 or token.startswith("if") or
        token.find(" while") != -1 or token.startswith("while") or
        token.find(" try") != -1 or token.startswith("try")):
            openingPos = -1
            break
        if token.rfind("(") != -1 and not foundLamda:
            openingPos = len(tokenized) - i - 1
        if foundLamda and token.rfind("<") != -1:
            foundLamda = False
    if openingPos != -1:
        methodName = tokenized[openingPos].replace("\t", " ").split("(")[0].split(" ")[-1]
        return methodName     
    return ""

def recursiveParse(source):
    i = 0
    k = 0
    content = []
    while(i < len(source)):
        if source[i] == "{":
            l, subcontent = recursiveParse(source[i+1:])
            i = l + i + 1
            tokenized = source[:i].replace("\n", " ").split("{")[0].split(" ")
            for j, token in enumerate(reversed(tokenized)):
                token = token.rstrip().lstrip()
                if(token.find(")") != -1):
                    pos = len(tokenized) - j
                    methodName = findMethod(tokenized[:pos])
                    content.append(Content("Method", methodName, [], []))
                    break
                if token.endswith("class") or token.endswith("namespace") or token.endswith("struct"):
                    content.append(Content(token.replace("\n", " ").replace("\t", " ").split(" ")[-1], tokenized[len(tokenized) - j], subcontent, []))
                    break
                if token.find(";") != -1 or token.find(">") != -1:
                    break
            source = source[i:]
            k += i
            i = 1
        elif source[i] == "}":
            
            return k + i, content
        i += 1
    return i, content

def readFile(file):
    content = []
    with open(file, "r") as content:
        source = content.read()
        commentstart = source.find("//")
        while(commentstart != -1):
            
            commentend = source[commentstart::].find("\n")
            if commentend == -1:
                commentend = len(source)
            else:
                commentend = commentstart + commentend
            source = source.replace(source[commentstart:commentend], "")
            commentstart = source.find("//")
        while(commentstart != -1):
            commentend = source[commentstart::].find("*/")
            if commentend == -1:
                commentend = len(source)
            else:
                commentend = commentstart + commentend
            numberOfLineBreaks = source[commentstart:commentend].count("\n")
            linebreaks = ""
            for i in range(numberOfLineBreaks):
                linebreaks = linebreaks + "\n"
            source = source.replace(source[commentstart:commentend], linebreaks)
            commentstart = source.find("/*")
    end, content = recursiveParse(source)
    return content

def appendFile(libraries, file):
    found = False
    pos = 0
    content = readFile(file[2])
    sourceFile = File(file[2], content)
    for i, library in enumerate(libraries):
        if library.Name == file[1][1]:
            found = True
            pos = i
    if not found:
        libraries.append(Library(file[1][0], file[1][1], [sourceFile]))
    else:
        libraries[pos].Files.append(sourceFile)

def disassembleConditions(code, rootNode, firstLine, firstColumn):
    start = 0
    current = 0
    conditionCount = 0
    currentNode = rootNode
    subNode = ConditionNode("<INVALID>")
    while(current+1<len(code)):
        if(code[current:].strip().startswith("unlikely(")):
            return current
        if(code[current] == "(" and checkIfCondition(code[start:current])):
            column = firstColumn + start
            if code[:current].rfind("\n") != -1:
                column = code[:current].rfind("\n") - 1
            if code[start:current].endswith("!"):
                column += current-start
            current = current + disassembleConditions(code[current+1:current+findConditionEnd(code[current+1:])+1], subNode, firstLine + code[:current].count("\n"), column+1)
        if(code[current] == "&" and code[current+1] == "&"):
            if subNode.condition != "<INVALID>":
                currentNode.condition = subNode.condition
                currentNode.condFalse = subNode.condFalse
                currentNode.condTrue = subNode.condTrue
                fillSubNodes(currentNode.condFalse, currentNode.condTrue, "T")
                subNode.condition = "<INVALID>"

            else:
                column = firstColumn + start + findNextOperator(code[start:])
                if code[:current].rfind("\n") != -1:
                    column = code[:current].rfind("\n") - 1
                currentNode.condition = str(firstLine + code[:start].count("\n")) + ":" + str(column)
                currentNode.condFalse = ConditionNode(0)
                currentNode.condTrue = ConditionNode(1)
            currentNode = currentNode.condTrue
            start = current 
            conditionCount += 1
        if(code[current] == "|" and code[current+1] == "|"):
            if subNode.condition != "<INVALID>":
                currentNode.condition = subNode.condition
                currentNode.condFalse = subNode.condFalse
                currentNode.condTrue = subNode.condTrue
                fillSubNodes(currentNode.condTrue, currentNode.condFalse, "F")
                subNode.condition = "<INVALID>"
            else:
                column = firstColumn + start + findNextOperator(code[start:])
                if code[:current].rfind("\n") != -1:
                    column = code[:current].rfind("\n") - 1
                currentNode.condition = str(firstLine + code[:start].count("\n")) + ":" + str(column)
                currentNode.condFalse = ConditionNode(0)
                currentNode.condTrue = ConditionNode(1)
            currentNode = currentNode.condFalse
            start = current
            conditionCount += 1
        current += 1
    column = firstColumn + start + findNextOperator(code[start:])
    if code[:current].rfind("\n") != -1:
        column = code[:current].rfind("\n") - 1
    currentNode.condition = str(firstLine + code[:start].count("\n")) + ":" + str(column)
    currentNode.condFalse = ConditionNode(0)
    currentNode.condTrue = ConditionNode(1)
    return current

def fillSubNodes(node, fill, branch):
    if branch == "T":
        if node.condition == 1:
            node.condTrue = fill
            return
        if node.condFalse != None:
            fillSubNodes(node.condFalse, fill, branch)
        if node.condTrue != None:
            fillSubNodes(node.condTrue, fill, branch)
    if branch == "F":
        if node.condition == 0:
            node.condFalse = fill
            return
        if node.condTrue != None:
            fillSubNodes(node.condTrue, fill, branch)
        if node.condFalse != None:
            fillSubNodes(node.condFalse, fill, branch)

def replaceSubNodes(node, fill, branch):
    if branch == "T" and node.condition == 1:
        node.condition = fill
    if branch == "F" and node.condition == 0:
        node.condition = fill
    if node.condFalse != None:
        replaceSubNodes(node.condFalse, fill, branch)
    if node.condTrue != None:
        replaceSubNodes(node.condTrue, fill, branch)

def findBlockEnd(code):
    lvl = 1
    for i, character in enumerate(code):
        if character == "{":
            lvl += 1
        if character == "}":
            lvl -= 1
        if lvl == 0:
            return i
    return -1

def checkIfCondition(code):
    if len(code) == 0:
        return True
    if code.startswith("&&"):
        return True
    if code.startswith("||"):
        return True
    if code.endswith("!"):
        return True
    return False

def findConditionEnd(code):
    lvl = 1
    for i, character in enumerate(code):
        if character == "(":
            lvl += 1
        if character == ")":
            lvl -= 1
        if lvl == 0:
            return i
    return -1

def findNextCharacter(code):
    pos = 0
    while pos < len(code):
        if code[pos:].startswith("try"):
            pos += 3
        if code[pos] != " " and code[pos] != "\n" and code[pos] != "{":
            return pos
        pos += 1
    return 0

def findNextOperator(code):
    pos = 0
    while pos < len(code):
        if (code[pos] == ">" and code[pos-1] != "-") or code[pos] == "<" or code[pos:pos+1] == "<=" or code[pos:pos+2] == ">=" or code[pos:pos+2] == "==" or code[pos:pos+2] == "!=": # or code[pos] == "!":
            stepOver = False
            if code[pos] == "<":
                possibleBracketEnd = code.find(">")
                if possibleBracketEnd != -1 and code[possibleBracketEnd-1] != "-" and pos < possibleBracketEnd and code[pos:possibleBracketEnd].find("&&") == -1 and code[pos:possibleBracketEnd].find("||") == -1:
                    stepOver = True
            if code[pos] == ">" and code[pos-1] != "-":
                possibleBracketStart = code.find("<")
                if possibleBracketStart != -1 and  pos > possibleBracketStart and code[possibleBracketStart:pos].find("&&") == -1 and code[pos:possibleBracketStart:pos].find("||") == -1:
                    stepOver = True
            if not stepOver:
                return pos 
        pos += 1
    return 0

def findNextStatement(code):
    searchEqual = False
    searchDot = False
    searchPointer = False
    charPos = findConditionEnd(code) + 1
    nextSemicolon = charPos + code[charPos:].find(";")
    if code[charPos:nextSemicolon].find("=") != -1:
        searchEqual = True
    elif code[charPos:nextSemicolon].find(".") != -1:
        searchDot = True
    elif code[charPos:nextSemicolon].find("->") != -1:
        searchPointer = True
    while(charPos < len(code)):
        if searchEqual:
            if code[charPos] == "=":
                return charPos + 1
        elif searchDot:
            if code[charPos] == ".":
                return charPos
        elif searchPointer:
            if code[charPos:].startswith("->"):
                return charPos + 1
        else:
            if code[charPos:].startswith("try"):
                charPos += 3
            if code[charPos:].startswith("//"):
                charPos += code[charPos:].find("\n")
            if code[charPos:].startswith("/*"):
                charPos += code[charPos:].find("*/")+2
            if code[charPos:].startswith("long") or code[charPos:].startswith("char") or code[charPos:].startswith("uint32_t"):
                endStatement = code[charPos:].find(";")
                if code[charPos:charPos+endStatement].find("=") == -1:
                    charPos = endStatement
                else:
                    charPos = charPos + code[charPos:].find(" ") -1
            if code[charPos] != "\n" and code[charPos] != "{" and code[charPos] != " ":
                return charPos
        charPos += 1

def findElseStatment(code, opening):
    pos = 0
    while(pos < len(code)):
        if code[pos:].startswith("try"):
            pos += 3
        if code[pos:].startswith("//"):
            pos += code[pos:].find("\n")
        if code[pos:].startswith("/*"):
            pos += code[pos:].find("*/")+2
        if code[pos] != "\n" and code[pos] != "{" and code[pos] != " " and code[pos] != "(" and not code[pos:].startswith("else") and not code[pos:].startswith("if"):
            return pos
        if code[pos:].startswith("else if"):
            pos += 7
        if code[pos:].startswith("else"):
            pos += 4
        if code[pos:].startswith("if"):
            pos += 2
        if code[pos] == "}":
            foundBlockend = True
        pos += 1
    return pos

def findFalseStatement(code):
    cleanCode = code.replace("\n", "").replace(" ", "")
    if cleanCode.find(")") == cleanCode.find("){"):
        trueStatement = findNextStatement(code)
        blockend = findBlockEnd(code[trueStatement:])
        return trueStatement + blockend + findElseStatment(code[trueStatement+blockend+1:], True)
    else:
        trueStatement = findNextStatement(code)
        endTrueStatement = code[trueStatement:].find(";") + 1
        return trueStatement+endTrueStatement + findElseStatment(code[trueStatement+endTrueStatement:], False)


def findBranch(code, token, firstLine, branches):
    start = 0
    end = len(code)
    currentLine = firstLine
    while(start < len(code)):
        currentLine = firstLine + code[:start].count("\n")
        subcode = code[start:end]
        substart = subcode.find(token) + len(token)
        currentLine += subcode[:substart].count("\n")
        if substart != (-1 + len(token)):
            condition_end = findConditionEnd(subcode[substart:])
            if condition_end != -1:
                column = (start+substart) - code[:start + substart].rfind("\n") - 1
                conditions = subcode[substart:substart+condition_end]
                root = ConditionNode(0)
                if(token.find("for") != -1):
                    conditions = conditions.split(";")

                    if len(conditions) == 1:
                        return
                    column += len(conditions[0]) + 1
                    if conditions[1].strip() == "":
                        return
                    conditions = conditions[1]
                if(token.find("while") != -1 ) and conditions.strip() == "true":
                    return
                if(token.find("while") != -1 ) and findNextOperator(conditions) == 0 and conditions.find("&&") == -1 and conditions.find("||") == -1 and conditions.find("()") == -1:
                    if code.find("while") == code.find("while "):
                        column = code.find("while") - 1
                    else:
                        column = code.find("while") 
                disassembleConditions(conditions, root, firstLine + code[:start+substart].count("\n"), column)
                trueStatement = findNextStatement(subcode[substart:])
                trueLine = currentLine + subcode[substart:substart+trueStatement].count("\n")
                trueColumn = trueStatement - subcode[substart:substart+trueStatement].rfind("\n")
                replaceSubNodes(root, str(trueLine) + ":" + str(trueColumn), "T")
                falseStatement = findFalseStatement(subcode[substart:]) - 1
                falseLine = currentLine + subcode[substart:substart+falseStatement].count("\n")
                falseColumn = falseStatement - subcode[substart:substart+falseStatement].rfind("\n") 
                replaceSubNodes(root, str(falseLine) + ":" + str(falseColumn), "F")
                branches.append(root)
            start = start + substart
        else:
            start = len(code)

def findBranches(code, firstLine, branches):
    findBranch(code, " if(", firstLine, branches)
    findBranch(code, " if (", firstLine, branches)
    findBranch(code, " for(", firstLine, branches)
    findBranch(code, " for (", firstLine, branches)
    findBranch(code, " while(", firstLine, branches)
    findBranch(code, " while (", firstLine, branches)

def generateCoverageFileInformationRecursive(content, code, lines):
    end = 0
    if content.Type == "Method":
        content.LineNumber = lines + code[:code.replace("\t", " ").find(" " + content.Name + "(")].count("\n") + 1   
        interfaceStart = code.replace("\t", " ").find(" " + content.Name + "(")
        if interfaceStart == -1:
            content.LineNumber = lines + code[:code.replace("\t", " ").find(content.Name + "(")].count("\n") + 1   
            interfaceStart = code.replace("\t", " ").find(content.Name + "(")
        start = interfaceStart + code[interfaceStart:].find("{") + 1
        end = start + findBlockEnd(code[start:])
        content.LineNumber += code[code.replace("\t", " ").find(" " + content.Name + "("):start].count("\n")
        findBranches(code[start:end].replace("\t", " "),content.LineNumber, content.Branches)
        lines = lines + code[:end].count("\n")
        for i, line in enumerate(code[start:end].split("\n")):
            content.Content.append(Content("Line", i+content.LineNumber, [], []))
    else:
        for subcontent in content.Content:
            tmp_end, lines = generateCoverageFileInformationRecursive(subcontent, code[end:], lines)
            end = end + tmp_end
    return end, lines


def parseCodeContentHierarchy():
    global COVERAGE_STRUCTURE
    for file in fileStructure.FILES:
        if file[0] == "HW":
            appendFile(COVERAGE_STRUCTURE.HWLibraries, file)
        elif file[0] == "SW":
            appendFile(COVERAGE_STRUCTURE.SWLibraries, file)
        else:
            print("<X> error when parsing the code content hierarchy")

def parseCodeContent():
    global PC_LINE
    for hw in COVERAGE_STRUCTURE.HWLibraries:
        for file in hw.Files:
            with open(file.Name, "r") as source:
                code = source.read()
                start = code.find(configuration.CFG_PC + " = ")
                end = len(code)
                while start != -1:
                    possibleAssignment = code[start:code.find(configuration.CFG_PC + "  ")]
                    if possibleAssignment.strip().startswith(configuration.CFG_PC + " = "):
                        PC_LINE = file.Name + ":" + str(code[:start].count("\n") + 1)
                    if code[start:].find(configuration.CFG_PC + " = ") != -1:
                        start = start + code[start:].find(configuration.CFG_PC + " = ") + 1
                    else:
                        start = -1
                last_pos = 0
                lines = 0
                for content in file.Content:
                    tmp_pos, lines = generateCoverageFileInformationRecursive(content, code[last_pos:], lines)
                    last_pos = last_pos + tmp_pos

    for sw in COVERAGE_STRUCTURE.SWLibraries:
        for file in sw.Files:
            with open(file.Name, "r") as source:
                code = source.read().replace("\t", " ")
                last_pos = 0
                lines = 0
                for content in file.Content:
                    tmp_pos, lines = generateCoverageFileInformationRecursive(content, code[last_pos:], lines)
                    last_pos = last_pos + tmp_pos

def parseCoverageStructure():
    parseCodeContentHierarchy()
    parseCodeContent()