#include "dr_api.h"

#include <unistd.h> //getpid();
#include <string.h> //strtok...

#include <stdlib.h>

#include <stdio.h>
#include <fcntl.h>
#include <errno.h>
#include <termios.h>

static file_t trace_file;

#define BUFFER_SIZE_BYTES(buf) sizeof(buf)
#define BUFFER_SIZE_ELEMENTS(buf) (BUFFER_SIZE_BYTES(buf)) / sizeof((buf)[0])
#define BUFFER_LAST_ELEMENT(buf) (buf)[BUFFER_SIZE_ELEMENTS(buf) - 1]
#define NULL_TERMINATE_BUFFER(buf) BUFFER_LAST_ELEMENT(buf) = 0

#define MAPS_LINE_LENGTH 8192
#define MAPS_LINE_FORMAT4 "%08lx-%08lx %s %*x %*s %*u %4096s"
#define MAPS_LINE_MAX4 49 /* sum of 8 1 8 1 4 1 8 1 5 1 10 1 */
#define MAPS_LINE_FORMAT8 "%016lx-%016lx %s %*x %*s %*u %4096s"
#define MAPS_LINE_MAX8 73 /* sum of 16 1 16 1 5 1 16 1 5 1 10 1 */
#define MAPS_LINE_MAX MAPS_LINE_MAX8

#define MAX_VP_RIPS 0x2FFFFF
#define MAX_SW_PCS 0x2FFFFF
//#define MAX_MOD_PCS 0x2FFFFF

#define MAX_ADDRESS_LINES 512000

static uint64 base_address;

static int lowest_address = 0xFFFFFFF;
static int highest_address = 0;

static void * find_exe_base();
static void parse_trace_addresses();

static uint riscv_pc = 0;
static bool vp_address[MAX_VP_RIPS] = {false};
static bool sw_address[MAX_SW_PCS] = {false};
//static bool mod_address[MAX_MOD_PCS] = {false};
static uint64 vp_rips[MAX_VP_RIPS] = {0};
static uint64 sw_pcs[MAX_SW_PCS] = {0};
//static uint64 mod_pcs[MAX_MOD_PCS] = {0};

struct branch{
    uint64 branch_true;
    uint64 branch_false;
} ;

static uint64 true_rip[MAX_VP_RIPS] = {0};
static uint64 false_rip[MAX_VP_RIPS] = {0};
static uint64 true_pc[MAX_SW_PCS] = {0};
static uint64 false_pc[MAX_SW_PCS] = {0};
//static uint64 true_mod_pc[MAX_MOD_PCS] = {0};
//static uint64 false_mod_pc[MAX_MOD_PCS] = {0};

static bool recording = true;
static uint64 start_address = 0;
static uint64 end_address = 0;
//static uint64 mod_start_address = 0;
//static uint64 mod_end_address = 0;
static uint64 serial_trigger_address = 0;

static int serial_port;
static const char * channel = "";
static bool cleanup = false;

static struct branch hw_branches_addresses[MAX_VP_RIPS] = {0,0};
static struct branch hw_branches[MAX_VP_RIPS] = {0,0};
static struct branch sw_branches_addresses[MAX_SW_PCS] = {0,0};
static struct branch sw_branches[MAX_SW_PCS] = {0,0};
//static struct branch mod_branches_addresses[MAX_MOD_PCS] = {0,0};
//static struct branch mod_branches[MAX_MOD_PCS] = {0,0};

//void *recording_lock;
//void *address_lock;

static char read_string[256];

static void config_serial();

static dr_emit_flags_t event_basic_block(void *drcontext, void *tag, instrlist_t *bb, bool for_trace, bool translating);
static void event_exit(void);

static void clean_call_wait_for_uart(app_pc pc);
static void clean_call_rip(uint rip);
static void clean_call_pc(uint reg);

