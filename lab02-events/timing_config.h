#pragma once
#include <stdint.h>

// Edit this file, rebuild aoes_lab02_timers, then flash its new ELF.
// UART input never changes the compiled experiment settings.
#define LAB02_MODE_RELATIVE 1
#define LAB02_MODE_ABSOLUTE 2
#define LAB02_MODE_CPU_WORK 3
#define LAB02_TIMING_MODE LAB02_MODE_RELATIVE
#define LAB02_FOREGROUND_WORK_US 0u
#define LAB02_ENABLE_TIMER_CALLBACK 0

// One transition per 500 ms gives one full on/off cycle per second.
#define HALF_PERIOD_MS 500
#define HALF_PERIOD_US ((uint64_t)HALF_PERIOD_MS * 1000u)
// An iteration count, not a calibrated execution duration.
#define BUSY_ITERATIONS 5000000u

#if LAB02_TIMING_MODE < LAB02_MODE_RELATIVE || LAB02_TIMING_MODE > LAB02_MODE_CPU_WORK
#error "Choose one of the three LAB02_MODE_ settings in timing_config.h"
#endif
#if LAB02_ENABLE_TIMER_CALLBACK != 0 && LAB02_ENABLE_TIMER_CALLBACK != 1
#error "LAB02_ENABLE_TIMER_CALLBACK must be 0 or 1"
#endif
#if HALF_PERIOD_MS <= 0
#error "HALF_PERIOD_MS must be positive"
#endif
