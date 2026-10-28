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

The later experiments remain in `lab02-events/`. Earlier reference-station
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