DR_EXPORT void dr_client_main(client_id_t id, int argc, const char *argv[]) {
    if(argc < 2) {
        dr_printf("Trace file missing!\n");
        return;
    }

    base_address = (uint64)(find_exe_base());
    parse_trace_addresses();
    dr_register_exit_event(event_exit);
    
    dr_register_bb_event(event_basic_block);

    if(argc > 2) {
        channel = argv[2];
        config_serial();
        //dr_create_client_thread(client_thread, NULL);
        recording = false;
        //recording_lock = dr_mutex_create();
        //address_lock = dr_mutex_create();
    }
    dr_delete_file(argv[1]);
    trace_file = dr_open_file(argv[1], DR_FILE_WRITE_OVERWRITE);
}

static void config_serial() {
    serial_port = open(channel, O_RDWR);
    struct termios tty;
    if(tcgetattr(serial_port, &tty) != 0) {
        dr_printf("Error %i from tcsetattr: %s\n", errno, strerror(errno));
        return;
    }
    tty.c_cflag &= ~PARENB;
    tty.c_cflag &= ~CSTOPB;
    tty.c_cflag &= ~CSIZE;
    tty.c_cflag |= CS8;
    tty.c_cflag &= ~CRTSCTS;
    tty.c_cflag |= CREAD | CLOCAL;

    tty.c_lflag &= ~ICANON;
    tty.c_lflag &= ~ECHO;
    tty.c_lflag &= ~ECHOE;
    tty.c_lflag &= ~ECHONL;
    tty.c_lflag &= ~ISIG;
    
    tty.c_iflag &= ~(IXON | IXOFF | IXANY);
    tty.c_iflag &= ~(IGNBRK | BRKINT | PARMRK | ISTRIP | INLCR | IGNCR | ICRNL);

    tty.c_oflag &= ~OPOST;
    tty.c_oflag &= ~ONLCR;

    tty.c_cc[VTIME] = 10;
    tty.c_cc[VMIN] = 0;
    cfsetispeed(&tty, B115200);
    cfsetospeed(&tty, B115200);

    if (tcsetattr(serial_port, TCSANOW, &tty) != 0) {
        dr_printf("Error %i from tcsetattr: %s\n", errno, strerror(errno));
        return;
    }

}

static void parse_trace_addresses() {
    char line[MAX_ADDRESS_LINES];

    file_t trace_addresses = dr_open_file("../experiments/config/address.tbl", DR_FILE_READ);
    uint64 read = dr_read_file(trace_addresses, &line, MAX_ADDRESS_LINES);
    char *token = strtok(line, "\n");

   
    while(token != NULL) {
        char str[128];
        char *ptr;

        strcpy(str, token);
        strtok_r(str,":", &ptr);
        if(strcmp(str, "0") == 0) {
            int address = atoi(ptr);
            if(lowest_address > address) {
                lowest_address = address;
            }
            if(highest_address < address) {
                highest_address = address;
            }
            vp_address[address] = true;
            //dr_printf("HW_STMT:%d\n", atoi(ptr));
        }
        if(strcmp(str, "1") == 0) {
            int counter=0;
            char *subtoken;
            int hw_branch;
            int hw_true;
            int hw_false;
            while(subtoken = strsep(&ptr, ":")){
                if(counter == 0){ hw_branch = atoi(subtoken); }
                if(counter == 1){ hw_true = atoi(subtoken); }
                if(counter == 2){ hw_false = atoi(subtoken); }
                counter++;
            }
            hw_branches_addresses[hw_branch].branch_true = hw_true;
            hw_branches_addresses[hw_branch].branch_false = hw_false;
        }
        if(strcmp(str, "2") == 0) {
            sw_address[atoi(ptr)] = true;
            //dr_printf("SW_STMT:%d\n", atoi(ptr));
        }
        if(strcmp(str, "3") == 0) {
            int counter=0;
            char *subtoken;
            int sw_branch;
            int sw_true;
            int sw_false;
            while(subtoken = strsep(&ptr, ":")){
                if(counter == 0){ sw_branch = atoi(subtoken); }
                if(counter == 1){ sw_true = atoi(subtoken); }
                if(counter == 2){ sw_false = atoi(subtoken); }
                counter++;
            }
            sw_branches_addresses[sw_branch].branch_true = sw_true;
            sw_branches_addresses[sw_branch].branch_false = sw_false;
        }
        if(strcmp(str, "4") == 0) {
            riscv_pc = atoi(ptr); 
        }
        /*if(strcmp(str, "5") == 0) {
            mod_address[atoi(ptr)] = true;
            //dr_printf("SW_STMT:%d\n", atoi(ptr));
        }
        if(strcmp(str, "6") == 0) {
            int counter=0;
            char *subtoken;
            int mod_branch;
            int mod_true;
            int mod_false;
            while(subtoken = strsep(&ptr, ":")){
                if(counter == 0){ mod_branch = atoi(subtoken); }
                if(counter == 1){ mod_true = atoi(subtoken); }
                if(counter == 2){ mod_false = atoi(subtoken); }
                counter++;
            }
            mod_branches_addresses[mod_branch].branch_true = mod_true;
            mod_branches_addresses[mod_branch].branch_false = mod_false;
        }*/
        if(strcmp(str, "7") == 0) {
            serial_trigger_address = atoi(ptr); 
        }
        token = strtok(NULL, "\n");
    }
}

