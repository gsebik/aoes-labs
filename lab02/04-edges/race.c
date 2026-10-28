#include "board.h"
#include "race.h"
#include "hardware/irq.h"

static volatile uint32_t pending_events;
static volatile bool injected;

static void injected_isr(void) {
    pending_events |= 2u;
    injected = true;
}

static void wait_for_injection(void) {
    while (!injected) tight_loop_contents();
}

// [R] A controlled interleaving, not a claim about natural failure frequency.
void lab_race_demo(void) {
    irq_set_exclusive_handler(SPARE_IRQ_0, injected_isr);
    irq_set_enabled(SPARE_IRQ_0, true);
    pending_events = 1u;
    injected = false;
    uint32_t copied = pending_events;
    irq_set_pending(SPARE_IRQ_0);
    wait_for_injection(); // Force an IRQ between the foreground read and clear.
    pending_events = 0u;
    printf("race,bad,copied=%" PRIu32 ",remaining=%" PRIu32
           ",expected_remaining=2\n", copied, pending_events);

    pending_events = 1u;
    injected = false;
    uint32_t state = save_and_disable_interrupts();
    copied = pending_events;
    irq_set_pending(SPARE_IRQ_0); // Pending, but cannot split the protected transfer.
    pending_events = 0u;
    restore_interrupts(state);
    wait_for_injection(); // Always outside the critical section.
    printf("race,protected,copied=%" PRIu32 ",remaining=%" PRIu32
           ",expected_remaining=2\n", copied, pending_events);
    irq_set_enabled(SPARE_IRQ_0, false);
    irq_remove_handler(SPARE_IRQ_0, injected_isr);
}
