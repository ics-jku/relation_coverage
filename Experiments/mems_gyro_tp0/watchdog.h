#ifndef __WATCHDOG_H__
#define __WATCHDOG_H__

#include <stdint.h>
#include <stdbool.h>

extern _Bool watchdog_triggered;

//static volatile char * const MEMS_GYRO_INPUT_ADDR = (char * const)0x50000000;
static volatile uint32_t * const INTERVAL_REG_ADDR = (uint32_t * const)0x50001010;

void watchdog_init();
void watchdog_handler();

#endif