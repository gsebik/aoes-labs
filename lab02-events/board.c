#include "board.h"

void lab_board_init(const char *experiment, bool buttons) {
    stdio_init_all();
    gpio_init(IRQ_MARKER_PIN);
    gpio_set_dir(IRQ_MARKER_PIN, GPIO_OUT);
    gpio_init(FRAME_MARKER_PIN);
    gpio_set_dir(FRAME_MARKER_PIN, GPIO_OUT);
    if (buttons) {
        for (uint pin = K1_PIN; pin <= K2_PIN; ++pin) {
            gpio_init(pin);
            gpio_set_dir(pin, GPIO_IN);
            gpio_disable_pulls(pin); // The EP-0172 supplies external pull-ups.
        }
    }
    if (!timing_counter_init()) panic("DWT cycle counter is unavailable");
    sleep_ms(1500); // Attach the Gremlin UART monitor after programming.
    printf("lab02 experiment=%s clock_hz=%" PRIu32 " gcc=%s\n",
           experiment, clock_get_hz(clk_sys), __VERSION__);
#ifdef LAB02_SENDER_NAME
    printf("sender=%s\n", LAB02_SENDER_NAME);
#endif
}
