/* AoES shared timing harness, adapted from src/es201/l0-dwt-demo/main.c.
 * GPIO call brackets, callback-entry periods and adc_read() brackets are
 * different observations. None is an interrupt-request-to-entry measurement.
 * EP-0172: GP16 user LED; GP26/ADC0 joystick; Gremlin UART0 console.
 * Collect one complete @@BEGIN ... @@END run. Output is outside each window.
 */
#include <inttypes.h>
#include <math.h>
#include <stdio.h>
#include "pico/stdlib.h"
#include "hardware/adc.h"
#include "hardware/clocks.h"
#include "hardware/structs/sio.h"
#include "timing.h"

#define SAMPLE_COUNT 256u
#define OUTPUT_PIN 16u
#define CALLBACK_PERIOD_US 1000
static uint32_t durations[SAMPLE_COUNT];
static volatile uint32_t callback_cycles[SAMPLE_COUNT + 1u];
static volatile uint32_t callback_count;
static volatile uint32_t callback_core;
static uint32_t clock_hz;
static uint32_t run_id;

static void emit_case(const char *name) {
    uint32_t minimum = durations[0], maximum = durations[0];
    uint64_t total = 0;
    for (uint i = 0; i < SAMPLE_COUNT; ++i) {
        uint32_t value = durations[i];
        if (value < minimum) minimum = value;
        if (value > maximum) maximum = value;
        total += value;
    }
    double mean = (double)total / SAMPLE_COUNT;
    double variance = 0;
    for (uint i = 0; i < SAMPLE_COUNT; ++i) {
        double difference = durations[i] - mean;
        variance += difference * difference;
    }
    printf("@@SUMMARY run=%" PRIu32 " case=%s n=%u min_cycles=%" PRIu32
           " mean_cycles=%.3f max_cycles=%" PRIu32 " sd_cycles=%.3f\n",
           run_id, name, SAMPLE_COUNT, minimum, mean, maximum,
           sqrt(variance / SAMPLE_COUNT));
    for (uint i = 0; i < SAMPLE_COUNT; ++i)
        printf("@@SAMPLE run=%" PRIu32 " case=%s index=%u cycles=%" PRIu32 "\n",
               run_id, name, i, durations[i]);
}

static void measure_gpio(void) {
    gpio_init(OUTPUT_PIN);
    gpio_set_dir(OUTPUT_PIN, GPIO_OUT);
    gpio_put(OUTPUT_PIN, 0);
    for (uint i = 0; i < SAMPLE_COUNT; ++i) {
        uint32_t start = timing_read_cycles();
        gpio_xor_mask(1u << OUTPUT_PIN);
        durations[i] = timing_read_cycles() - start;
    }
    emit_case("gpio_xor_mask");
    gpio_put(OUTPUT_PIN, 0);
    for (uint i = 0; i < SAMPLE_COUNT; ++i) {
        uint32_t start = timing_read_cycles();
        gpio_put(OUTPUT_PIN, (i + 1u) & 1u);
        durations[i] = timing_read_cycles() - start;
    }
    emit_case("gpio_put");
    gpio_put(OUTPUT_PIN, 0);
    for (uint i = 0; i < SAMPLE_COUNT; ++i) {
        uint32_t start = timing_read_cycles();
        sio_hw->gpio_togl = 1u << OUTPUT_PIN;
        durations[i] = timing_read_cycles() - start;
    }
    emit_case("sio_xor_write");
    gpio_put(OUTPUT_PIN, 0);
}

static bool timer_callback(struct repeating_timer *timer) {
    (void)timer;
    uint32_t count = callback_count;
    if (count < SAMPLE_COUNT + 1u) {
        callback_cycles[count] = timing_read_cycles();
        callback_core = get_core_num();
        callback_count = count + 1u;
    }
    return callback_count < SAMPLE_COUNT + 1u;
}

static bool measure_callback_period(void) {
    callback_count = 0;
    callback_core = UINT32_MAX;
    struct repeating_timer timer;
    if (!add_repeating_timer_us(-CALLBACK_PERIOD_US, timer_callback, NULL, &timer)) {
        printf("@@ABORT run=%" PRIu32 " reason=timer_setup\n", run_id);
        return false;
    }
    absolute_time_t timeout = make_timeout_time_ms(2000);
    while (callback_count < SAMPLE_COUNT + 1u && !time_reached(timeout))
        tight_loop_contents();
    cancel_repeating_timer(&timer);
    if (callback_count != SAMPLE_COUNT + 1u || callback_core != get_core_num()) {
        printf("@@ABORT run=%" PRIu32 " reason=timer_window_or_core\n", run_id);
        return false;
    }
    /* Full recorder is immutable. Same-core callback entries, not IRQ requests. */
    for (uint i = 0; i < SAMPLE_COUNT; ++i)
        durations[i] = callback_cycles[i + 1u] - callback_cycles[i];
    emit_case("timer_callback_period");
    return true;
}

static void measure_adc(void) {
    adc_init();
    adc_gpio_init(26);
    adc_select_input(0);
    adc_set_round_robin(0);
    adc_run(false);
    for (uint i = 0; i < SAMPLE_COUNT; ++i) {
        uint32_t start = timing_read_cycles();
        (void)adc_read();
        durations[i] = timing_read_cycles() - start;
    }
    emit_case("adc_read");
}

int main(void) {
    stdio_init_all();
    sleep_ms(2000);
    clock_hz = clock_get_hz(clk_sys);
    if (!timing_counter_init()) {
        printf("@@ERROR reason=dwt_counter_unavailable\n");
        for (;;) tight_loop_contents();
    }
    for (;;) {
        ++run_id;
        printf("@@BEGIN schema=aoes-timing-v1 run=%" PRIu32
               " clock_hz=%" PRIu32 " core=%u n=%u period_us=%u\n",
               run_id, clock_hz, get_core_num(), SAMPLE_COUNT, CALLBACK_PERIOD_US);
        for (uint i = 0; i < SAMPLE_COUNT; ++i) {
            uint32_t start = timing_read_cycles();
            durations[i] = timing_read_cycles() - start;
        }
        emit_case("empty_bracket");
        measure_gpio();
        if (measure_callback_period()) {
            measure_adc();
            printf("@@END run=%" PRIu32 "\n", run_id);
        }
        /* Repeat so a monitor opened after reset can retain a complete run. */
        sleep_ms(5000);
    }
}
