# Lab 2 source candidate — main

Repository: https://github.com/gsebik/aoes-labs

This source is a review candidate. Retain its commit (`git rev-parse HEAD`), your
source edits, build settings, ELF and raw observations together.

## Timing projects

Tasks 1–2 use three independent projects under `lab02/`. Each has one `main.c`:

- `01-relative`: implement `TODO R1`, the wait before the GPIO change.
- `02-absolute`: implement `TODO A1`, the due check, and `TODO A2`, the target increment.
- `03-interrupt`: reuse your `TODO A1/A2` and implement `TODO I1`, timer registration.

The supplied placeholders compile. Their observed behaviour helps identify
unfinished timing statements. Follow the manual's functional checks.

From the selected project directory, for example `lab02/01-relative/`:

```sh
export PICOLAB_BUILD_TYPE=Release
picolab build
picolab flash build/aoes_lab02_relative.elf
picolab monitor
```

Use the matching ELF name for each project. Logs contain individual GP16
transition records, the interval and work settings, and elapsed board time.
The interrupt project also reports callback counts observed by main.
Host analysis and plotting programs are in `lab02/tools/`.

## Verification scope

All three timing starters and private completed versions compiled with Pico SDK
2.3.1 and Arm GNU GCC 16.2.0, in Release configuration. The host test suite checks
log validation, interval/phase calculations and pin decoding. These new direct
programs still require a fresh board walkthrough; earlier timing-framework
captures do not qualify these changed programs.

The later experiments are in `lab02/04-edges` … `08-atomics`, one directory per
task (reorganised from `lab02-events/` on 2026-10-28). Earlier reference-station
checks exercised deterministic race/repair, RGB pulse generation and IRQ
interference, lock-free atomic counts and the blocking-fade comparison.
The user confirmed visible colour/brightness control with the shorter-zero
24-bit GRB sender. The final reference wire capture measured approximately
320 ns zero HIGH and 640 ns one HIGH at 50 MS/s. Its fade uses 62.5 ms steps
for an approximately two-second up/down cycle. Per-trial debounce statistics
and wider classroom acceptance remain pending.

Normal waveform targets require W1/W2 in `waveform_exercise.c`; separately
named `_recovery` targets provide the supplied sender. Use the target and
matching ELF explicitly.

A source tag identifies code, not a worst-case timing guarantee. UART timestamps
are read after GPIO writes; callback counts are not callback timestamps. Physical
pin captures have finite sampling resolution. Debugger stops alter timing.

## Station walkthrough, 2026-10-28

Fresh clone, every task as a student, EP-0172 + Pico 2 W + PicoGremlin, SDK 2.3.1,
GCC 16.2.0, Release:

- Tasks 1–2: median intervals 502.8 ms (relative, no work), 522.9 ms (relative,
  20 ms work), 500.0 ms (absolute, both); with 650 ms of work GP16 changed every
  653 ms and GP17 every 500 ms; the backtrace showed `alarm_pool_irq_handler`.
- Tasks 3–4 (new `04-edges` layout): race demonstration `copied=1,remaining=0`
  then `remaining=2`; the written ISR and debounce rule were exercised with
  **simulated** presses (the button pin driven low over SWD, bursts about 0.5 ms
  apart). Real contact bounce, per-trial debounce statistics and the multimeter-free
  physical captures still need a person pressing the buttons.
- Task 5: 320 ns zero highs, 640 ns one high, 960–980 ns lows at 50 MS/s.
- Task 6: `f` one high stretched to about 2.0 µs, `e` intact with 422 µs service
  delay, `u` one low stretched to about 1.8 µs, `m` intact with about 22 µs delay.
- Task 7: colour and fade control and the blocking-fade comparison (about 1.6 s
  handling delay) with simulated presses; the colours were not inspected by eye.
- Extension: the atomic counts and `LDREX/STREX`, `LDAEX/STLEX` loops as described.


## Task 3 review update

The core recorder is now supplied. The required Task 3 edit is S1/S2 in
`04-edges/race.c`: protect a shared read/clear without losing the injected event.
The optional `_isr_exercise` target retains E1–E3. Task 4 still implements D1/D2;
normal controller builds use that filter with the supplied ring.

The race reports one before/after result per `x`, not the old supplied bad/protected
pair. It rejects an un-restored interrupt mask or timed-out injection. The updated transfer passed host-model and cross-build checks. On the identified
reference station, actual picolab monitor returned copied=1/remaining=0 before
repair and copied=1/remaining=2 afterwards. An omitted restore returned INVALID
and regular status reports continued. The board check used Release, SDK 2.3.1,
GCC 16.2.0 at 150 MHz. Physical bounce and per-trial debounce observations remain
pending; these controlled IRQ checks do not substitute for them.

Bounce-analysis v2 requires explicit UART-burst selection and leaves ambiguous
edge/marker associations unpaired. Its sampled gaps are not IRQ-entry latency.
