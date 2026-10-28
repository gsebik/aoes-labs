// Recoverable implementation for later experiments and comparison after an attempt.
#include "ws2812.h"
#define PACK_GRB(g, r, b) (((uint32_t)(g) << 16) | ((uint32_t)(r) << 8) | (b))
#define HIGH_CYCLES(one) ((one) ? one_cycles : zero_cycles)
#include "sender_body.h"
