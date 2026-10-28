// Task 4: turn the raw edge stream into presses and releases.
//
// main calls filter_edge for every recorded edge, in order, with its ISR
// timestamp. accept_level() reports a new stable level (a press or a release).
// The main loop also accepts a pending candidate once the input has been quiet
// for DEBOUNCE_US with nothing left in the ring.

// TODO D2: replace 0 with the quiet interval you chose from your Task 3 data.
#define DEBOUNCE_US 0u

static void filter_edge(const edge_t *e) {
    button_t *b = &buttons[e->pin - K1_PIN];
    // TODO D1: this placeholder accepts every edge as a new level: no debouncing.
    // Replace it with a quiet-window rule. Keep the newest level as the pending
    // candidate (candidate, changed_us, pending). Before replacing a pending
    // candidate, accept it if it stayed unchanged for at least DEBOUNCE_US,
    // reporting eligible_us = changed_us + DEBOUNCE_US.
    b->candidate = e->level;
    b->changed_us = e->t_us;
    accept_level(b, e->pin, e->t_us);
}
