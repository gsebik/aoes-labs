#include "board.h"
#include "race.h"
#ifdef LAB_WITH_RGB
#include "led_app.h"
#endif

#define RING_SIZE 256u
_Static_assert((RING_SIZE & (RING_SIZE - 1u)) == 0 && RING_SIZE > 1,
               "RING_SIZE must be a power of two greater than one");
// Initial trial setting only. Task 4 replaces it using the recorded edge clusters.
#define DEBOUNCE_US 5000u

typedef struct { uint64_t t_us; uint8_t pin, level; } edge_t;
static volatile edge_t ring[RING_SIZE];
static volatile uint32_t head, tail, dropped, ambiguous;
typedef struct {
    uint64_t changed_us;
    bool candidate, stable, pending;
    uint32_t presses;
} button_t;
static button_t buttons[2]; // Main-owned filter state.

// [1] GPIO callback: SDK dispatch has acknowledged the delivered edge flags.
static void edge_isr(uint pin, uint32_t events) {
    if (pin != K1_PIN && pin != K2_PIN) return;
    uint32_t both = GPIO_IRQ_EDGE_RISE | GPIO_IRQ_EDGE_FALL;
    if ((events & both) == both) { ++ambiguous; return; }
    uint32_t next = (head + 1u) & (RING_SIZE - 1u);
    if (next == tail) { ++dropped; return; }
    ring[head].t_us = time_us_64();
    ring[head].pin = pin;
    ring[head].level = (events & GPIO_IRQ_EDGE_RISE) != 0;
    head = next; // Publish last. No overwrite until main releases the slot.
}

static bool pop_edge(edge_t *e) {
    if (tail == head) return false;
    e->t_us = ring[tail].t_us;
    e->pin = ring[tail].pin;
    e->level = ring[tail].level;
    tail = (tail + 1u) & (RING_SIZE - 1u); // Release after copying.
    return true;
}

static void accept_level(button_t *b, uint pin, uint64_t eligible_us) {
    b->pending = false;
    if (b->stable == b->candidate) return;
    b->stable = b->candidate;
    if (!b->stable) ++b->presses;
    uint64_t handled = time_us_64();
    printf("button,eligible_us=%" PRIu64 ",handled_us=%" PRIu64
           ",pin=%u,pressed=%u\n", eligible_us, handled, pin, !b->stable);
#ifdef LAB_WITH_RGB
    if (!b->stable) led_app_press(pin, handled);
#endif
}

// [2] Replay observed quiet gaps even if main drained the records late.
static void filter_edge(const edge_t *e) {
    button_t *b = &buttons[e->pin - K1_PIN];
    if (b->pending && e->t_us - b->changed_us >= DEBOUNCE_US) {
        accept_level(b, e->pin, b->changed_us + DEBOUNCE_US);
    }
    b->candidate = e->level;
    b->changed_us = e->t_us;
    b->pending = true;
}

int main(void) {
    lab_board_init("events", true);
    for (uint i = 0; i < 2; ++i) {
        buttons[i].stable = buttons[i].candidate = gpio_get(K1_PIN + i);
    }
#ifdef LAB_WITH_RGB
    led_app_init();
    puts("controller: K1=next colour K2=fade/steady; b=blocking fade comparison");
#endif
    puts("edge,t_us,pin,level,delta_us; status,t_us,k1_presses,k2_presses,dropped,ambiguous");
    puts("x=controlled read/clear race; no UART printing in the GPIO ISR");
    gpio_set_irq_enabled_with_callback(K1_PIN,
        GPIO_IRQ_EDGE_RISE | GPIO_IRQ_EDGE_FALL, true, edge_isr);
    gpio_set_irq_enabled(K2_PIN, GPIO_IRQ_EDGE_RISE | GPIO_IRQ_EDGE_FALL, true);
    uint64_t previous[2] = {0, 0};
    uint64_t next_status = time_us_64() + 1000000;
    while (true) {
        edge_t edge;
        // [3] The queue carries raw history; filters and colour state stay in main.
        while (pop_edge(&edge)) {
            uint i = edge.pin - K1_PIN;
            uint64_t delta = previous[i] ? edge.t_us - previous[i] : 0;
            previous[i] = edge.t_us;
            printf("edge,%" PRIu64 ",%u,%u,%" PRIu64 "\n",
                   edge.t_us, edge.pin, edge.level, delta);
            filter_edge(&edge);
        }
        // Confirm only a history already drained by main. Keep the sample short;
        // printing and application updates happen after restoring interrupts.
        uint32_t snapshot_state = save_and_disable_interrupts();
        uint64_t now = time_us_64();
        bool caught_up = head == tail;
        uint32_t levels = gpio_get_all();
        restore_interrupts(snapshot_state);
        for (uint i = 0; i < 2; ++i) {
            button_t *b = &buttons[i];
            bool level = (levels & (1u << (K1_PIN + i))) != 0;
            if (caught_up && b->pending && now - b->changed_us >= DEBOUNCE_US
                    && level == b->candidate) {
                accept_level(b, K1_PIN + i, b->changed_us + DEBOUNCE_US);
            }
        }
#ifdef LAB_WITH_RGB
        led_app_step(now);
#endif
        int key = getchar_timeout_us(0);
        if (key == 'x') lab_race_demo();
#ifdef LAB_WITH_RGB
        if (key == 'b') {
            puts("blocking fade begins; raw edges may queue while main waits");
            led_app_blocking_fade();
            puts("blocking fade ends");
        }
#endif
        now = time_us_64();
        if (now >= next_status) {
            uint32_t saved = save_and_disable_interrupts();
            uint32_t lost = dropped, merged = ambiguous;
            restore_interrupts(saved);
            printf("status,%" PRIu64 ",%" PRIu32 ",%" PRIu32 ",%" PRIu32
                   ",%" PRIu32 "\n", now, buttons[0].presses,
                   buttons[1].presses, lost, merged);
            next_status = now + 1000000;
        }
        sleep_us(100);
    }
}
