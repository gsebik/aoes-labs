# AoES Labs — RP2350 / EP-0172

Student starter code and measurement tools for **Architecture of Embedded
Systems**. The [lab manuals](https://www.aut.uni-obuda.hu/es-work/Architecture%20Of%20Embedded%20Systems/Labs/)
are maintained separately from this repository.

## Start Lab 2

Reference station: EP-0172 + Pico 2 W (RP2350 Arm/Core 0) + PicoGremlin, using
SWD and UART0. Complete the manual's Environment Setup first.

```sh
git clone --depth 1 --branch aoes-lab02-v1.0.0-rc3 \
  https://github.com/gsebik/aoes-labs.git ~/aoes-labs
cd ~/aoes-labs/lab02-events
code .
```

The project starts with a small T1 exercise. Follow the manual before expecting
the timing target to compile. Student edits belong in source files, never in
`build/`. Keep `common/` in its supplied location.

| Directory | Contents |
|---|---|
| `lab02-events/` | Seven-task lab project, guided timing/waveform TODOs, analysis tools and tests |
| `common/` | Shared elapsed-cycle helper |
| `tools/timing/` | Optional cycle/period observation instrument and decoder |
| `tools/picolab/` | Course command helper, including explicit Release/Debug selection |

This repository contains no RTOS dependency, course-site checkout, private
solutions or instructor acceptance completions. The normal waveform targets use
the exercise; separately named `_recovery` programs let a group continue without
mistaking recovery work for a completed exercise.

## Reproducibility and status

`aoes-lab02-v1.0.0-rc3` is a **review candidate**, not an unconditional hardware
qualification. See `lab02-events/release-card.md` for the exact verification
scope. Builds, actual station measurements and physical button/colour observations
are distinct evidence. Never use illustrative manual numbers as board results.

The source in this repository is authoritative. The course documentation keeps a
pinned mirror for its excerpts and material register; its source-check command
compares this repository and the recorded release rather than accepting silent
divergence. Student captures, build output and virtual environments are ignored.

Authored code is MIT licensed; tools retain their existing license notices. The
separately installed picogremlin-la analyzer is GPL-3.0-only and is not vendored.
