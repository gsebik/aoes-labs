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
    const uint64_t period_us = (uint64_t)period_ms * 1000;
    unsigned count = 0;
    uint64_t start_us = time_us_64();
    uint64_t next_us = start_us + period_us;

    puts("start,absolute");

    while (true) {
        if (false) { // A1: replace false with the deadline comparison.
            gpio_xor_mask(1u << 16);
            uint64_t elapsed_us = time_us_64() - start_us;
            ++count;
            printf("led,absolute,%u,%u,%u,%llu\n",
                   period_ms, work_ms, count, (unsigned long long)elapsed_us);

            // A2: advance next_us by one period_us here.
            busy_wait_ms(work_ms);
        }
    }
}
