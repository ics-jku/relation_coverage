import sys
import time
import subprocess

import configuration
import relationCoverage
import fileStructure
import coverageStructure
import addressTranslation
import simulator
import coverageResults
import reportGenerator

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage " + sys.argv[0] + " <coverage_configuration_file>")
        sys.exit(1)

    print("Start reading configuration...")
    current_time = time.time()
    configuration.parseConfig(sys.argv[1])
    print("...Finished reading configratuion: " + str(time.time()-current_time))

    print("Start reading relations...")
    current_time = time.time()
    relationCoverage.parseRelationsFile(configuration.CFG_RELATIONS)
    print("...Finished reading relations: " + str(time.time()-current_time))
    
    print("Start static code analysis...")
    current_time = time.time()
    fileStructure.parseFileStructure()
    print("...Finished analysing file structure: " + str(time.time()-current_time))
    sub_current_time = time.time()
    coverageStructure.parseCoverageStructure()
    print("...Finished analysing source code structure: " + str(time.time()-sub_current_time))
    sub_current_time = time.time()
    addressTranslation.generateAddressTable()
    print("...Finished generation of address table: " + str(time.time()-sub_current_time))
    print("...Finished static code analysis: " + str(time.time()-current_time))

    for relation in relationCoverage.RELATIONS:
        if relation.Type == "EQU":
            print(relation.Name + ":" + relation.Lhs)

    print("Start simulation (without)...")
    current_time = time.time()
    vp_param = configuration.CFG_HARDWARE + ":" + ":".join(configuration.CFG_HARDWARE_PARAMETERS) + ":" + configuration.CFG_SOFTWARE
    vp_param = vp_param.split(":")
    subprocess.run(vp_param)
    print("...Finished simulation (withou): " + str(time.time()-current_time))

    print("Start simulation....")
    current_time = time.time()
    simulator.runSimulation()
    print("...Finished simulation: " + str(time.time()-current_time))

    print("Start reading coverage results...")
    current_time = time.time()
    coverageResults.processCoverageResults()
    print("...Finished reading coverage results: " + str(time.time()-current_time))

    print("Start generating code report...")
    current_time = time.time()
    reportGenerator.generateReport()
    print("...Finished generating code report: " + str(time.time()-current_time))

    print("Start generating relation report...")
    current_time = time.time()
    relationCoverage.generateReport()
    print("...Finished generating relation report: " + str(time.time()-current_time))

    