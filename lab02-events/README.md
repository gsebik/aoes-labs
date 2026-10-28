# Lab 2 — events, time and a CPU-driven RGB waveform

Reference: EP-0172 + Pico 2 W, Arm/Core 0, Pico SDK, Gremlin SWD + UART0.
This is a **review candidate**. The build matrix and automated station checks
have been exercised; physical-button statistics, visual colour confirmation and
the fitted LED revision still need acceptance. It is not an issued release pack.

## Programs

| Target | Source | Purpose / controls |
|---|---|---|
| `aoes_lab02_timers` | `timers.c` | GP16 foreground, GP17 callback. Edit `timing_config.h` to choose the timing mode, workload and callback enable; rebuild and flash. `n` starts a fresh measurement window without changing settings. |
| `aoes_lab02_events` | `events.c`, `race.c` | GP14/15 edge recorder, quiet-window filter, loss counters. `x` reproduces read/clear event loss and its repair. |
| `aoes_lab02_rgb` | `rgb.c`, `waveform_exercise.c` | `r`, `g`, `b`, `w`, `o` select low-brightness colours. |
| `aoes_lab02_irq` | `irq_experiment.c`, `waveform_exercise.c` | `f`, `e`, `u`, `m` select foreground, equal-priority, urgent, masked-frame experiments. |
| `aoes_lab02_controller` | `events.c`, `led_app.c`, `waveform_exercise.c` | K1 cycles colour; K2 switches fade/steady. UART `b` runs one blocking-fade comparison. |
| `aoes_lab02_atomics` | `atomics.c` | Advanced, controlled volatile/critical-section/atomic counter comparison. |

Type a command character followed by Enter in the UART monitor. The CMake
default first target is `aoes_lab02_timers`; use explicit names throughout.

## Get the student source

The pinned source candidate is `aoes-lab02-v1.0.0-rc5` in the public
`gsebik/aoes-labs` repository. The course manual is linked from the root README.

```sh
git clone --depth 1 --branch aoes-lab02-v1.0.0-rc5 \
  https://github.com/gsebik/aoes-labs.git ~/aoes-labs
cd ~/aoes-labs/lab02-events
code .
```

Keep `../common/` beside the project. No course-document checkout, RTOS or nested
repository is required. Complete the course station setup first. Use the already installed `picolab` from Environment Setup. No CLI or installer
is bundled here. In the lab terminal, set the measurement build once:

```sh
export PICOLAB_BUILD_TYPE=Release
```

Repeat that setting when opening a new terminal. `picolab debug --debug-build`
selects Debug only for its own invocation; later normal builds use this terminal's
Release setting.

## Implement the timing versions

`timing_config.h` contains the experiment settings. `timers.c` contains five
small TODOs; reporting, timestamps, work injection and GPIO initialization are
provided. Replace each active `#error` with your implementation. Inactive modes
are excluded by the preprocessor, so later TODOs do not block the first stage.

| Stage | Configuration | Required implementation | Functional check |
|---|---|---|---|
| Relative wait | `LAB02_MODE_RELATIVE`, callback `0` | T1: one `sleep_ms` call using the requested millisecond interval | GP16 changes; IRQ count is zero. |
| Absolute targets | `LAB02_MODE_ABSOLUTE`, callback `0` | T2: due comparison, including equality; T3: advance the previous microsecond target | Compare with relative timing under the same work. |
| Timer interrupt | `LAB02_MODE_CPU_WORK`, callback `1` | T4: GP17 XOR operation; T5: checked repeating-timer registration using a negative millisecond interval | Both counts grow while the foreground calculation runs. |

The detailed manual gives API signatures, variables, predictions and fault
checks. Keep the supplied recorder unchanged when comparing these versions.
`LAB02_FOREGROUND_WORK_US` selects the interruptible busy interval after each
relative/absolute transition; CPU-work mode applies zero additional work.
A relative wait is a duration; an absolute target is a clock timestamp.

After implementing a stage, build and program its ELF:

```sh
picolab build aoes_lab02_timers
picolab flash build/aoes_lab02_timers.elf
picolab monitor
```

