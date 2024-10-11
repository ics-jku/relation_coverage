#ifndef __MEMS_GYRO_H__
#define __MEMS_GYRO_H__

#include <stdint.h>

static volatile char * const TERMINAL_ADDR = (char * const)0x20000000;
//static volatile char * const MEMS_GYRO_INPUT_ADDR = (char * const)0x50000000;
static volatile uint32_t * const CONFIG_REG_ADDR = (uint32_t * const)0x50000010;
static volatile uint32_t * const STATUS_REG_ADDR = (uint32_t * const)0x50000010;
static volatile uint32_t * const X_DATA_REG_ADDR = (uint32_t * const)0x50000030;
static volatile uint32_t * const Y_DATA_REG_ADDR = (uint32_t * const)0x50000034;
static volatile uint32_t * const Z_DATA_REG_ADDR = (uint32_t * const)0x50000038;

void mems_gyro_irq_handler();

void init_mems_gyro();
void enable_interrupt();
void disable_interrupt();
void enable_axes(_Bool x, _Bool y, _Bool z);
int get_x_axis();
int get_y_axis();
int get_z_axis();
void print_mems_gyro_data();

#endif