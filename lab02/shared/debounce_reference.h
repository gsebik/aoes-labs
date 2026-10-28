// Supplied debounce rule for the _recovery targets. Task 4 asks you to write
// filter_edge in debounce_exercise.h; a recovery run does not complete Task 4.
#define DEBOUNCE_US 5000u

// Replay observed quiet gaps even if main drained the records late.
static void filter_edge(const edge_t *e) {
    button_t *b = &buttons[e->pin - K1_PIN];
    if (b->pending && e->t_us - b->changed_us >= DEBOUNCE_US) {
        accept_level(b, e->pin, b->changed_us + DEBOUNCE_US);
    }
    b->candidate = e->level;
    b->changed_us = e->t_us;
    b->pending = true;
}

