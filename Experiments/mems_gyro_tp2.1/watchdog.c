#include <stdlib.h>
#include "irq.h"

#include "watchdog.h"

const int WATCHDOG_IRQ_ID = 3;

_Bool watchdog_triggered = false;

void watchdog_init(){
    
    *INTERVAL_REG_ADDR = 100;
    register_interrupt_handler(WATCHDOG_IRQ_ID, watchdog_handler);
}

void watchdog_handler() {
    exit(1);
}