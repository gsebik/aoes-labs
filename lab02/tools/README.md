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
