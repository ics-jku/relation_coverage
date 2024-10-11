OBJECTS = main.o irq.o mems_gyro.o test_package.o bootstrap.o watchdog.o
CFLAGS = --sysroot=$(HOME)/riscv/riscv64-unknown-elf --gcc-toolchain=$(HOME)/riscv --target=riscv32 -march=rv32i -g3
LDFLAGS = -march=rv32i -mabi=ilp32 -nostartfiles -Wl,--no-relax -g3

override CC = /bin/clang
override CXX = /bin/clang++
override LD = riscv64-unknown-elf-gcc


EXECUTABLE ?= main

$(EXECUTABLE): $(OBJECTS)
	$(LD) -o $@ $(LDFLAGS) $^

%.o: %.S
	$(CC) $(CFLAGS) -c $<
%.o: %.c
	$(CC) $(CFLAGS) -c $<
%.o: %.cpp
	$(CXX) $(CFLAGS) -c $<

clean:
	rm -f $(OBJECTS) $(EXECUTABLE)

.PHONY: clean
.DEFAULT_GOAL := $(EXECUTABLE)