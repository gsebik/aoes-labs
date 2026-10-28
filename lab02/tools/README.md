# Lab 2 host analysis tools

These Python programs run on the PC, not on the RP2350. Firmware stays in
the individual project directories; captured files stay in `lab02/captures/`.
From `lab02/` in the standalone repository, for example:

```sh
.venv/bin/python tools/analyze_timing.py captures/relative-0.log --plot captures/relative-0.png
.venv/bin/python tools/analyze_edges.py captures/edges.log --pin 14 --gap-ms 50 --json captures/edges.json
.venv/bin/python tools/analyze_pins.py captures/pins-r20.csv --pins 16 17 --plot captures/pins-r20.png
```

Prepare the optional plot dependencies with the manual's virtual-environment
steps. Plain JSON decoding uses the Python standard library.

From `lab02/`, run host checks with:

```sh
python3 -m unittest discover -s tools/tests -v
```

The documentation repository keeps this pinned mirror at `src/aoes/lab02/tools/`.
The authoritative source distribution is `gsebik/aoes-labs`.

## Follow the calculation

`analyze_timing.py` has three main functions:

1. `analyze()` reads `led,` records, checks their settings and ordering, and
   calculates phase error: recorded time minus transition count × requested
   interval. Consecutive transition timestamps give an interval; missing records
   are not treated as a longer physical interval.
2. `plot()` draws phase error and transition intervals on shared axes. In the
   interrupt experiment, a third panel shows callback counts observed by main.
3. `main()` reads filenames/options, prints a brief summary and saves the chosen
   JSON and plot files. `--plot` saves a file; it does not launch a viewer.

Open the saved image with `xdg-open captures/relative-0.png`. JSON includes the
raw-file SHA-256, settings, decoded rows and interval/phase summaries so results
can be traced back to the input file.

`analyze_pins.py` reads sampled logic levels from a logic-analyzer CSV and measures
complete pulses and transition intervals. `analyze_edges.py` groups ISR-observed
button edges using the specified quiet-gap assumption, then reports separate
press/release statistics. Each script separates decoding/calculation (`analyze`),
drawing (`plot`) and command-line handling (`main`). Their checks reject incomplete
or inconsistent evidence rather than silently invent missing observations.

`legacy_timing.py` is retained only to read old rc6 `window`/`timing,` captures.
The current three timing projects use `analyze_timing.py`.
