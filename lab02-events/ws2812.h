#pragma once
#include "board.h"
#include "hardware/structs/sio.h"

// CPU wait thresholds for the reference 150 MHz / O2 SRAM sender.
// GPIO stores and loop overhead change physical widths; verify the pin capture.
// WS2812B-V5 wire limits are in the manual; these constants are not those limits.
#define WS2812_T0H_NS 300u
#define WS2812_T1H_NS 620u
#define WS2812_BIT_NS 1200u
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
