#!/usr/bin/env python3
"""Measure physical logic-analyzer samples from la CSV exports (time_s,chN)."""
import argparse
import csv
import hashlib
import io
import json
import math
from pathlib import Path
from statistics import median


def channel(pin):
    if 2 <= pin <= 22:
        return pin - 2
    if 26 <= pin <= 28:
        return pin - 5
    raise ValueError("PicoGremlin inputs cover GP2–22 and GP26–28")


def analyze(text, pins):
    reader = csv.DictReader(io.StringIO(text))
    columns = [f"ch{channel(pin)}" for pin in pins]
    if not reader.fieldnames or not set(["time_s", *columns]).issubset(reader.fieldnames):
        raise ValueError("Expected la CSV columns time_s and selected chN columns")
    times, levels = [], {str(pin): [] for pin in pins}
    for row in reader:
        try:
            stamp = float(row["time_s"])
            if not math.isfinite(stamp) or stamp < 0 or (times and stamp <= times[-1]):
                raise ValueError("Sample times must increase")
            times.append(stamp)
            for pin, column in zip(pins, columns):
                value = int(row[column])
                if value not in (0, 1):
                    raise ValueError("Logic levels must be 0 or 1")
                levels[str(pin)].append(value)
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(f"Malformed sample: {exc}") from exc
    if len(times) < 2:
        raise ValueError("At least two samples are required")
    spacing = median(b - a for a, b in zip(times, times[1:]))
    if any(abs((b - a) - spacing) > max(spacing * .001, 1e-12)
           for a, b in zip(times, times[1:])):
        raise ValueError("Nonuniform sample spacing; do not treat gaps as continuous capture")
    signals = {}
    for pin in pins:
        values = levels[str(pin)]
        edges = [{"time_s": times[i], "level": values[i]}
                 for i in range(1, len(times)) if values[i] != values[i-1]]
        widths = [{"level": a["level"], "start_s": a["time_s"],
                   "width_s": b["time_s"] - a["time_s"]}
                  for a, b in zip(edges, edges[1:])]
        intervals = [w["width_s"] for w in widths]
        rising = [e["time_s"] for e in edges if e["level"]]
        periods = [b-a for a, b in zip(rising, rising[1:])]
        signals[str(pin)] = {"channel": channel(pin), "initial_level": values[0], "edges": edges,
                             "complete_widths": widths,
                             "median_transition_interval_s": median(intervals) if intervals else None,
                             "median_full_period_s": median(periods) if periods else None}
    return {"schema": "aoes-lab02-pins-v1", "sample_interval_s": spacing,
            "sample_count": len(times), "start_s": times[0], "end_s": times[-1],
            "signals": signals,
            "interpretation": "Sampled GPIO levels, not CPU execution. Incomplete first/last widths excluded."}


def plot(report, destination):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(len(report["signals"]), 1, figsize=(11, 2*len(report["signals"])+1),
                             sharex=True, squeeze=False, layout="constrained")
    for ax, (pin, signal) in zip(axes[:, 0], report["signals"].items()):
        edges = signal["edges"]
        initial = signal["initial_level"]
        # Only edges are needed to draw a sampled digital waveform.
        xs = [report["start_s"], *[e["time_s"] for e in edges], report["end_s"]]
        ys = [initial, *[e["level"] for e in edges], edges[-1]["level"] if edges else initial]
        ax.step(xs, ys, where="post")
        ax.set_ylabel(f"GP{pin}\nch{signal['channel']}")
        ax.set_yticks([0, 1], ["LOW", "HIGH"])
        ax.set_ylim(-.2, 1.2)
        ax.grid(axis="x", alpha=.2)
    axes[-1, 0].set_xlabel("Time from capture origin (s)")
    fig.suptitle(f"Sampled GPIO signals — sample interval {report['sample_interval_s']*1e6:g} µs")
    fig.savefig(destination, dpi=160)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("capture", type=Path)
    parser.add_argument("--pins", nargs="+", type=int, default=[16, 17])
    parser.add_argument("--json", type=Path)
    parser.add_argument("--plot", type=Path)
    args = parser.parse_args()
    try:
        raw = args.capture.read_bytes()
        report = analyze(raw.decode(), args.pins)
        report.update(source=str(args.capture), source_sha256=hashlib.sha256(raw).hexdigest())
        for pin, signal in report["signals"].items():
            print(f"GP{pin}: {len(signal['edges'])} transitions; "
                  f"median adjacent-transition interval={signal['median_transition_interval_s']} s; "
                  f"full rising-to-rising period={signal['median_full_period_s']} s")
        if args.json:
            args.json.write_text(json.dumps(report, indent=2) + "\n")
        if args.plot:
            plot(report, args.plot)
    except (OSError, UnicodeError, ValueError, ImportError) as exc:
        parser.exit(2, f"capture rejected: {exc}\n")


if __name__ == "__main__":
    main()
