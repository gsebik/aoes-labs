# Lab 2 — GPIO, timers and interrupts

Reference: EP-0172 + Pico 2 W, Arm/Core 0, Pico SDK, PicoGremlin SWD + UART0.
The course manual is the guide; this file is a map of the source.

## Projects

One directory per task. Projects that build on earlier work compile your files
from the earlier directory, so nothing is copied by hand.

| Directory | Task | Targets | Your work |
|---|---|---|---|
| `01-relative/` | 1 | `aoes_lab02_relative` | `TODO R1` in `main.c` |
| `02-absolute/` | 1 | `aoes_lab02_absolute` | `TODO A1/A2` in `main.c` |
| `03-interrupt/` | 2 | `aoes_lab02_interrupt` | `TODO A1/A2/I1` in `main.c` |
| `04-edges/` | 3–4 | `aoes_lab02_edges`, `_recovery` | `TODO S1/S2` in `race.c`, then `TODO D1/D2` in `debounce_exercise.h` |
| `05-rgb/` | 5 | `aoes_lab02_rgb`, `_recovery` | `TODO W1/W2` in `waveform_exercise.c` |
| `06-irq/` | 6 | `aoes_lab02_irq`, `_recovery` | none; compiles your `05-rgb` sender |
| `07-controller/` | 7 | `aoes_lab02_controller`, `_recovery` | one change in `led_app.c`; compiles your `04-edges` and `05-rgb` code |
| `04-edges/` | optional ISR extension | `aoes_lab02_edges_isr_exercise` | `TODO E1–E3` in `edge_exercise.h` |
| `08-atomics/` | extension | `aoes_lab02_atomics` | none |
| `shared/` | — | — | board setup and the supplied reference versions |
| `tools/` | — | — | PC analysis and plotting, with tests |

Build from the project directory with an explicit target and flash the matching ELF:

```sh
export PICOLAB_BUILD_TYPE=Release
cd ~/aoes-labs/lab02/04-edges
picolab build aoes_lab02_edges
picolab flash build/aoes_lab02_edges.elf
picolab monitor
```

Type a command character followed by Enter in the monitor (`x` in `04-edges`,
`r g b w o` in `05-rgb`, `f e u m` in `06-irq`, `b` in `07-controller`).

## Recovery targets

An unfinished exercise fails to build with its `TODO` errors. A `_recovery` target
builds the same program from the supplied reference in `shared/` (recorder,
debounce rule and sender), so a group can continue while discussing the exercise.
The recorder banner says `recorder=supplied`; the filter banner says
`filter=exercise` or `filter=recovery`. Sender banners identify `sender=student`
or `sender=recovery`. A recovery filter does not complete Task 4.
The core recorder supplies the ring and compiles without the optional ISR TODOs.

## Contracts

- `04-edges/main.c [1]`, `shared/edge_reference.h`: one GPIO IRQ producer writes a ring
  of 256 slots (255 usable); the ISR owns `head` and publishes a slot by writing
  `head` last, main owns `tail` and releases a slot after copying it. Full means
  the newest edge is discarded and counted in `dropped`; a call with both edge
  flags latched is counted in `ambiguous`. Each recorded edge toggles GP16.
- `04-edges/debounce_exercise.h [2]`: the quiet-window rule runs in main on the ISR
  timestamps. `eligible_us` is when the rule could first decide; `handled_us` is
  when main processed it.
- `04-edges/race.c [R]`: a software-pended spare IRQ forces a known interleaving.
  `take_pending_events` starts unsafe; students protect its transfer in S1/S2.
  Injection leaves a request pending if masked and never waits inside that mask.
  Missing mask restoration/timeouts produce INVALID and restore normal service.
  This is a controlled test, not a natural failure probability or debounce rule.
- `shared/sender_body.h [W]`: only the 24-bit waveform is inside the optional
  mask; GP17 brackets it and GP12 carries the data. The 400 µs reset guard is
  outside the mask. Sender targets use `-O2` and run the bit loop from SRAM.
- `06-irq/main.c [H/L]`: two separately claimed hardware alarms with distinct IRQs;
  low priority `0xc0`, fast `0xc0` or `0x40`.
- `07-controller/led_app.c [A/S]`: main owns colour and fade state; the fade phase
  derives from an absolute epoch. `[B]` is a deliberately blocking fade.
- `08-atomics/main.c`: checks lock-free support before using the atomic object in
  an ISR.

The 300/620/1200 ns wait guards are calibrated for the reference build; they are
not the WS2812B-V5 wire limits. A correct-looking colour does not establish pulse
compliance; measure the pins.

## Tools

```sh
cd ~/aoes-labs/lab02
python3 -m venv .venv
.venv/bin/python -m pip install -r tools/requirements-plots.txt
.venv/bin/python -m unittest discover -s tools/tests
```

| Tool | Reads | Reports |
|---|---|---|
| `analyze_timing.py` | Task 1–2 UART logs | intervals and phase error |
| `analyze_pins.py` | analyzer CSV (`time_s,chN`) | sampled levels and transition intervals |
| `analyze_bounce.py` | one analyzer capture of GP14 + GP16, optional UART log | sampled input edges against marker toggles; explicit optional UART-burst alignment |
| `analyze_edges.py` | Task 3 UART log | press and release clusters, edge counts and spans |

From another project directory, use the lab environment's full path:
`~/aoes-labs/lab02/.venv/bin/python`.

Task 3 uses the normal `aoes_lab02_edges` with the initial pass-through filter:
observe a press, diagnose and repair the shared-word transfer, then collect raw
observations. Task 4 edits the filter. The optional `_isr_exercise` target uses
`edge_exercise.h`; it is not a dependency of the controller.

## Code style

The sources follow one style so that each file reads the same way. `.clang-format` in
the repository root holds the mechanical rules. Run it before you commit:

```sh
clang-format -i lab02/*/*.c lab02/*/*.h
```

Rules the formatter cannot check:

- **One declaration per line.** Write `uint8_t red;` and `uint8_t green;`, not `uint8_t red, green;`.
- **Blank lines separate steps.** Leave one between functions, and one between the setup, the loop and the reporting inside a long function.
- **Braces on every `if` and loop**, even for a single statement.
- **Name the numbers.** Put timing values, priorities and offsets in a named constant or `enum`, with a comment that says what the number means and its unit.
- **Comments say why**, on their own line above the code. A bracketed marker such as `[W]` stays because the manual points at it.
- **Short functions.** If `main` needs more than one screen, move each step into a small named function.
- **Print fixed-width integers with the `PRI` macros** (`PRIu32`, `PRIu64`, `PRId64`), as in C99 and later. Include `common/pri_compat.h`, which defines them when the toolchain does not. Ubuntu 24.04's `gcc-arm-none-eabi` 13.2 uses GCC's own `<stdint.h>`, so newlib 4.4.0 omits them.
- **Target C11 and the Ubuntu 24.04 toolchain.** Code must build there, and a newer compiler is fine once it does too.
- **Student files keep their `TODO` markers.** Keep each `#error "TODO …"` message on one line of at most 90 characters, and put longer instructions in a comment above it.