In the monitor type `n`, then Enter, to reset the measurement origin, counters
and timer registration and print the settings. This command changes no settings.
Close the monitor with Ctrl+C before rebuilding/programming. Retain separate
captures and the corresponding source/configuration/ELF for each comparison.
Changing the header without programming the rebuilt ELF does not change the board.

For Task 2's five matched runs, keep `HALF_PERIOD_MS=500` and callback `1`:
relative/0, absolute/0, relative/20000, absolute/20000 and CPU-work/0. Record at
least one minute per run after its `window` header. The printed `mode=r/a/b`
labels identify compiled modes; they are not UART selection commands.

Other targets retain their input commands: for example `x` triggers the
controlled race and `b` starts the controller's blocking-fade comparison.
Specify the target and its ELF by name; never use an old ELF after a failed build.

## Sender exercise and recovery

The normal `aoes_lab02_rgb`, `aoes_lab02_irq` and `aoes_lab02_controller` targets
compile `waveform_exercise.c`. Task 5 completes its two guarded macros: GRB
packing and high-duration selection. `sender_body.h` supplies the explicit GPIO
stores, SRAM bit loop and measurement mechanics.

```sh
picolab build aoes_lab02_rgb
```

An unfinished exercise fails with W1/W2 errors. For recovery, use an explicitly
named target and its matching ELF, for example:

```sh
picolab build aoes_lab02_irq_recovery
picolab flash build/aoes_lab02_irq_recovery.elf
```

The startup banner prints `sender=student` or `sender=recovery`. Recovery targets
use the supplied `ws2812.c` and do not count as completing W1/W2. No cached
sender switch affects a later build.

Pulse targets are in `ws2812.h`. The CPU loop is in SRAM and sender targets use
`-O2` even when the rest of a debug configuration would otherwise use `-Og`.
Record the effective compiler flags and `clk_sys`; inspect the linked loop.

## Timing and ownership contracts

- `timers.c [W]`: the same interruptible busy interval follows each foreground
  toggle in `r` and `a`. `work_us` is the applied setting; `work_elapsed_us` is
  the most recent observed call duration, including IRQ service. These are not
  execution-demand bounds. `b` uses only its iteration loop and reports zero
  extra workload. Edit/rebuild/flash to change mode or workload; `n` starts a fresh window with those compiled settings.
- `timers.c [1/T4]`: SDK repeating-timer callback in IRQ context, not a thread. It is disabled until the student completes and enables T4/T5.
  `[2]` dispatches the compiled foreground strategy; `[3]` snapshots count/timestamp
  with local interrupts briefly masked. Startup registration adds a phase offset.
- `events.c [1]`: one GPIO IRQ producer. Records and indices are volatile;
  the aligned 32-bit head publishes a completed slot. Main copies then releases
  through tail. Capacity is 255 records; full means discard newest and count it.
  Simultaneous rise/fall flags are counted as ambiguous and not ordered by guess.
- `events.c [2]`: main replays observed quiet gaps before updating each candidate.
  `DEBOUNCE_US=5000` is an initial trial setting, not a measured switch bound.
  `eligible_us` is when the filter's observed quiet interval ends;
  `handled_us` is when main actually processes that logical event. Final
  confirmation samples pins and ring emptiness under a short local mask;
  printing and application updates occur after restoration.
- `race.c [R]`: a software-pended spare IRQ forces a known interleaving. It is
  not a measurement of natural failure probability. The protected path never
  waits with interrupts masked. Event bits coalesce; they cannot replace a
  timestamp queue when every edge matters.
- `sender_body.h [W]`: only the 24-bit waveform is inside the optional mask.
  GP17 brackets that waveform; GP12 carries LED data. The low reset guard is
  outside that mask. The returned cycle span includes any preemption; its
  endpoints differ from the UART microsecond bracket and physical wire edges.
