import subprocess

import configuration

def generateReport():
    report_generator_call = ["ReportGenerator", "-reports:" + configuration.CFG_COVERAGE_RESULT.replace(".trc", ".xml"), "-targetdir:" + configuration.CFG_COVERAGE_RESULT.replace(".trc", "_report")]
    subprocess.run(report_generator_call)