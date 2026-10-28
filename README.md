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
| `lab02/01-relative/` … `03-interrupt/` | Tasks 1–2: timing in main and a timer callback |
| `lab02/04-edges/` | Tasks 3–4: the button-edge recorder and your debounce rule |
| `lab02/05-rgb/`, `06-irq/` | Tasks 5–6: your RGB sender, and interrupts against it |
| `lab02/07-controller/` | Task 7: the controller built from your earlier code |
| `lab02/08-atomics/` | Advanced extension |
| `lab02/shared/` | Board setup and supplied reference versions |
| `lab02/tools/` | PC-side UART/pin analysis, plotting dependencies and tests |
| `lab02/captures/` | Create this directory for saved observations |
| `common/` | Shared elapsed-cycle helper for later experiments |
| `instruments/timing/` | Optional timing-instrument firmware |
| `tools/timing/` | Decoder for that optional instrument |

See `lab02/README.md` for the projects, targets and exercises. Separately named
`_recovery` programs let a group continue while discussing an unfinished exercise
with the lecturer; the startup banner identifies which executable is running.

## Reproducibility and status

The current `main` is a **review candidate**, not an unconditional hardware
qualification. See `lab02/release-card.md` for the exact verification
scope. Builds, actual station measurements and physical button/colour observations
are distinct evidence. Never use illustrative manual numbers as board results.

Retain the source revision, settings, ELF and raw captures together when comparing
measurements. Captures, build output and virtual environments are ignored by Git.

Authored code is MIT licensed. The
separately installed picogremlin-la analyzer is GPL-3.0-only and is not vendored.
