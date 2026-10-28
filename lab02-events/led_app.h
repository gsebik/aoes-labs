#pragma once
#include "board.h"
void led_app_init(void);
void led_app_press(uint pin, uint64_t now);
void led_app_step(uint64_t now);
void led_app_blocking_fade(void);
