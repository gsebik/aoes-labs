#include "led_app.h"
#include "ws2812.h"

#define STEP_US 62500u // 32 steps form a two-second up/down cycle.
#define PEAK 16u

typedef enum { STEADY, RAMP_UP, RAMP_DOWN } colour_state_t;
// [A] Main owns all application state. No ISR reads or writes these fields.
static colour_state_t state;
static uint colour;
static uint8_t brightness;
static uint64_t fade_epoch, next_step;
static bool dirty;

static void send_colour(void) {
    uint8_t r = 0, g = 0, b = 0;
    if (colour == 0 || colour == 3) r = brightness;
    if (colour == 1 || colour == 3) g = brightness;
    if (colour == 2 || colour == 3) b = brightness;
    ws2812_send_grb(g, r, b, true);
}

void led_app_init(void) {
    ws2812_init();
    state = STEADY;
    colour = 0;
    brightness = PEAK;
    dirty = true;
}

void led_app_press(uint pin, uint64_t now) {
    if (pin == K1_PIN) {
        colour = (colour + 1u) % 4u; // Red, green, blue, white.
    } else if (pin == K2_PIN) {
        if (state == STEADY) {
            state = RAMP_UP;
            brightness = 0;
            fade_epoch = now;
            next_step = now;
        } else {
            // TODO C1: implement the requested K2 stop policy.
            state = STEADY;
            brightness = PEAK;
        }
    }
    dirty = true;
    printf("app,colour=%u,state=%u,brightness=%u\n", colour, state, brightness);
}

// [S] One bounded update, with time anchored to the fade's original epoch.
void led_app_step(uint64_t now) {
    if (state != STEADY && now >= next_step) {
        uint32_t phase = ((now - fade_epoch) / STEP_US) % (2u * PEAK);
        brightness = phase <= PEAK ? phase : 2u * PEAK - phase;
        state = phase < PEAK ? RAMP_UP : RAMP_DOWN;
        next_step = fade_epoch + ((now - fade_epoch) / STEP_US + 1u) * STEP_US;
        dirty = true;
    }
    if (dirty) {
        send_colour();
        dirty = false;
    }
}

// [B] Controlled comparison: a real visual transition, but main cannot drain inputs.
void led_app_blocking_fade(void) {
    for (uint phase = 0; phase < 2u * PEAK; ++phase) {
        brightness = phase <= PEAK ? phase : 2u * PEAK - phase;
        send_colour();
        sleep_us(STEP_US);
    }
    brightness = PEAK;
    dirty = true;
}
