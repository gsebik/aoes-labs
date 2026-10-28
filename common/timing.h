/* Cortex-M DWT timing helpers. Same core, fixed clock, less than one wrap.
 * A bracket counts elapsed core cycles, including interrupts and waits.
 */
#pragma once
#include <stdbool.h>
#include <stdint.h>
#include "pico/stdlib.h"
#include "hardware/sync.h"

#define TIMING_DEMCR (*(volatile uint32_t *)0xe000edfcu)
#define TIMING_DWT_CTRL (*(volatile uint32_t *)0xe0001000u)
#define TIMING_DWT_CYCCNT (*(volatile uint32_t *)0xe0001004u)

static inline uint32_t timing_read_cycles(void) {
    __compiler_memory_barrier();
    uint32_t value = TIMING_DWT_CYCCNT;
    __compiler_memory_barrier();
    return value;
}

static inline bool timing_counter_init(void) {
    TIMING_DEMCR |= 1u << 24; /* TRCENA: enable trace facilities. */
    __dsb();
    __isb();
    if (TIMING_DWT_CTRL & (1u << 25)) return false; /* NOCYCCNT */
    TIMING_DWT_CYCCNT = 0;
    TIMING_DWT_CTRL |= 1u;
    __dsb();
    __isb();
    uint32_t before = timing_read_cycles();
    __asm volatile("nop\nnop\nnop\nnop" ::: "memory");
    return timing_read_cycles() != before;
}

static inline double timing_cycles_to_us(double cycles, uint32_t clock_hz) {
    return cycles * 1000000.0 / clock_hz;
}
