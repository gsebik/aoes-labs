#include "ws2812.h"

int main(void) {
    lab_board_init("rgb", false);
    ws2812_init();
    puts("commands: r=red g=green b=blue w=white o=off; low brightness=16/255");
    uint8_t r = 16, g = 0, b = 0;
    while (true) {
        int key = getchar_timeout_us(0);
        if (key == 'r') { r = 16; g = 0; b = 0; }
        if (key == 'g') { r = 0; g = 16; b = 0; }
        if (key == 'b') { r = 0; g = 0; b = 16; }
        if (key == 'w') { r = 16; g = 16; b = 16; }
        if (key == 'o') { r = 0; g = 0; b = 0; }
        ws2812_send_grb(g, r, b, true);
        ws2812_observation_t span = ws2812_last_observation();
        printf("rgb,r=%u,g=%u,b=%u,frame_cycles=%" PRIu32 "\n", r, g, b, span.cycles);
        sleep_ms(500);
    }
}
