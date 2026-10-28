cmake_minimum_required(VERSION 3.13)
set(PICO_BOARD pico2_w CACHE STRING "AoES reference board")
include($ENV{PICO_SDK_PATH}/external/pico_sdk_import.cmake)
project(aoes_lab02 C CXX ASM)
set(CMAKE_C_STANDARD 11)
pico_sdk_init()
if(NOT PICO_RP2350 OR NOT PICO_PLATFORM MATCHES "arm")
    message(FATAL_ERROR "Lab 2 timing sources require the RP2350 Arm platform")
endif()
add_executable(aoes_lab02_timers timers.c board.c)
add_executable(aoes_lab02_events events.c board.c race.c)
add_executable(aoes_lab02_rgb rgb.c board.c waveform_exercise.c)
add_executable(aoes_lab02_irq irq_experiment.c board.c waveform_exercise.c)
add_executable(aoes_lab02_controller events.c board.c race.c led_app.c waveform_exercise.c)
target_compile_definitions(aoes_lab02_controller PRIVATE LAB_WITH_RGB=1)
# Recovery is an explicitly named program, never a cached sender switch.
add_executable(aoes_lab02_rgb_recovery rgb.c board.c ws2812.c)
add_executable(aoes_lab02_irq_recovery irq_experiment.c board.c ws2812.c)
add_executable(aoes_lab02_controller_recovery events.c board.c race.c led_app.c ws2812.c)
target_compile_definitions(aoes_lab02_controller_recovery PRIVATE LAB_WITH_RGB=1)
add_executable(aoes_lab02_atomics atomics.c board.c)
foreach(target aoes_lab02_timers aoes_lab02_events aoes_lab02_rgb
               aoes_lab02_irq aoes_lab02_controller aoes_lab02_atomics
               aoes_lab02_rgb_recovery aoes_lab02_irq_recovery
               aoes_lab02_controller_recovery)
    target_link_libraries(${target} pico_stdlib hardware_timer hardware_irq
                                  hardware_sync hardware_clocks)
    target_compile_options(${target} PRIVATE -Wall -Wextra)
    pico_enable_stdio_uart(${target} 1)
    pico_enable_stdio_usb(${target} 0)
    pico_add_extra_outputs(${target})
endforeach()

# Keep the instruction-dependent sender build consistent, including Debug builds.
foreach(target aoes_lab02_rgb aoes_lab02_irq aoes_lab02_controller)
    target_compile_options(${target} PRIVATE -O2)
    target_compile_definitions(${target} PRIVATE LAB02_SENDER_NAME="student")
endforeach()
foreach(target aoes_lab02_rgb_recovery aoes_lab02_irq_recovery
               aoes_lab02_controller_recovery)
    target_compile_options(${target} PRIVATE -O2)
    target_compile_definitions(${target} PRIVATE LAB02_SENDER_NAME="recovery")
endforeach()
