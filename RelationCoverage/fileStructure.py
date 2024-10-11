import os

import configuration

LIBRARIES = []
FILES = []

def parseIncludeFileHierarchy(type, entry_file):
    for library in LIBRARIES:
        if (os.path.dirname(entry_file)) == library[0]:
            parseFileIncludes(type, entry_file, library)

def fileIsDuplicate(file_name):
    for existing_file in FILES:
        if existing_file[2] == os.path.abspath(file_name):
            return True
    return False

def parseFileIncludes(type, entry_file, base_library):
    global FILES
    global LIBRARIES
    FILES.append([type, base_library, os.path.abspath(entry_file)])
    with open(entry_file, "r") as code_file:
        for line in code_file:
            line = line.rstrip().lstrip()
            if(line.startswith('#include "')):
                file_name = line.replace('"', "").replace("#include ", "")
                for library in LIBRARIES:
                    file = library[0] + "/" + file_name
                    if os.path.exists(file) and not fileIsDuplicate(file):
                        parseFileIncludes(type, file, library)
                        if file.endswith(".h"):
                            file_cpp = file.replace(".h", ".cpp")
                            file_c = file.replace(".h", ".c")
                            if os.path.exists(file_cpp) and not fileIsDuplicate(file_cpp):
                                parseFileIncludes(type, file_cpp, library)
                            if os.path.exists(file_c) and not fileIsDuplicate(file_c):
                                parseFileIncludes(type, file_c, library)
                                

def removeUnusedLibraries():
    global LIBRARIES
    baseLibrary = ""
    for i, library in enumerate(LIBRARIES):
        to_be_removed = []
        for j, include_library in enumerate(library[2]):
            found = False
            for existing_library in LIBRARIES:
                if existing_library[1] == include_library:
                    found = True
            if not found:
                to_be_removed.append(include_library)
        for remove in to_be_removed:
            LIBRARIES[i][2].remove(remove)
    to_be_removed = []

    for i, library in enumerate(LIBRARIES):
        if library[0] != os.path.dirname(configuration.CFG_HARDWARE_MAIN_ENTRY):
            found = False
            for existing_library in LIBRARIES:
                for j, include_library in enumerate(existing_library[2]):
                    if library[1] == include_library:
                        found = True
            if not found:
                to_be_removed.append(library)
    for remove in to_be_removed:
        LIBRARIES.remove(remove)

def parseCMAKE(folder):
    global LIBRARIES
    libname = ""
    libs = []
    arr = os.listdir(folder) 
    for file in arr:
        if(file == "CMakeLists.txt"):
            with open(folder + "/" + file, "r") as cmake:
                for cmake_line in cmake:
                    cmake_line = cmake_line.rstrip()
                    if cmake_line.startswith("add_library("):
                        libname = cmake_line[cmake_line.find("(")+1::]
                    if cmake_line.startswith("target_link_libraries"):
                        libs = cmake_line[cmake_line.find("(")+1:cmake_line.find(")")].split(" ")
        if os.path.isdir(folder + "/" + file):
            parseCMAKE(folder + "/" + file)
    if libname != "":
        for i, lib in enumerate(libs):
            if libname == lib:
                del libs[i]
    LIBRARIES.append([folder, libname, libs])

def parseMAKE(type, folder):
    files = os.listdir(folder)
    for file in files:
        if(file == "Makefile"):
            with open(folder + "/" + file, "r") as make:
                for make_line in make:
                    make_line = make_line.rstrip().lstrip()
                    if make_line.startswith("include "):
                        parseMAKE(folder + "/" + make_line.split(" ")[1].replace("Makefile", ""))
                    if make_line.startswith("OBJECTS"):
                        tokens = make_line.split("=")
                        objects = tokens[1].split(" ")
                        for object in objects:
                            if object != "":
                                if os.path.exists(folder.replace("../", "") + "/" + object.replace(".o", ".c")):
                                    FILES.append([type, [folder, os.path.basename(folder), []], os.path.abspath(folder.replace("../", "") + "/" + object.replace(".o", ".c"))])
                                if os.path.exists(folder.replace("../", "") + "/" + object.replace(".o", ".cpp")):
                                    FILES.append([type, [folder, os.path.basename(folder), []], os.path.abspath(folder.replace("../", "") + "/" + object.replace(".o", ".cpp"))])
                                if os.path.exists(folder.replace("../", "") + "/" + object.replace(".o", ".h")):
                                    FILES.append([type, [folder, os.path.basename(folder), []], os.path.abspath(folder.replace("../", "") + "/" + object.replace(".o", ".h"))])
                    if make_line.startswith("$(CC) ") and make_line.find("-I") > 0:
                        include_folders = make_line.split("-I")[1].split("-")[0].split(" ")
                        for include_folder in include_folders:
                            include_subfolders = os.listdir(folder.replace("../", "") + include_folder)
                            for include_file in include_subfolders:
                                 if(os.path.basename(include_file).endswith(".h") or os.path.basename(include_file).endswith(".hpp") or os.path.basename(include_file).endswith(".c") or os.path.basename(include_file).endswith(".cpp")):
                                    found = False
                                    for existingFile in FILES:
                                        if existingFile[2] == os.path.abspath(folder.replace("../", "") + include_folder + include_file):
                                            found = True
                                    if not found:
                                        includePath = os.path.abspath(folder.replace("../", "") + include_folder)
                                        libName = os.path.basename(include_folder.replace("/", "").replace("..", ""))
                                        FILES.append([type, [includePath, libName, []], os.path.abspath(folder.replace("../", "") + include_folder + include_file)])


def parseFileStructure():

    if configuration.CFG_HARDWARE_BUILD_SYSTEM == "CMAKE":
        parseCMAKE(configuration.CFG_HARDWARE_MAIN_FOLDER)
        removeUnusedLibraries()
    else:
        parseMAKE("HW", configuration.CFG_HARDWARE_MAIN_FOLDER)
    parseIncludeFileHierarchy("HW", configuration.CFG_HARDWARE_MAIN_ENTRY)

    LIBRARIES = []

    if configuration.CFG_SOFTWARE_BUILD_SYSTEM == "CMAKE":
        parseCMAKE(configuration.CFG_SOFTWARE_MAIN_FOLDER)
        removeUnusedLibraries()
    else:
        parseMAKE("SW", configuration.CFG_SOFTWARE_MAIN_FOLDER)
    parseIncludeFileHierarchy("SW", configuration.CFG_SOFTWARE_MAIN_ENTRY)
