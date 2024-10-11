#include "mems_gyro.h"
#include "irq.h"
#include "stdbool.h"
#include "stdlib.h"
#include "watchdog.h"

volatile _Bool has_data = 0;

const int MEMS_GYRO_IRQ_ID = 2;
const int SAMPLE_RATE = 1; //ms

void mems_gyro_irq_handler() {
    //int status = *STATUS_REG_ADDR;
    //if((status & 1) || (status & 2) || (status & 4)){
    has_data = 1;
    //}
}

void enable_interrupt(int sample_rate){
    int config = *CONFIG_REG_ADDR;
    config = (config & 0xF) | (sample_rate << 4) | 1;
    *CONFIG_REG_ADDR = config;
}

void disable_interrupt(){
    int config = *CONFIG_REG_ADDR;
    config = config & 0xFFFFFFFE;
    *CONFIG_REG_ADDR = config;
}

void init_mems_gyro() {
    //disable_interrupt();
    register_interrupt_handler(MEMS_GYRO_IRQ_ID, mems_gyro_irq_handler);
}

void enable_axes(_Bool x, _Bool y, _Bool z) {
    int config;
    config = *CONFIG_REG_ADDR;

    if(x){
        config = config | 2;
    }else{
        config = config & 0xFFFFFFFD;
    }
    if(y){
        config = config | 4;
    }else{
        config = config & 0xFFFFFFFB;
    }
    if(z){
        config = config | 8;
    }else{
        config = config & 0xFFFFFFF7;
    }

    *CONFIG_REG_ADDR = config;
}

int get_x_axis(){
    return *X_DATA_REG_ADDR;
}

int get_y_axis(){
    return *Y_DATA_REG_ADDR;
}

int get_z_axis(){
    return *Z_DATA_REG_ADDR;
}

void print_mems_gyro_data() {
    int status;
    while(!has_data) {
        asm volatile("wfi");
    }
    has_data = 0;
    char result[10];

    *TERMINAL_ADDR = 'X';
    *TERMINAL_ADDR = ':';
    itoa(get_x_axis(), result, 10);
    for(int i=0; i<9; ++i) {
        *TERMINAL_ADDR = result[i];
    }
    *TERMINAL_ADDR = ' ';

    *TERMINAL_ADDR = 'Y';
    *TERMINAL_ADDR = ':';
    itoa(get_y_axis(), result, 10);
    for(int i=0; i<9; ++i) {
        *TERMINAL_ADDR = result[i];
    }
    *TERMINAL_ADDR = ' ';

    *TERMINAL_ADDR = 'Z';
    *TERMINAL_ADDR = ':';
    itoa(get_z_axis(), result, 10);
    for(int i=0; i<9; ++i) {
        *TERMINAL_ADDR = result[i];
    }
    *TERMINAL_ADDR = ' ';

    *TERMINAL_ADDR = '\n';
   
}