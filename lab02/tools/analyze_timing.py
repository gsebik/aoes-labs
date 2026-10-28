#!/usr/bin/env python3
"""Read LED transition logs, calculate timing differences, and save comparison plots."""
import argparse
import hashlib
import json
from pathlib import Path
import re
from statistics import median


def analyze(text):
    """Read per-transition records from the independent main.c exercises."""
    rows = []
    settings = None
    for number, raw in enumerate(text.splitlines(), 1):
        line = re.sub(r"\x1b\[[0-9;]*[A-Za-z]", "", raw).strip()
        if any(marker in line for marker in ("start,relative", "start,absolute", "start,interrupt")):
            rows = []
            settings = None
            continue
        if not line.startswith("led,"):
            continue
        parts = line.split(",")
        try:
            kind = parts[1]
            if kind not in ("relative", "absolute", "interrupt"):
                raise ValueError("Unknown experiment")
            if len(parts) != (7 if kind == "interrupt" else 6):
                raise ValueError("Incomplete transition record")
            period_ms, work_ms, count, elapsed_us = map(int, parts[2:6])
            irq_count = int(parts[6]) if kind == "interrupt" else None
            current = {"experiment": kind, "period_ms": period_ms, "work_ms": work_ms}
            if period_ms <= 0 or work_ms < 0 or count <= 0 or elapsed_us < 0:
                raise ValueError("Invalid interval, count or timestamp")
            if settings is not None and current != settings:
                raise ValueError("Settings changed; use a separate file for each build")
            if rows and (count <= rows[-1]["main_count"] or elapsed_us <= rows[-1]["elapsed_us"]):
                raise ValueError("Reset/repeated record; use a fresh capture file")
            if irq_count is not None and (irq_count < 0 or
                    (rows and irq_count < rows[-1]["irq_count"])):
                raise ValueError("Callback count moved backwards")
            settings = current
            rows.append({"main_count": count, "elapsed_us": elapsed_us,
                         "main_phase_us": elapsed_us - count * period_ms * 1000,
                         "irq_count": irq_count})
        except (IndexError, ValueError) as exc:
            raise ValueError(f"Line {number}: invalid LED record ({exc})") from exc
    if not rows:
        raise ValueError("No LED transitions: finish the timing statement and retain UART output")
    phases = [r["main_phase_us"] for r in rows]
    # A gap in transition numbers means an interval was not completely recorded.
    intervals = [(b["elapsed_us"] - a["elapsed_us"])
                 for a, b in zip(rows, rows[1:])
                 if b["main_count"] == a["main_count"] + 1]
    interval_summary = ({"count": len(intervals), "min_us": min(intervals),
                         "median_us": median(intervals), "max_us": max(intervals)}
                        if intervals else {"count": 0, "min_us": None,
                                           "median_us": None, "max_us": None})
    return {"schema": "aoes-led-transitions-v1", "settings": settings, "rows": rows,
            "windows_in_file": 1, "selected_window": 1,
            "observation_end_us": rows[-1]["elapsed_us"],
            "summary": {"interval": interval_summary, "main": {"final_count": rows[-1]["main_count"],
                "final_phase_us": phases[-1], "observed_min_phase_us": min(phases),
                "observed_max_phase_us": max(phases)},
                "irq": {"final_count": rows[-1]["irq_count"], "final_phase_us": None}},
            "interpretation": "Main timestamps follow GP16 transitions. Timer counts have no per-IRQ timestamps; use pin captures for GP17 intervals."}


def plot(reports, destination):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    has_irq = any(r["settings"]["experiment"] == "interrupt" for r in reports)
    fig, axes = plt.subplots(3 if has_irq else 2, 1, figsize=(11, 9 if has_irq else 7),
                             sharex=True, layout="constrained")
    for report in reports:
        rows = report["rows"]
        xs = [r["elapsed_us"] / 1e6 for r in rows]
        axes[0].plot(xs, [r["main_phase_us"]/1000 for r in rows], ".-", label=report["label"])
        pairs = [(a,b) for a,b in zip(rows, rows[1:]) if b["main_count"] == a["main_count"]+1]
        axes[1].plot([b["elapsed_us"]/1e6 for a,b in pairs],
                     [(b["elapsed_us"]-a["elapsed_us"])/1000 for a,b in pairs],
                     ".-", label=report["label"])
        if has_irq and report["settings"]["experiment"] == "interrupt":
            axes[2].step(xs, [r["irq_count"] for r in rows], where="post", label=report["label"])
    axes[0].set_title("GP16 phase: recorded transition versus its intended schedule")
    axes[0].set_ylabel("Phase error (ms)")
    axes[1].set_title("GP16: time between consecutive recorded transitions")
    axes[1].set_ylabel("Interval (ms)")
    if has_irq:
        axes[2].set_title("Timer callback progress observed by main (not callback timestamps)")
        axes[2].set_ylabel("Callback count")
    for ax in axes:
        ax.grid(alpha=.2)
        if ax.lines: ax.legend(fontsize=8)
    axes[-1].set_xlabel("Elapsed board time (s)")
    fig.savefig(destination, dpi=160)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("captures", nargs="+", type=Path, help="One UART log per run")
    parser.add_argument("--json", type=Path, help="Save decoded rows and calculated results")
    parser.add_argument("--plot", type=Path, help="Save PNG or SVG; open it separately with xdg-open")
    args = parser.parse_args()
    try:
        reports = []
        for source in args.captures:
            raw = source.read_bytes()
            result = analyze(raw.decode())
            result.update(label=source.stem, source=str(source),
                          source_sha256=hashlib.sha256(raw).hexdigest())
            reports.append(result)
            settings = result["settings"]
            intervals = result["summary"]["interval"]
            interval_text = (f"{intervals['median_us']/1000:.3f} ms"
                             if intervals["count"] else "not enough consecutive records")
            print(f"{source.stem}: {len(result['rows'])} transitions, "
                  f"requested={settings['period_ms']} ms, work={settings['work_ms']} ms; "
                  f"median interval={interval_text}")
        if args.json:
            args.json.write_text(json.dumps({"captures": reports}, indent=2) + "\n")
            print(f"Saved decoded results: {args.json}")
        if args.plot:
            plot(reports, args.plot)
            print(f"Saved plot: {args.plot} (open this file to view it)")
    except (OSError, UnicodeError, ValueError, ImportError) as exc:
        parser.exit(2, f"analysis failed: {exc}\n")


if __name__ == "__main__":
    main()
