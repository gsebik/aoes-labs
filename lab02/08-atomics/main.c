#include "board.h"
#include <stdatomic.h>
#include "hardware/irq.h"

static volatile uint32_t plain_counter;
static _Atomic uint32_t atomic_counter = 0;
static volatile bool injected;
static volatile bool use_atomic;

__attribute__((noinline)) void increment_relaxed(void) {
    atomic_fetch_add_explicit(&atomic_counter, 1, memory_order_relaxed);
}

__attribute__((noinline)) void increment_seq_cst(void) {
    atomic_fetch_add_explicit(&atomic_counter, 1, memory_order_seq_cst);
}

static void injected_isr(void) {
    if (use_atomic) increment_relaxed();
    else ++plain_counter;
    injected = true;
}

static void wait_for_irq(void) {
    while (!injected) tight_loop_contents();
}

int main(void) {
    lab_board_init("atomics", false);
    bool lock_free = atomic_is_lock_free(&atomic_counter);
    printf("atomic object_bytes=%u lock_free=%u\n", (uint)sizeof atomic_counter, lock_free);
    if (!lock_free) panic("Atomic operation is not suitable for this ISR exercise");
    irq_set_exclusive_handler(SPARE_IRQ_0, injected_isr);
    irq_set_enabled(SPARE_IRQ_0, true);
    while (true) {
        use_atomic = false;
        plain_counter = 0;
        injected = false;
        uint32_t stale = plain_counter;
        irq_set_pending(SPARE_IRQ_0);
        wait_for_irq();
        plain_counter = stale + 1u;
        printf("counter,volatile,expected=2,observed=%" PRIu32 "\n", plain_counter);

        plain_counter = 0;
        injected = false;
        uint32_t saved = save_and_disable_interrupts();
        irq_set_pending(SPARE_IRQ_0);
        ++plain_counter;
        restore_interrupts(saved);
        wait_for_irq();
        printf("counter,critical,expected=2,observed=%" PRIu32 "\n", plain_counter);

        use_atomic = true;
        atomic_store_explicit(&atomic_counter, 0, memory_order_relaxed);
        injected = false;
        irq_set_pending(SPARE_IRQ_0);
        increment_relaxed();
        wait_for_irq();
        printf("counter,atomic,expected=2,observed=%" PRIu32 "\n",
               atomic_load_explicit(&atomic_counter, memory_order_relaxed));
        increment_seq_cst(); // Keep both functions in the linked disassembly.
        printf("counter,seq_cst_added,expected=3,observed=%" PRIu32 "\n",
               atomic_load_explicit(&atomic_counter, memory_order_relaxed));
        sleep_ms(2000);
    }
}
