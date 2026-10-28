#pragma once
#include <inttypes.h>
#include <stdio.h>
#include "pico/stdlib.h"
#include "hardware/clocks.h"
#include "hardware/sync.h"
#include "../../common/timing.h"

// Tasks 1–2 use GP16/17 as visible foreground/callback outputs.
// Tasks 5–6 reuse those pins as IRQ-entry/frame measurement markers.
enum { K1_PIN = 14, K2_PIN = 15, IRQ_MARKER_PIN = 16,
       FRAME_MARKER_PIN = 17, RGB_PIN = 12 };
void lab_board_init(const char *experiment, bool buttons);
