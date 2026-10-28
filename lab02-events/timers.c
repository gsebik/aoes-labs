#include "board.h"
#include "timing_config.h"

static volatile uint32_t irq_count;
static volatile uint64_t irq_last_us;

#if LAB02_TIMING_MODE == LAB02_MODE_RELATIVE
// [T1] One relative wait. The caller changes GP16 afterwards.
static void relative_wait(void) {
    // Replace the #error with one SDK call. sleep_ms accepts milliseconds;
    // HALF_PERIOD_MS is the requested interval. See Task 1, step 1.
#error "TODO T1: implement relative_wait with the supplied millisecond interval"
}
#elif LAB02_TIMING_MODE == LAB02_MODE_ABSOLUTE
// [T2] Compare microsecond timestamps; equality must count as due.
static bool target_reached(uint64_t now, uint64_t deadline) {
    // Replace the #error with a return expression using these two arguments.
#error "TODO T2: return whether now has reached deadline"
}

// [T3] Advance the old target, not the time when main finally reaches this call.
static uint64_t advance_target(uint64_t deadline) {
    // Replace the #error with a return expression using HALF_PERIOD_US.
    // Do not read the clock here. See Task 1, step 3.
#error "TODO T3: advance the previous deadline by one interval"
}
#endif

#if LAB02_ENABLE_TIMER_CALLBACK
// [T4 / 1] Called by the SDK alarm-pool IRQ on Core 0, not by the main loop.
static bool heartbeat_cb(repeating_timer_t *timer) {
    (void)timer;
    // Replace the #error with one GPIO XOR call for FRAME_MARKER_PIN (GP17).
    // Keep the timestamp, count and return: they support the measurements.
#error "TODO T4: change the GP17 output once per callback"
    irq_last_us = time_us_64();
    ++irq_count;
    return true;
}

// [T5] Register the callback once per measurement window.
static void start_heartbeat(repeating_timer_t *timer) {
    // Template: replace the signed-interval placeholder and use this checked call.
    // if (!add_repeating_timer_ms(/* signed interval */, heartbeat_cb, NULL, timer)) {
    //     panic("Cannot allocate repeating timer");
    // }
    // Negative intervals anchor successive targets to the previous target.
    // HALF_PERIOD_MS is positive. See Task 2, "Register the callback".
#error "TODO T5: register heartbeat_cb with a negative millisecond interval"
}
#endif

#if LAB02_TIMING_MODE == LAB02_MODE_CPU_WORK
static void burn_iterations(void) {
    for (volatile uint32_t i = 0; i < BUSY_ITERATIONS; ++i) {
        __asm volatile("nop");
    }
}
#endif

int main(void) {
    lab_board_init("timers", false);
    puts("Edit timing_config.h, rebuild and flash to change the experiment.");
    puts("Monitor: n then Enter starts a fresh window; it changes no settings.");
#if LAB02_TIMING_MODE == LAB02_MODE_RELATIVE
    const char mode = 'r';
#elif LAB02_TIMING_MODE == LAB02_MODE_ABSOLUTE
    const char mode = 'a';
#else
    const char mode = 'b';
#endif
    const uint32_t work_us = mode == 'b' ? 0 : LAB02_FOREGROUND_WORK_US;
    while (true) {
        uint32_t count = 0;
        uint64_t work_elapsed_us = 0;
        irq_count = 0;
        irq_last_us = 0;
        uint64_t epoch = time_us_64();
        uint64_t last = epoch;
#if LAB02_TIMING_MODE == LAB02_MODE_ABSOLUTE
        uint64_t deadline = epoch + HALF_PERIOD_US;
#endif
        uint64_t report = epoch + 1000000;
#if LAB02_ENABLE_TIMER_CALLBACK
        repeating_timer_t timer;
        start_heartbeat(&timer);
#endif
        printf("window mode=%c half_period_us=%" PRIu64 " busy_iterations=%u work_us=%" PRIu32
               " callback_enabled=%d\n", mode, HALF_PERIOD_US, BUSY_ITERATIONS,
               work_us, LAB02_ENABLE_TIMER_CALLBACK);
        bool restart = false;
        while (!restart) {
            // [2] Each foreground strategy uses the same supplied recorder.
            bool toggle = true;
#if LAB02_TIMING_MODE == LAB02_MODE_RELATIVE
            relative_wait();
#elif LAB02_TIMING_MODE == LAB02_MODE_ABSOLUTE
            toggle = target_reached(time_us_64(), deadline);
#else
            burn_iterations();
#endif
            if (toggle) {
                gpio_xor_mask(1u << IRQ_MARKER_PIN); // GP16: foreground output.
                last = time_us_64();
                ++count;
#if LAB02_TIMING_MODE == LAB02_MODE_ABSOLUTE
                deadline = advance_target(deadline);
#endif
                // [W] Same work after each relative/absolute toggle. This
                // interruptible elapsed busy interval includes preemption;
                // it is not a calibrated CPU-demand or WCET bound.
                if (work_us) {
                    uint64_t start = time_us_64();
                    busy_wait_us(work_us);
                    work_elapsed_us = time_us_64() - start;
                }
            }
            if (time_us_64() >= report) {
                // [3] Copy the 32-bit count and 64-bit timestamp consistently.
                uint32_t state = save_and_disable_interrupts();
                uint32_t n = irq_count;
                uint64_t stamp = irq_last_us;
                restore_interrupts(state);
                int64_t phase = (int64_t)(last - epoch) - count * (int64_t)HALF_PERIOD_US;
                int64_t irq_phase = n ? (int64_t)(stamp - epoch)
                                       - n * (int64_t)HALF_PERIOD_US : 0;
                printf("timing,mode=%c,elapsed_us=%" PRIu64 ",main_count=%" PRIu32
                       ",main_phase_us=%" PRId64 ",irq_count=%" PRIu32
                       ",irq_phase_us=%" PRId64 ",work_us=%" PRIu32
                       ",work_elapsed_us=%" PRIu64 "\n", mode, time_us_64() - epoch,
                       count, phase, n, irq_phase, work_us, work_elapsed_us);
                report = time_us_64() + 1000000;
            }
            restart = getchar_timeout_us(0) == 'n';
            tight_loop_contents();
        }
#if LAB02_ENABLE_TIMER_CALLBACK
        cancel_repeating_timer(&timer);
#endif
    }
}
