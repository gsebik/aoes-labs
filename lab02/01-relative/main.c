#include <stdio.h>
#include <stdint.h>
#include "pico/stdlib.h"

int main(void) {
    stdio_init_all();
    gpio_init(16);
    gpio_set_dir(16, GPIO_OUT);
    gpio_put(16, false);

    const unsigned period_ms = 500;
    const unsigned work_ms = 0;
    unsigned count = 0;
    uint64_t start_us = time_us_64();

    puts("start,relative");

    while (true) {
        // R1: wait period_ms milliseconds here.

        gpio_xor_mask(1u << 16);
        uint64_t elapsed_us = time_us_64() - start_us;
        ++count;
        printf("led,relative,%u,%u,%u,%llu\n",
               period_ms, work_ms, count, (unsigned long long)elapsed_us);
        busy_wait_ms(work_ms);
    }
}
