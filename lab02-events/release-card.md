# Lab 2 source candidate — aoes-lab02-v1.0.0-rc4

Repository: https://github.com/gsebik/aoes-labs

Clone this immutable tag and retain its commit (`git rev-parse HEAD`) with your
measurements. This pack contains the Lab 2 starter, common helper, optional timing
instrument, host analyzers and compatible picolab command helper. The course-site
repository and private instructor completions are not dependencies.

## Build configuration

- Target: Pico 2 W / RP2350 Arm/Core 0; EP-0172 pin map; UART0 via PicoGremlin.
- Acceptance toolchain: Pico SDK 2.3.1; Arm GNU GCC 16.2.0 on the instructor host.
- Measurement builds: Release. Instruction-dependent waveform translation units
  additionally use O2, including Debug builds; this is explicit in CMakeLists.txt.
- T1 is required for relative mode; T2/T3 for absolute mode; T4/T5 only when the
  callback is enabled. W1/W2 are required by the normal waveform targets.
- Separately named `_recovery` targets use the supplied recovery implementation.
  Startup prints `sender=student` or `sender=recovery`; there is no cached switch.

After completing the selected timing TODOs, from `lab02-events/`:

```sh
picolab build aoes_lab02_timers --release-build
picolab flash build/aoes_lab02_timers.elf
picolab monitor
```

The compatible helper is included at `../tools/picolab/picolab` if the installed
copy lacks `--release-build`. It uses the same SDK/toolchain installation.
`n` then Enter restarts the observation window; mode/workload/callback remain
compiled settings in timing_config.h. Record one minute after the fresh header
for each of r0, a0, r20, a20 and b0. Keep separate logs and ELFs.

The first implementation, interval change, selected TODO errors, five matched
configurations, completed waveform programs, recovery programs and Debug-to-Release
switch are covered by build checks. Decoder tests cover malformed/inconsistent
records and the distinction between toggle intervals and full periods.

## Automated station checks

The 2026-10-28 instructor walkthrough used this source on the reference station:

- Relative/absolute first runs, 200 ms interval change and five matched timing
  windows; each matched window retained at least one minute after a reset header.
- Actual GP16/GP17 captures for relative/absolute 20 ms-work comparisons at 10 kS/s.
- Deterministic read/clear loss and protected transfer, with their expected values.
- GP12 RGB pulses and all four IRQ cases captured at 50 MS/s, with valid UART rows.
- Lock-free atomic-counter comparison and the controller's blocking-fade command.

These are observations on the recorded configuration, not guaranteed timing
bounds. Captures and private completed acceptance copies remain with the
instructor, separately from this starter.

## Hardware qualification boundary

A source tag identifies code, not an unconditional timing guarantee. The
instructor's dated bench record lists actual SWD/UART/analyzer checks separately
from builds. Physical K1/K2 trials, visual channel order and fitted LED revision
must be confirmed before assigning this as a qualified teaching release.

The analyzer can show physical GP16/GP17 transitions, and high-rate captures can
measure GP12 pulses subject to sample resolution and clock uncertainty. UART
plots show report-time phase observations, not every edge or CPU execution.
An observed maximum is not a WCET/WCRT bound. Debugger stops alter timing.
