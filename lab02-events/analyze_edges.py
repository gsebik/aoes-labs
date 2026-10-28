#!/usr/bin/env python3
"""Group software-observed edges; never infer a physical WCET/bounce bound."""
import argparse
from collections import Counter
import json
from pathlib import Path
from statistics import median


def analyze(lines, gap_us=50000, pin=14, allow_loss=False):
    if gap_us <= 0 or pin not in (14, 15):
        raise ValueError("Use a positive quiet gap and pin 14 or 15")
    edges, statuses = [], []
    last_time = {"edge": -1, "status": -1}
    for number, line in enumerate(lines, 1):
        line = line.strip()
        if line.startswith("lab02 experiment=") and (edges or statuses):
            raise ValueError("Reset banner after data: use one capture per reset")
        if line.startswith("edge,t_us,"):
            continue
        if not line.startswith(("edge,", "status,")):
            continue
        parts = line.split(",")
        try:
            values = [int(x) for x in parts[1:]]
        except ValueError as exc:
            raise ValueError(f"Line {number}: malformed numeric record") from exc
        if any(x < 0 for x in values):
            raise ValueError(f"Line {number}: negative record field")
        stream = parts[0]
        if not values or values[0] < last_time[stream]:
            raise ValueError("Timestamp moved backwards: use one capture per reset")
        last_time[stream] = values[0]
        if parts[0] == "edge":
            if len(values) != 4 or values[1] not in (14, 15) or values[2] not in (0, 1):
                raise ValueError(f"Line {number}: invalid edge record")
            if values[1] == pin:
                edges.append({"t_us": values[0], "level": values[2]})
        else:
            if len(values) != 5:
                raise ValueError(f"Line {number}: invalid status record")
            statuses.append(values)
    if not edges or not statuses:
        raise ValueError("Retain edges for the selected pin and at least one status line")
    lost = max(s[3] for s in statuses)
    ambiguous = max(s[4] for s in statuses)
    if (lost or ambiguous) and not allow_loss:
        raise ValueError("Loss counters increased: preserve this run, then recapture")
    end_us = statuses[-1][0]
    if end_us < edges[-1]["t_us"]:
        raise ValueError("Retain a final status after the last edge")
    groups, group = [], []
    for edge in edges:
        if group and edge["t_us"] - group[-1]["t_us"] >= gap_us:
            groups.append(group)
            group = []
        group.append(edge)
    incomplete = bool(group and end_us - group[-1]["t_us"] < gap_us)
    if group and not incomplete:
        groups.append(group)
    clusters = [{"kind": "press" if g[-1]["level"] == 0 else "release",
                 "first_us": g[0]["t_us"], "last_us": g[-1]["t_us"],
                 "edges": len(g), "span_us": g[-1]["t_us"] - g[0]["t_us"]}
                for g in groups]
    summary = {}
    for kind in ("press", "release"):
        selected = [c for c in clusters if c["kind"] == kind]
        def stats(key):
            values = [c[key] for c in selected]
            return {"min": min(values), "median": median(values), "max": max(values)} \
                if values else None
        summary[kind] = {"clusters": len(selected), "edge_count": stats("edges"),
                         "observed_span_us": stats("span_us"),
                         "edge_histogram": dict(Counter(c["edges"] for c in selected))}
    return {"schema": "aoes-lab02-edges-v1", "pin": pin, "gap_us": gap_us,
            "last_status_us": end_us, "dropped": lost, "ambiguous": ambiguous,
            "incomplete_final_cluster_excluded": incomplete,
            "summary": summary, "clusters": clusters, "edges": edges,
            "interpretation": "Software-observed clusters; no physical worst-case bound"}


def plot(report, destination):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(3, 1, figsize=(11, 8), layout="constrained")
    edges = report["edges"]
    origin = edges[0]["t_us"]
    axes[0].step([(e["t_us"]-origin)/1e6 for e in edges],
                 [e["level"] for e in edges], where="post")
    axes[0].set_ylabel("Observed level")
    axes[0].set_xlabel("Time since first software observation (s)")
    axes[0].set_title(f"GP{report['pin']} — ISR observations; physical edges may be missed")
    for kind, color in (("press", "#2778a5"), ("release", "#b46c24")):
        clusters = [c for c in report["clusters"] if c["kind"] == kind]
        if clusters:
            axes[1].hist([c["span_us"]/1000 for c in clusters], bins="auto", alpha=.5,
                         label=kind, color=color)
            counts = report["summary"][kind]["edge_histogram"]
            axes[2].plot(list(counts), list(counts.values()), "o", label=kind, color=color)
    axes[1].set_xlabel("Observed cluster span (ms)")
    axes[1].set_ylabel("Clusters")
    axes[2].set_xlabel("Observed edges per cluster")
    axes[2].set_ylabel("Clusters")
    for ax in axes[1:]:
        ax.legend()
        ax.grid(alpha=.2)
    fig.savefig(destination, dpi=160)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("capture", type=Path)
    parser.add_argument("--gap-ms", type=float, default=50)
    parser.add_argument("--pin", type=int, default=14)
    parser.add_argument("--allow-loss", action="store_true")
    parser.add_argument("--json", type=Path)
    parser.add_argument("--plot", type=Path, help="Save PNG or SVG; requires matplotlib")
    args = parser.parse_args()
    try:
        report = analyze(args.capture.read_text().splitlines(),
                         int(args.gap_ms * 1000), args.pin, args.allow_loss)
        if args.plot:
            plot(report, args.plot)
    except (OSError, ValueError, OverflowError, ImportError) as exc:
        parser.exit(2, f"capture rejected: {exc}\n")
    output = json.dumps(report, indent=2)
    if args.json:
        args.json.write_text(output + "\n")
    print(output)


if __name__ == "__main__":
    main()
