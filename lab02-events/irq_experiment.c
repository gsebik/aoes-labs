#include "ws2812.h"
#include "hardware/irq.h"
#include "hardware/timer.h"

static uint slow_alarm, fast_alarm;
static volatile bool slow_done, fast_done;
static volatile uint64_t fast_entry_us;
static char experiment = 'f';

// [H] Timestamp is after SDK IRQ dispatch. This measures service lateness.
static void fast_cb(uint alarm) {
    (void)alarm;
    gpio_put(IRQ_MARKER_PIN, true);
    fast_entry_us = time_us_64();
    gpio_put(IRQ_MARKER_PIN, false);
    fast_done = true;
}

// [L] Candidate design: do a complete blocking LED update from an alarm IRQ.
static void slow_cb(uint alarm) {
    (void)alarm;
    ws2812_send_grb(0x05, 0x0a, 0x05, experiment == 'm');
    slow_done = true;
}

int main(void) {
    lab_board_init("irq", false);
    ws2812_init();
    slow_alarm = hardware_alarm_claim_unused(true);
    fast_alarm = hardware_alarm_claim_unused(true);
    hardware_alarm_set_callback(slow_alarm, slow_cb);
    hardware_alarm_set_callback(fast_alarm, fast_cb);
    irq_set_priority(hardware_alarm_get_irq_num(slow_alarm), 0xc0);
    puts("f=foreground, e=equal IRQ priority, u=urgent IRQ, m=masked frame");
    while (true) {
        int key = getchar_timeout_us(0);
        if (key == 'f' || key == 'e' || key == 'u' || key == 'm') {
            experiment = (char)key;
        }
        hardware_alarm_cancel(slow_alarm);
        hardware_alarm_cancel(fast_alarm);
        slow_done = fast_done = false;
        fast_entry_us = 0;
        irq_set_priority(hardware_alarm_get_irq_num(fast_alarm),
                         experiment == 'e' ? 0xc0 : 0x40);
        printf("case=%c low_irq=%u low_priority=%u fast_irq=%u fast_priority=%u\n",
               experiment, hardware_alarm_get_irq_num(slow_alarm),
               irq_get_priority(hardware_alarm_get_irq_num(slow_alarm)),
               hardware_alarm_get_irq_num(fast_alarm),
               irq_get_priority(hardware_alarm_get_irq_num(fast_alarm)));
        uint64_t start = time_us_64() + 500;
        uint64_t requested = start + 10;
        bool missed = hardware_alarm_set_target(fast_alarm, from_us_since_boot(requested));
        if (experiment == 'f') {
            busy_wait_until(from_us_since_boot(start));
            ws2812_send_grb(0x05, 0x0a, 0x05, false);
            slow_done = true;
        } else {
            missed |= hardware_alarm_set_target(slow_alarm, from_us_since_boot(start));
        }
        uint64_t timeout = start + 50000;
        while ((!slow_done || !fast_done) && time_us_64() < timeout) {
            tight_loop_contents();
        }
        uint32_t saved = save_and_disable_interrupts();
        uint64_t entry = fast_entry_us;
        bool complete = slow_done && fast_done;
        restore_interrupts(saved);
        ws2812_observation_t frame = ws2812_last_observation();
        if (missed || !complete) {
            printf("irq,case=%c,INVALID missed=%u complete=%u\n",
                   experiment, missed, complete);
        } else {
            printf("irq,case=%c,requested_us=%" PRIu64 ",entry_us=%" PRIu64
                   ",service_late_us=%" PRId64 ",bracket_start_us=%" PRIu64
                   ",bracket_end_us=%" PRIu64 ",frame_cycles=%" PRIu32 "\n",
                   experiment, requested, entry, (int64_t)(entry - requested),
                   frame.start_us, frame.end_us, frame.cycles);
        }
        sleep_ms(1000);
    }
}
