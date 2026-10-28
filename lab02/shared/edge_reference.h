// Supplied recorder for the core lab: ISR owns head, main owns tail.
// The optional _isr_exercise target uses edge_exercise.h instead.
static void edge_isr(uint pin, uint32_t events) {
    if (pin != K1_PIN && pin != K2_PIN) return;
    uint32_t both = GPIO_IRQ_EDGE_RISE | GPIO_IRQ_EDGE_FALL;
    // Both flags latched: two edges came before this ISR ran, and their order is lost.
    if ((events & both) == both) { ++ambiguous; return; }
    uint32_t next = (head + 1u) & (RING_SIZE - 1u);
    if (next == tail) { ++dropped; return; }
    ring[head].t_us = time_us_64();
    ring[head].pin = pin;
    ring[head].level = (events & GPIO_IRQ_EDGE_RISE) != 0;
    head = next; // Publish last. No overwrite until main releases the slot.
    gpio_xor_mask(1u << IRQ_MARKER_PIN); // One SIO write: the analyzer sees the record.
}
