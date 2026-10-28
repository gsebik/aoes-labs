#include "ws2812.h"

// Task 5A: form the transmitted 24-bit word. The loop sends bit 23 first.
// GRB means the green byte is sent before red, then blue.
#error "TODO W1: define PACK_GRB(g, r, b) using shifts and bitwise OR"

// Task 5B: select the high-pulse duration for a data bit of zero or one.
// zero_cycles and one_cycles are computed from the recorded clock in the helper.
#error "TODO W2: define HIGH_CYCLES(one) with the appropriate duration choice"

#include "sender_body.h"
