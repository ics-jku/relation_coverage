#include "test_package.h"
#include "watchdog.h"

int main() {
    watchdog_init();
    testpackage_init();
    testpackage_execute();

    return 0;
}