static void *find_exe_base() {
    pid_t pid = getpid();
    char proc_pid_maps[64]; /* filename */
    file_t maps;
    char exe_path[MAPS_LINE_LENGTH];

    char line[MAPS_LINE_LENGTH];
    int len = snprintf(proc_pid_maps, BUFFER_SIZE_ELEMENTS(proc_pid_maps), "/proc/%d/maps", pid);
    if (len < 0 || len == sizeof(proc_pid_maps)) {
        DR_ASSERT(0);
    }

    maps = dr_open_file(proc_pid_maps, DR_FILE_READ);
    uint64 read = dr_read_file(maps, &line, MAPS_LINE_LENGTH);
    char *token = strtok(line, "\n");
    while(token != NULL) {
        void *vm_start, *vm_end;
        char perm[16];
        char comment_buffer[MAPS_LINE_LENGTH];

        len = dr_sscanf(token, sizeof(void *) == 4 ? MAPS_LINE_FORMAT4 : MAPS_LINE_FORMAT8, (unsigned long *)&vm_start, (unsigned long*)&vm_end, perm, comment_buffer);
        if (len < 4){
            comment_buffer[0] = '\0';
        }
        
        if (strstr(comment_buffer, dr_get_application_name()) != 0) {
            dr_close_file(maps);
            return vm_start;
        }
        token = strtok(NULL, "\n");
    }
    dr_close_file(maps);
    return NULL;
}

static dr_emit_flags_t event_basic_block(void *drcontext, void *tag, instrlist_t *bb, bool for_trace, bool translating) {
    //dr_printf("Event Basic Block enabled\n");
    for(instr_t *instr = instrlist_first(bb); instr != NULL; instr = instr_get_next(instr)) {
        uint64 pc = (uint64)(instr_get_app_pc(instr));
        pc = pc - base_address;
        uint pc_32 = pc & 0xFFFFFFFF;
        /* TRACE RIPS*/
        //if(recording){
            //dr_printf("Recording started\n");
            if(pc_32 > 0 && pc_32 < MAX_VP_RIPS && vp_address[pc_32]) {
                //dr_printf("Instrumenting RIP\n");
                dr_insert_clean_call(drcontext, bb, instr, clean_call_rip, false, 1, OPND_CREATE_INT32(pc_32));
            }
            /* END TRACE RIPS */

            /* TRACE SW PC */
        
        //}
            if(pc_32 == riscv_pc){
                if(instr_writes_memory(instr)) {
                    //dr_printf("Instrumenting PC\n");
                    dr_insert_clean_call(drcontext, bb, instr, clean_call_pc, false, 1, OPND_CREATE_INT32(opnd_get_reg(instr_get_src(instr, 0))));
                }
            }
        //}
        if(channel != "") {
            if(pc_32 > 0 && pc_32 < MAX_VP_RIPS && pc_32 == serial_trigger_address) {
                dr_insert_clean_call_ex(drcontext, bb, instr, clean_call_wait_for_uart, DR_CLEANCALL_READS_APP_CONTEXT, 1, OPND_CREATE_INTPTR((ptr_uint_t)instr_get_app_pc(instr)));
            }
        }
    }
    return DR_EMIT_DEFAULT;
}

