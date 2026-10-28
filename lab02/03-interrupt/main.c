#include <stdio.h>
#include <stdint.h>
#include "pico/stdlib.h"

static volatile unsigned timer_count;

// Called by the SDK timer handler in interrupt context.
static bool heartbeat_cb(repeating_timer_t *timer) {
    (void)timer;
    gpio_xor_mask(1u << 17);
    ++timer_count;
    return true;
}

int main(void) {
    stdio_init_all();
    gpio_init(16);
    gpio_set_dir(16, GPIO_OUT);
    gpio_put(16, false);
    gpio_init(17);
    gpio_set_dir(17, GPIO_OUT);
    gpio_put(17, false);

    const unsigned period_ms = 500;
    const unsigned work_ms = 20;
    const uint64_t period_us = (uint64_t)period_ms * 1000;
    repeating_timer_t timer;
    // TODO I1: register heartbeat_cb with a negative period_ms interval here.

    unsigned count = 0;
    uint64_t start_us = time_us_64();
    uint64_t next_us = start_us + period_us;
    puts("start,interrupt");

    while (true) {
        if (false) { // TODO A1: copy your deadline comparison from 02-absolute.
            gpio_xor_mask(1u << 16);
            uint64_t elapsed_us = time_us_64() - start_us;
            ++count;
            printf("led,interrupt,%u,%u,%u,%llu,%u\n",
                   period_ms, work_ms, count,
                   (unsigned long long)elapsed_us, timer_count);

            // TODO A2: copy your next_us increment from 02-absolute.
            busy_wait_ms(work_ms);
        }
    }
}
