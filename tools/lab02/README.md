# Lab 2 host analysis tools

These Python programs run on the PC, not on the RP2350. Firmware stays in
`lab02-events/`; captured files stay in that project's `captures/` directory.
From the firmware directory in the standalone repository, for example:

```sh
.venv/bin/python ../tools/lab02/analyze_timing.py captures/timing-r0.log --plot captures/r0.png
.venv/bin/python ../tools/lab02/analyze_edges.py captures/edges.log --pin 14 --gap-ms 50 --json captures/edges.json
.venv/bin/python ../tools/lab02/analyze_pins.py captures/pins-r20.csv --pins 16 17 --plot captures/pins-r20.png
```

Prepare the optional plot dependencies with the manual's virtual-environment
steps. Plain JSON decoding uses the Python standard library.

From the standalone repository root, run host checks with:

```sh
python3 -m unittest discover -s tools/lab02/tests -v
```

The documentation repository keeps this pinned mirror at `tools/aoes/lab02/`.
The authoritative source distribution is `gsebik/aoes-labs`.