- `irq_experiment.c [H/L]`: two separately claimed hardware alarms, distinct
  IRQs. Low IRQ uses priority `0xc0`; high IRQ uses `0xc0` or `0x40` (lower
  number is more urgent). Default SDK alarm ownership is respected. Reports
  reject missed setup deadlines/timeouts. Entry timestamps include SDK dispatch.
  Equal-priority service also waits for the sender's low reset guard, since
  the candidate design performs the entire blocking function in the low ISR.
- `led_app.c [A/S]`: main owns colour and fade state. Fade phase derives from
  an absolute epoch. `[B]` is an intentionally blocking, real fade for comparison;
  the later queue drain exposes handling delay and possible capacity limits.
- `atomics.c`: uses a separate software-pended IRQ, on a different executable.
  It checks this atomic object's lock-free support before enabling ISR use.
  The exclusive retry loop need not be wait-free. SDK initialization is retained.

The fitted LED must be identified before pulse compliance is claimed. Current
400/800 ns high and 1250 ns total targets refer to the cited classical WS2812B
specification, not all package revisions. The reset guard is a 400 us design
setting. A correct-looking colour does not establish pulse compliance. Changing
clock, compiler, placement or timing constants requires a fresh wire capture.

## Capture and decode

The decoders use the Python standard library. Prepare the optional plotter once:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-plots.txt
```

`analyze_timing.py` plots the five UART summary logs with `--json` and `--plot`.
It selects the last announced window in each file, prints that choice and
retains the source hash. It rejects malformed or inconsistent rows. Report-time
points are observations, not a reconstruction of every transition.

`analyze_pins.py` reads the analyzer's `time_s,chN` CSV, draws actual sampled GPIO
levels and reports complete transition intervals/full periods. `--pins 16 17`
selects the timing outputs; `--pins 12 16 17` selects waveform/IRQ markers.
Incomplete boundary pulses are excluded, and missing channels or nonuniform
sampling are rejected. The instrument's clock accuracy is not established by
these plots. Use `picolab la gui` to inspect and export captures interactively.


Create a capture directory:

```sh
mkdir -p captures
```

Run the monitor through `tee` to retain what it prints, without guessing a port:

```sh
picolab monitor | tee captures/edges.log
```

One capture per reset. Start released, make deliberate presses/releases, then
leave the inputs quiet for at least a second and retain a final `status` line
before Ctrl+C. The monitor still accepts keyboard input through its stdin.
The decoder ignores monitor banners and button/race messages.

```sh
.venv/bin/python analyze_edges.py captures/edges.log --pin 14 --gap-ms 50 --json captures/edges.json --plot captures/edges.png
```

The grouping gap is an analysis assumption. The JSON retains cluster endpoints,
counts, histograms and separate press/release min/median/max spans. It excludes
an unfinished final cluster. It rejects malformed records, reset-spanning logs,
missing status/edges and nonzero drop/ambiguity counts. `--allow-loss` explicitly
retains a limited dataset for diagnosis; do not derive a filter bound from it.
Zero counters cannot prove the GPIO hardware observed every electrical edge.

## Acceptance before teaching release

Record source/settings/ELF hash, SDK/compiler/clock, probe firmware and capture
instrument resolution. Validate all of the following on the reference board:

1. Matched foreground/callback timing windows and mode-reset behaviour.
2. Pin map, raw edges, quiet-gap statistics, overflow/ambiguity handling and
   per-trial debounce results. Never infer missed/double counts from totals alone.
3. RGB channel order, pulse highs/lows/period and reset guard against the fitted
   part. Use a validated >=50 MS/s capture or suitable oscilloscope; retain data.
4. Actual IRQ/frame overlap, priority nesting, service lateness and bounded mask.
5. Controlled race results, safe ownership and the responsive/blocking comparison.
6. Atomic object lock-free report and the linked implementation of both orders.

The instructor walkthrough used this source on RP2350 with SDK 2.3.1/GCC 16.2.0:
the timing comparisons, forced race/repair, RGB/IRQ captures, atomic counts and
blocking-fade command were exercised. Those checks do not replace the physical
button trials, visual colour check or fitted-part identification above. Keep
this candidate under review until those remaining checks are recorded. Old
experiments are not acceptance data for a different build.