static void event_exit(void) {
    recording = false;
    dr_write_file(trace_file, &vp_rips, sizeof(vp_rips));
    dr_write_file(trace_file, &sw_pcs, sizeof(sw_pcs));
    //dr_write_file(trace_file, &mod_pcs, sizeof(mod_pcs));
    dr_write_file(trace_file, &hw_branches, sizeof(hw_branches));
    dr_write_file(trace_file, &sw_branches, sizeof(sw_branches));
    //dr_write_file(trace_file, &mod_branches, sizeof(mod_branches));
    dr_close_file(trace_file);
    dr_unregister_bb_event(event_basic_block);
    close(serial_port);
}

static void clean_call_wait_for_uart(app_pc pc){
    char read_buf[256];
    
    //memset(&read_buf, '\0', sizeof(read_buf));
    int num_bytes = read(serial_port, &read_buf, sizeof(read_buf));
    if(num_bytes > 0) {
        char cuttedString[256];
        memset(cuttedString, '\0', 256);
        strncpy(cuttedString, read_buf, num_bytes);
        strcat(read_string, cuttedString);
        //dr_printf("Message Received by Dynamorio:%s with length:%d\n", &read_buf, num_bytes);
        //dr_printf("CuttedString: %s", cuttedString);
        //dr_printf("Concatenated to: %s\n", read_string);
        if((strstr(read_string, "\r")) != NULL) {
            if ((strstr(read_string, "START:")) != NULL){
                char * read_tmp = read_string;
                //dr_mutex_lock(recording_lock);
                //dr_mutex_lock(address_lock);
                int counter=0;
                char *subtoken;
                while((subtoken = strsep(&read_tmp, ":"))){
                    if(counter == 0){}
                    if(counter == 1){ start_address = strtoul(subtoken, NULL, 0); /*dr_printf("StartAddress: 0x%llx\n", start_address);*/ }
                    if(counter == 2){ end_address = strtoul(subtoken, NULL, 0); /*dr_printf("EndAddress: 0x%llx\n", end_address);*/ }
                    //if(counter == 3){ mod_start_address = strtoul(subtoken, NULL, 0); }
                    //if(counter == 4){ mod_end_address = strtoul(subtoken, NULL, 0); }
                    counter++;
                }
                recording = true;
                read_string[0] = 0;
                //dr_printf("Flushing Region at start\n");
                /*if (!dr_flush_region(NULL, ~0UL))
                    DR_ASSERT(false);
                void *drcontext = dr_get_current_drcontext();
                dr_mcontext_t mcontext;
                mcontext.size = sizeof(mcontext);
                mcontext.flags = DR_MC_ALL;
                dr_get_mcontext(drcontext, &mcontext);
                mcontext.pc = pc;
                dr_redirect_execution(&mcontext);
                DR_ASSERT(false);
                //dr_unlink_flush_region((app_pc)base_address, highest_address);
                dr_delay_flush_region(NULL, ~0UL, 0, NULL);
                cleanup = true;*/

            } else if ((strstr(read_string, "STOP")) != NULL) {
                //dr_mutex_lock(recording_lock);
                //dr_printf("STOP Message Received by Dynamorio:%s\n", read_string);
                
                
                //return false;
                //dr_mutex_unlock(recording_lock);
                read_string[0] = 0;
                recording = false;
                //dr_printf("Flushing Region at end\n");
                /*if (!dr_flush_region(NULL, ~0UL))
                    DR_ASSERT(false);
                void *drcontext = dr_get_current_drcontext();
                dr_mcontext_t mcontext;
                mcontext.size = sizeof(mcontext);
                mcontext.flags = DR_MC_ALL;
                dr_get_mcontext(drcontext, &mcontext);
                mcontext.pc = pc;
                dr_redirect_execution(&mcontext);
                DR_ASSERT(false);*/
                //dr_unlink_flush_region((app_pc)base_address, highest_address);
                //dr_delay_flush_region(NULL, ~0UL, 0, NULL);
                //cleanup = true;
                
            }
            
        }
    }

}

