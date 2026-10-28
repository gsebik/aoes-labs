#include "board.h"
#include "race.h"
#include "hardware/irq.h"

static volatile uint32_t pending_events;
static volatile bool injected;
static bool injection_timed_out;

static void injected_isr(void) {
    pending_events |= 2u;
    injected = true;
}

static bool wait_for_injection(void) {
    uint64_t deadline = time_us_64() + 100000;
    while (!injected) {
        if (time_us_64() >= deadline) return false;
        tight_loop_contents();
    }
    return true;
}

// Test scaffolding: request one extra event at the same point on every run.
// If the caller masked interrupts, leave the IRQ pending and return immediately.
// Otherwise wait for it to run, so the unsafe read/clear loses it reliably.
static void inject_between_accesses(void) {
    uint32_t state = save_and_disable_interrupts();
    irq_set_pending(SPARE_IRQ_0);
    restore_interrupts(state);
    if ((state & 1u) == 0 && !wait_for_injection()) injection_timed_out = true;
}

// [S] Task 3: repair this shared-word transfer. Keep the injected event in place.
// On entry bit 0 represents an event already waiting for main. A second event
// sets bit 1 during the transfer; it must remain pending for the next transfer.
static uint32_t take_pending_events(void) {
    // TODO S1: save the current interrupt state and mask interrupts here.
    uint32_t copied = pending_events;
    inject_between_accesses();
    pending_events = 0u;
    // TODO S2: restore the saved interrupt state here.
    return copied;
}

// [R] A deterministic interleaving, not a measurement of natural failure rate.
void lab_race_demo(void) {
    uint32_t entry_state = save_and_disable_interrupts();
    restore_interrupts(entry_state);
    if (entry_state & 1u) {
        puts("race,INVALID,reason=interrupts_masked_on_entry");
        return;
    }
    irq_set_exclusive_handler(SPARE_IRQ_0, injected_isr);
    irq_clear(SPARE_IRQ_0);
    irq_set_enabled(SPARE_IRQ_0, true);
    pending_events = 1u;
    injected = false;
    injection_timed_out = false;
    uint32_t copied = take_pending_events();

    // Recover from a missing restoration before waiting, printing or returning.
    uint32_t exit_state = save_and_disable_interrupts();
    restore_interrupts(entry_state);
    bool completed = wait_for_injection();
    irq_set_enabled(SPARE_IRQ_0, false);
    irq_clear(SPARE_IRQ_0);
    irq_remove_handler(SPARE_IRQ_0, injected_isr);
    if (exit_state != entry_state) {
        puts("race,INVALID,reason=interrupt_state_not_restored");
    } else if (!completed || injection_timed_out) {
        puts("race,INVALID,reason=injected_irq_timeout");
    } else {
        printf("race,copied=%" PRIu32 ",remaining=%" PRIu32 "\n",
               copied, pending_events);
    }
}
