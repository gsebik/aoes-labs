// Shared mechanics. The selected translation unit supplies the two protocol choices.
static uint32_t zero_cycles, one_cycles, bit_cycles;
static volatile ws2812_observation_t observation;

void ws2812_init(void) {
    gpio_init(RGB_PIN);
    gpio_set_dir(RGB_PIN, GPIO_OUT);
    gpio_put(RGB_PIN, 0);
    uint32_t hz = clock_get_hz(clk_sys);
    zero_cycles = (uint64_t)hz * WS2812_T0H_NS / 1000000000u;
    one_cycles = (uint64_t)hz * WS2812_T1H_NS / 1000000000u;
    bit_cycles = (uint64_t)hz * WS2812_BIT_NS / 1000000000u;
    printf("sender wait_guards_ns: zero_high=%u one_high=%u cell=%u reset_us=%u\n",
           WS2812_T0H_NS, WS2812_T1H_NS, WS2812_BIT_NS, WS2812_RESET_US);
    busy_wait_us(WS2812_RESET_US);
}

// [W] The whole 24-bit loop executes from SRAM. IRQs can still interrupt it.
void __not_in_flash_func(ws2812_send_grb)(uint8_t green, uint8_t red,
                                         uint8_t blue, bool mask_irqs) {
    uint32_t word = PACK_GRB(green, red, blue);
    uint32_t state = 0;
    observation.start_us = time_us_64();
    if (mask_irqs) state = save_and_disable_interrupts();
    sio_hw->gpio_set = 1u << FRAME_MARKER_PIN;
    uint32_t frame_start = timing_read_cycles();
    for (uint32_t mask = 1u << 23; mask; mask >>= 1) {
        bool one = (word & mask) != 0;
        uint32_t high_cycles = HIGH_CYCLES(one);
        uint32_t start = timing_read_cycles();
        sio_hw->gpio_set = 1u << RGB_PIN;
        ws2812_wait_from(start, high_cycles);
        sio_hw->gpio_clr = 1u << RGB_PIN;
        ws2812_wait_from(start, bit_cycles);
    }
    observation.cycles = timing_read_cycles() - frame_start;
    sio_hw->gpio_clr = 1u << FRAME_MARKER_PIN;
    if (mask_irqs) restore_interrupts(state);
    observation.end_us = time_us_64();
    // IRQs remain enabled during the low reset interval in the normal thread path.
    // If called from an ISR, only higher-priority IRQs can preempt this wait.
    busy_wait_us(WS2812_RESET_US);
}

ws2812_observation_t ws2812_last_observation(void) {
    uint32_t state = save_and_disable_interrupts();
    ws2812_observation_t copy = {
        observation.start_us, observation.end_us, observation.cycles
    };
    restore_interrupts(state);
    return copy;
}
