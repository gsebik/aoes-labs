#pragma once
#include "board.h"
#include "hardware/structs/sio.h"

// Design targets for the classical WS2812B timing table. These are not bench data.
// Verify the fitted LED's specification and the actual pin waveform before release.
#define WS2812_T0H_NS 400u
#define WS2812_T1H_NS 800u
#define WS2812_BIT_NS 1250u
#define WS2812_RESET_US 400u

typedef struct {
    uint64_t start_us;
    uint64_t end_us;
    uint32_t cycles;
} ws2812_observation_t;

void ws2812_init(void);
void ws2812_send_grb(uint8_t green, uint8_t red, uint8_t blue, bool mask_irqs);
ws2812_observation_t ws2812_last_observation(void);

// The sender body is included in the recovery and exercise translation units.
// These helpers are inlined into its SRAM code; they do not run a flash loop.
static inline __attribute__((always_inline)) void ws2812_wait_from(
        uint32_t start, uint32_t duration) {
    while ((uint32_t)(timing_read_cycles() - start) < duration) {
        __asm volatile("nop");
    }
}
