#ifndef RISCV_ISA_MEMS_GYRO_H
#define RISCV_ISA_MEMS_GYRO_H

#include <cstdlib>
#include <cstring>

#include <systemc>

#include <tlm_utils/simple_target_socket.h>

#include "core/common/irq_if.h"

struct MEMSGyro : public sc_core::sc_module {
	tlm_utils::simple_target_socket<MEMSGyro> tsock;

	interrupt_gateway *plic = 0;
	uint32_t irq_number = 0;
	sc_core::sc_event run_event;

	// memory mapped configuration registers
	uint32_t config = 0x30; // default samplerate = 5us (1x) all config bits are off (x0)
	//uint32_t status = 0;
	int32_t x_data = 0;
	int32_t y_data = 0;
	int32_t z_data = 0;

	enum {
		CONFIG_REG_ADDR = 0x10,
		//STATUS_REG_ADDR = 0x20,
		X_DATA_REG_ADDR = 0x30,
		Y_DATA_REG_ADDR = 0x34,
		Z_DATA_REG_ADDR = 0x38
	};

	SC_HAS_PROCESS(MEMSGyro);

	MEMSGyro(sc_core::sc_module_name, uint32_t irq_number) : irq_number(irq_number) {
		tsock.register_b_transport(this, &MEMSGyro::transport);
		SC_THREAD(run);
	}

	void transport(tlm::tlm_generic_payload &trans, sc_core::sc_time &delay) {
		auto addr = trans.get_address();
		auto cmd = trans.get_command();
		auto len = trans.get_data_length();
		auto ptr = trans.get_data_ptr();

		if (cmd == tlm::TLM_WRITE_COMMAND){
			config = *((uint32_t *)ptr);
			run_event.cancel();
			run_event.notify(sc_core::sc_time(1, sc_core::SC_US));
		}else {
			if(addr == CONFIG_REG_ADDR) {
				*((uint32_t *)ptr) = config;
			}
			//if(addr == STATUS_REG_ADDR) {
			//	*((uint32_t *)ptr) = status;
			//}
			if(addr == X_DATA_REG_ADDR) {
				*((int32_t *)ptr) = x_data;
			}
			if(addr == Y_DATA_REG_ADDR) {
				*((int32_t *)ptr) = y_data;
			}
			if(addr == Z_DATA_REG_ADDR) {
				*((int32_t *)ptr) = z_data;
			}
		}
		(void)delay;  // zero delay
	}

	void run() {
		while (true) {
			uint sample_rate = config & 0xFFFFFFF0;
			sample_rate = sample_rate >> 4;
			run_event.notify(sc_core::sc_time(sample_rate, sc_core::SC_US));
			sc_core::wait(run_event);  // 40 times per second by default
			
			bool int_enabled = config & 1;
			bool x_enabled = config & 2;
			bool y_enabled = config & 4;
			bool z_enabled = config & 8; 
			
			if(x_enabled) {
				x_data = rand() % 100 - 180;
				//status = status | 1;
			}else{
				x_data = 0;
				//status = status & 0xFFFFFFFE;
			}
			if(y_enabled) {
				y_data = rand() % 100 - 180;
				//status = status | 2;
			}else{
				y_data = 0;
				//status = status & 0xFFFFFFFD;
			}
			if(z_enabled) {
				z_data = rand() % 100 - 180;
				//status = status | 4;
			}else{
				z_data = 0;
				//status = status & 0xFFFFFFFB;
			}
			if(int_enabled){
				plic->gateway_trigger_interrupt(irq_number);
			}
		}
	}
};

#endif  // RISCV_ISA_SENSOR_H
