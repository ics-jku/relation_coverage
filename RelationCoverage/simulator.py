import subprocess

import configuration

def runSimulation():
    if configuration.CFG_TYPE == "BARE":
        coverage_tracer_call = ["drrun", "-c", "./coverage_simulator/build/libcoverage_simulator.so"]
        vp_param = configuration.CFG_COVERAGE_RESULT + ":" + configuration.CFG_HARDWARE + ":" + ":".join(configuration.CFG_HARDWARE_PARAMETERS) + ":" + configuration.CFG_SOFTWARE
        vp_param = vp_param.split(":")
        coverage_tracer_call = coverage_tracer_call + [vp_param[0], "--"]
        coverage_tracer_call = coverage_tracer_call + vp_param[1:]
        print(" ".join(coverage_tracer_call))
        subprocess.run(coverage_tracer_call)