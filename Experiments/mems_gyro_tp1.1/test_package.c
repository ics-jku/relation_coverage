#include "test_package.h"
#include "irq.h"
#include "mems_gyro.h"
#include "stdbool.h"

void testpackage_init() {
    init_mems_gyro();
}

void testpackage_execute() {
    test_no_axis();
//    test_y_axis();
//    test_z_axis();
//    test_ena_all_axis();
//    test_dis_all_axis();
//     // test_filter_0();
//     // test_filter_1();
//     // test_filter_2();
//     // test_filter_3();
//     // test_filter_10();

//     // test_scaler_0();
//     // test_scaler_1();
//     // test_scaler_5();
//     // test_scaler_1000();

}

void test_no_axis() {
    enable_interrupt(3);
    enable_axes(false, false, false);
    get_y_axis();
    get_z_axis();
    get_z_axis();
    print_mems_gyro_data();
    disable_interrupt();
}

// void test_y_axis() {
//      enable_axes(false, true, false);
//      print_mems_gyro_data();
// }

// void test_z_axis() {
//      enable_axes(false, false, true);
//      print_mems_gyro_data();
// }

// void test_ena_all_axis() {
//      enable_axes(true, true, true);
//      print_mems_gyro_data();
// }

// void test_dis_all_axis() {
//     enable_axes(false, false, false);
//     print_mems_gyro_data();
// }
// void test_filter_1() {
//     set_sensor_scaler(5);
//     set_sensor_filter(1);

//     dump_sensor_data();
// }

// void test_filter_2() {
//     set_sensor_scaler(5);
//     set_sensor_filter(2);

//     dump_sensor_data();
// }

// void test_filter_3() {
//     set_sensor_scaler(5);
//     set_sensor_filter(3);

//     dump_sensor_data();
// }

// void test_filter_10() {
//     set_sensor_scaler(5);
//     set_sensor_filter(10);

//     dump_sensor_data();
// }

// void test_scaler_0() {
//     set_sensor_scaler(0);
//     set_sensor_filter(2);

//     dump_sensor_data();
// }

// void test_scaler_1() {
//     set_sensor_scaler(1);
//     set_sensor_filter(2);

//     dump_sensor_data();
// }

// void test_scaler_5() {
//     set_sensor_scaler(5);
//     set_sensor_filter(2);

//     dump_sensor_data();
// }

// void test_scaler_1000() {
//     set_sensor_scaler(1000);
//     set_sensor_filter(2);

//     dump_sensor_data();
// }

