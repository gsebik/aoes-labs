// Optional ISR-construction extension: record one button edge from the GPIO interrupt into the ring.
//
// The ISR owns head; main owns tail. A slot between tail and head belongs to
// main until main advances tail. Keep this function short: no printing.
static void edge_isr(uint pin, uint32_t events) {
    if (pin != K1_PIN && pin != K2_PIN) return;
    uint32_t both = GPIO_IRQ_EDGE_RISE | GPIO_IRQ_EDGE_FALL;
    // Both flags latched: two edges came before this ISR ran, and their order is lost.
    if ((events & both) == both) { ++ambiguous; return; }
    uint32_t next = (head + 1u) & (RING_SIZE - 1u);
#error "TODO E1: if next == tail the ring is full: count the edge in dropped and return"
#error "TODO E2: fill ring[head] (t_us = time_us_64(), pin, level = 1 for a rising edge), then publish it with head = next, last"
#error "TODO E3: toggle IRQ_MARKER_PIN (GP16) with one SIO write so the analyzer sees every recorded edge"
}
