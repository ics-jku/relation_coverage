#!/bin/sh
{ time python3 UniCover.py ../config/coverage_bare_tp0.ccfg ; } #> ../results/coverage_tracer_tp0.out 2>&1
{ time python3 UniCover.py ../config/coverage_bare_tp1.ccfg ; } #> ../results/coverage_tracer_tp1.out 2>&1
{ time python3 UniCover.py ../config/coverage_bare_tp1.1.ccfg ; } #> ../results/coverage_tracer_tp1.1.out 2>&1
{ time python3 UniCover.py ../config/coverage_bare_tp2.ccfg ; } #> ../results/coverage_tracer_tp2.out 2>&1
{ time python3 UniCover.py ../config/coverage_bare_tp2.1.ccfg ; } #> ../results/coverage_tracer_tp2.1.out 2>&1
{ time python3 UniCover.py ../config/coverage_bare_tp2.2.ccfg ; } #> ../results/coverage_tracer_tp2.1.out 2>&1
{ time python3 UniCover.py ../config/coverage_bare_tp2.3.ccfg ; } #> ../results/coverage_tracer_tp2.1.out 2>&1
