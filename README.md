# Relation Coverage

This repository is used to perform relation coverage.   
It contains a Pyhton script which performs following step:   
1. Generate a test programs
2. Compile the test programs using LLMV with RISC-V settings
3. Run the test program on the VP
4. Generate Structural and Relation Coverage
5. Store Results

## Prerequisites
- Working Python3 environment 
- [DynamoRIO](https://www.dynamorio.org)
- [ReportGenerator](https://reportgenerator.io/)
- [RISC-V VP++](https://github.com/ics-jku/riscv-vp-plusplus)

## Requirements
- Relation Coverage repository
- Running Experiments with RISC-V VP

## HowTo
1. Clone Relation Coverage repository
```
git clone https://github.com/ics-jku/relation_coverage.git
```
2. Clone RISCV-VP++ repository
```
git clone https://github.com/ics-jku/riscv-vp-plusplus.git
```
3. Install packages and build RISCV-VP++ according to README of RISCV-VP++
```
sudo apt install ...
make -j
```
4. Integrate the "mems_gyro.h", located in "Experiments/mems_gyro_hw", peripheral into the desired VP Platform
5. Edit "config/coverage_bar_tp*.ccfg" with your personal folder locations

Replace tokens in "<>" tags with your pathes e.g.
```
HARDWARE:<MAIN_FOLDER>/<VP_FOLDER>/vp/build/bin/riscv-vp
HARDWARE:/home/user/relation_coverage/riscv_vp_plusplus/vp/build/bin/riscv-vp
```
5. Execute environment
```
python3 UniCover.py ./config/coverage_bare_tp0.ccfg
```

## *Relation Coverage: A new Paradigm for Hardware/Software Testing*

[Christoph Hazott and Daniel Große. Relation Coverage: A new Paradigm for Hardware/Software Testing. In ETS, 2024.
](https://ics.jku.at/files/2024ETS_relation-coverage.pdf)

```
@inproceedings{HG:2024,
  author =        {Christoph Hazott and Daniel Gro{\ss}e},
  booktitle =     {European Test Symposium},
  title =         {Relation Coverage: A new Paradigm for
                   Hardware/Software Testing},
  year =          {2024},
}
```