static void clean_call_rip(uint rip) {
    //if(!recording){
    //    return;
    //}
    //if(channel != ""){
        //dr_mutex_lock(recording_lock);
        //if(!recording){
        //    dr_mutex_unlock(recording_lock);
        //    return;
        //}
        //dr_mutex_unlock(recording_lock);
    //}
    //dr_printf("CURRENTPC: 0x%08x\n", rip);
    if(hw_branches_addresses[rip].branch_true != 0 && hw_branches_addresses[rip].branch_false != 0) {
        true_rip[hw_branches_addresses[rip].branch_true] = rip;
        false_rip[hw_branches_addresses[rip].branch_false] = rip;
    }
    if(true_rip[rip] != 0) {
        hw_branches[true_rip[rip]].branch_true++;
        false_rip[hw_branches_addresses[true_rip[rip]].branch_false] = 0;
        true_rip[rip] = 0;
    }
    if(false_rip[rip] != 0) {
        hw_branches[false_rip[rip]].branch_false++;
        true_rip[hw_branches_addresses[false_rip[rip]].branch_true] = 0;
        false_rip[rip] = 0;
    }
    vp_rips[rip]++;
}

static void clean_call_pc(uint reg) {
    if(!recording){
        return;
    }
    dr_mcontext_t mcontext = {
        sizeof(mcontext),
        DR_MC_ALL,
    };
    void * drcontext = dr_get_current_drcontext();
    dr_get_mcontext(drcontext, &mcontext);
    reg_t pc = reg_get_value(reg, &mcontext);
    if(channel != "") {
        //dr_printf("PC: %llx START: %llx END: %llx\n", pc, start_address, end_address);
        if(pc < start_address || pc > end_address) { // && (pc < mod_start_address || pc > mod_end_address)){
            return;
        }
        //dr_mutex_lock(address_lock);
        pc = pc - start_address;
        //dr_mutex_unlock(address_lock);
    }
    
    if(pc < MAX_SW_PCS && sw_address[pc]) {
        if(sw_branches_addresses[pc].branch_true != 0 && sw_branches_addresses[pc].branch_false != 0) {
            true_pc[sw_branches_addresses[pc].branch_true] = pc;
            false_pc[sw_branches_addresses[pc].branch_false] = pc;
        }
        if(true_pc[pc] != 0) {
            sw_branches[true_pc[pc]].branch_true++;
            false_pc[sw_branches_addresses[true_pc[pc]].branch_false] = 0;
            true_pc[pc] = 0;
        }
        if(false_pc[pc] != 0) {
            sw_branches[false_pc[pc]].branch_false++;
            true_pc[sw_branches_addresses[false_pc[pc]].branch_true] = 0;
            false_pc[pc] = 0;
        }

        sw_pcs[pc]++;
    }

    /*if(channel != "" && pc < MAX_MOD_PCS && mod_address[pc]) {
        if(mod_branches_addresses[pc].branch_true != 0 && mod_branches_addresses[pc].branch_false != 0) {
            true_mod_pc[mod_branches_addresses[pc].branch_true] = pc;
            false_mod_pc[mod_branches_addresses[pc].branch_false] = pc;
        }
        if(true_mod_pc[pc] != 0) {
            mod_branches[true_mod_pc[pc]].branch_true++;
            false_mod_pc[mod_branches_addresses[true_mod_pc[pc]].branch_false] = 0;
            true_mod_pc[pc] = 0;
        }
        if(false_mod_pc[pc] != 0) {
            mod_branches[false_mod_pc[pc]].branch_false++;
            true_mod_pc[mod_branches_addresses[false_mod_pc[pc]].branch_true] = 0;
            false_mod_pc[pc] = 0;
        }

        mod_pcs[pc]++;
    }
    */
}