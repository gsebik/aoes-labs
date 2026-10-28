#!/usr/bin/env python3
"""Plot recorded UART phase observations; do not reconstruct unrecorded edges."""
import argparse
import hashlib
import json
from pathlib import Path
import re


def fields(text):
    return dict(token.split("=", 1) for token in text.split())


def analyze_led(text):
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
    return {"schema": "aoes-led-transitions-v1", "settings": settings, "rows": rows,
            "windows_in_file": 1, "selected_window": 1,
            "observation_end_us": rows[-1]["elapsed_us"],
            "summary": {"main": {"final_count": rows[-1]["main_count"],
                "final_phase_us": phases[-1], "observed_min_phase_us": min(phases),
                "observed_max_phase_us": max(phases)},
                "irq": {"final_count": rows[-1]["irq_count"], "final_phase_us": None}},
            "interpretation": "Main timestamps follow GP16 transitions. Timer counts have no per-IRQ timestamps; use pin captures for GP17 intervals."}


def analyze(text, window=None):
    if any(line.strip().startswith("led,") for line in text.splitlines()):
        if window not in (None, 1):
            raise ValueError("Per-transition files contain one run; use separate files after reset")
        return analyze_led(text)
    windows = []
    current = None
    for number, raw in enumerate(text.splitlines(), 1):
        line = re.sub(r"\x1b\[[0-9;]*[A-Za-z]", "", raw).strip()
        if line.startswith("window "):
            current = {"settings": fields(line[7:]), "lines": []}
            windows.append(current)
        elif line.startswith("lab02 experiment="):
            current = None
        elif line.startswith("timing,") and current is not None:
            current["lines"].append((number, line))
    if not windows:
        raise ValueError("No window header: type n then Enter after starting the capture")
    index = len(windows) - 1 if window is None else window - 1
    if not 0 <= index < len(windows):
        raise ValueError("Selected window is absent (window numbers start at 1)")
    selected = windows[index]
    settings = selected["settings"]
    try:
        mode = settings["mode"]
        half_period = int(settings["half_period_us"])
        work = int(settings["work_us"])
        callback = int(settings["callback_enabled"])
        if mode not in "rab" or len(mode) != 1 or half_period <= 0 or work < 0 or callback not in (0, 1):
            raise ValueError("Invalid window settings")
    except (KeyError, ValueError) as exc:
        raise ValueError("Incomplete/invalid window header") from exc
    rows = []
    required = ("elapsed_us", "main_count", "main_phase_us", "irq_count",
                "irq_phase_us", "work_us", "work_elapsed_us")
    for number, line in selected["lines"]:
        try:
            raw = dict(token.split("=", 1) for token in line.split(",")[1:])
            row = {key: int(raw[key]) for key in required}
            if raw["mode"] != mode or row["work_us"] != work:
                raise ValueError("Row disagrees with window settings")
            if any(row[key] < 0 for key in required if "phase" not in key):
                raise ValueError("Negative count or elapsed duration")
            if not callback and row["irq_count"]:
                raise ValueError("IRQ count with callback disabled")
            if rows and (row["elapsed_us"] <= rows[-1]["elapsed_us"] or
                         any(row[key] < rows[-1][key] for key in ("main_count", "irq_count"))):
                raise ValueError("Time/count moved backwards; retain one reset per file")
        except (KeyError, ValueError) as exc:
            raise ValueError(f"Line {number}: invalid timing row ({exc})") from exc
        rows.append(row)
    if not rows:
        raise ValueError("Selected window has no timing rows; record beyond its header")
    summary = {}
    for path in ("main", "irq"):
        values = [r[path + "_phase_us"] for r in rows if r[path + "_count"]]
        summary[path] = {"final_count": rows[-1][path + "_count"],
                         "final_phase_us": rows[-1][path + "_phase_us"] if values else None,
                         "observed_min_phase_us": min(values) if values else None,
                         "observed_max_phase_us": max(values) if values else None}
    return {"schema": "aoes-lab02-timing-v1", "settings": settings,
            "windows_in_file": len(windows), "selected_window": index + 1,
            "observation_end_us": rows[-1]["elapsed_us"], "rows": rows,
            "summary": summary,
            "interpretation": "Phase observations at UART report times, not every GPIO edge or a worst-case bound"}


def plot_led(reports, destination):
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


def plot(reports, destination):
    if any(r["schema"] == "aoes-led-transitions-v1" for r in reports):
        if not all(r["schema"] == "aoes-led-transitions-v1" for r in reports):
            raise ValueError("Do not mix different UART log formats in one comparison")
        return plot_led(reports, destination)
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    busy = any(r["settings"]["mode"] == "b" for r in reports)
    fig, axes = plt.subplots(3 if busy else 2, 1, figsize=(11, 9 if busy else 7),
                             sharex=True, layout="constrained")
    for report in reports:
        is_busy = report["settings"]["mode"] == "b"
        foreground_ax = axes[1] if busy and is_busy else axes[0]
        for ax, path, scale in ((foreground_ax, "main", 1000), (axes[-1], "irq", 1)):
            rows = [r for r in report["rows"] if r[path + "_count"]]
            if rows:
                ax.plot([r["elapsed_us"] / 1e6 for r in rows],
                        [r[path + "_phase_us"] / scale for r in rows],
                        ".-", linewidth=1, markersize=3, label=report["label"])
    axes[0].set_title("GP16 — relative waits and absolute targets")
    axes[0].set_ylabel("Phase error (ms)")
    if busy:
        axes[1].set_title("GP16 — uncalibrated CPU-work loop (separate scale)")
        axes[1].set_ylabel("Phase error (ms)")
    axes[-1].set_title("GP17 — timer-callback observations")
    axes[-1].set_ylabel("Phase error (µs)")
    for ax in axes:
        ax.grid(alpha=.2)
        if ax.lines:
            ax.legend(fontsize=8)
    axes[-1].set_xlabel("Elapsed time at UART report (s)")
    fig.suptitle("Recorded phase observations; lines do not reconstruct intervening edges", fontsize=11)
    fig.savefig(destination, dpi=160)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("captures", nargs="+", type=Path)
    parser.add_argument("--window", type=int, help="1-based window; default last announced window per file")
    parser.add_argument("--json", type=Path)
    parser.add_argument("--plot", type=Path, help="Save PNG or SVG; requires matplotlib")
    args = parser.parse_args()
    try:
        reports = []
        for source in args.captures:
            raw = source.read_bytes()
            result = analyze(raw.decode(), args.window)
            result.update(label=source.stem, source=str(source),
                          source_sha256=hashlib.sha256(raw).hexdigest())
            reports.append(result)
            print(f"{source}: window {result['selected_window']}/{result['windows_in_file']}, "
                  f"{len(result['rows'])} reports, through {result['observation_end_us']/1e6:.3f} s; "
                  f"main phase={result['summary']['main']['final_phase_us']} us, "
                  f"callback phase={result['summary']['irq']['final_phase_us']} us")
        if args.json:
            args.json.write_text(json.dumps({"captures": reports}, indent=2) + "\n")
        if args.plot:
            plot(reports, args.plot)
    except (OSError, UnicodeError, ValueError, ImportError) as exc:
        parser.exit(2, f"analysis failed: {exc}\n")


if __name__ == "__main__":
    main()
