# AoES Labs — RP2350 / EP-0172

Student starter code and measurement tools for **Architecture of Embedded
Systems**. The [lab manuals](https://www.aut.uni-obuda.hu/es-work/Architecture%20Of%20Embedded%20Systems/Labs/)
are maintained separately from this repository.

## Start Lab 2

Reference station: EP-0172 + Pico 2 W (RP2350 Arm/Core 0) + PicoGremlin, using
SWD and UART0. Complete the manual's Environment Setup first.

```sh
git clone --depth 1 --branch main \
  https://github.com/gsebik/aoes-labs.git ~/aoes-labs
cd ~/aoes-labs/lab02/01-relative
code .
```

Record `git rev-parse HEAD` with your measurements to identify the source version.

Each timing experiment has its own `main.c`. Follow the manual to implement
its timing statements, build, program the board and compare the recorded output.
Keep source edits outside `build/`.

| Directory | Contents |
|---|---|
| `lab02/01-relative/` | Relative wait directly in main's loop |
| `lab02/02-absolute/` | Clock check and absolute-target update in main |
| `lab02/03-interrupt/` | Foreground loop and SDK timer callback |
| `lab02/tools/` | PC-side UART/pin analysis, plotting dependencies and tests |
| `lab02/captures/` | Create this directory for saved observations |
| `lab02-events/` | Later button, shared-state, RGB and interrupt-interference experiments |
| `common/` | Shared elapsed-cycle helper for later experiments |
| `instruments/timing/` | Optional timing-instrument firmware |
| `tools/timing/` | Decoder for that optional instrument |

The waveform targets use the student exercise. Separately named `_recovery`
programs let a group continue while discussing an unfinished sender with the
lecturer; the startup banner identifies which executable is running.

## Reproducibility and status

`aoes-lab02-v1.0.0-rc7` is a **review candidate**, not an unconditional hardware
qualification. See `lab02-events/release-card.md` for the exact verification
scope. Builds, actual station measurements and physical button/colour observations
are distinct evidence. Never use illustrative manual numbers as board results.

Retain the source revision, settings, ELF and raw captures together when comparing
measurements. Captures, build output and virtual environments are ignored by Git.

Authored code is MIT licensed. The
separately installed picogremlin-la analyzer is GPL-3.0-only and is not vendored.
