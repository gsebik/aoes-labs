#!/usr/bin/env python3
"""Compare a button's physical edges with the edges the ISR recorded.

One analyzer capture of one press or release, with two channels:

* the button pin (GP14 for K1): every physical transition, at the sample rate;
* the ISR marker (GP16): the recorder toggles it once per edge it stores.

    analyze_bounce.py press-01.csv [--uart edges.log] [--json out.json] [--plot out.png]

The tool counts both, pairs each recorded edge with the latest physical edge
before it, and reports the delay from that edge to the marker. With --uart it
also draws the board's own `edge` timestamps of the matching press (the burst
whose spacing fits the marker toggles), aligned so that the first recorded
edge coincides with the first marker toggle (the ISR takes the timestamp just
before toggling the marker, so they differ by a few instructions). The two clocks
are not otherwise synchronized; only differences inside one press are compared.
"""
import argparse
import json
from pathlib import Path

from analyze_pins import analyze as analyze_samples


def uart_edges(text, pin):
    """Board timestamps (us) of `edge,t_us,pin,level,delta` rows for one pin."""
    rows = []
    for line in text.splitlines():
        parts = line.strip().split(',')
        if len(parts) == 5 and parts[0] == 'edge':
            try:
                t_us, p, level = int(parts[1]), int(parts[2]), int(parts[3])
            except ValueError:
                continue
            if p == pin:
                rows.append({'t_us': t_us, 'level': level})
    return rows


def compare(csv_text, button=14, marker=16, uart=None, cluster_gap_us=50000):
    samples = analyze_samples(csv_text, [button, marker])
    physical = samples['signals'][str(button)]['edges']
    marks = samples['signals'][str(marker)]['edges']
    if not physical:
        raise ValueError(f'GP{button} has no transitions in this capture: '
                         'trigger on the button and press within the window')
    pairs = []
    for m in marks:
        before = [e for e in physical if e['time_s'] <= m['time_s']]
        if before:
            pairs.append({'marker_s': m['time_s'],
                          'edge_s': before[-1]['time_s'],
                          'delay_us': (m['time_s'] - before[-1]['time_s']) * 1e6})
    report = {
        'schema': 'aoes-lab02-bounce-v1',
        'sample_interval_us': samples['sample_interval_s'] * 1e6,
        'window_ms': (samples['end_s'] - samples['start_s']) * 1e3,
        'physical_edges': len(physical),
        'physical_span_us': (physical[-1]['time_s'] - physical[0]['time_s']) * 1e6,
        'recorded_edges': len(marks),
        'not_recorded': max(0, len(physical) - len(marks)),
        'edge_to_marker_us': {
            'min': min((p['delay_us'] for p in pairs), default=None),
            'max': max((p['delay_us'] for p in pairs), default=None)},
        'physical': physical, 'markers': marks, 'pairs': pairs,
        'interpretation': ('Physical edges are sampled at the stated interval; edges closer '
                           'than one sample are invisible to the analyzer as well.'),
    }
    if uart is not None:
        rows = uart_edges(uart, button)
        if rows and marks:
            # Split the rows into bursts and take the latest one that starts with the
            # same direction as the captured physical edge (press or release).
            bursts = [[rows[0]]]
            for r in rows[1:]:
                if r['t_us'] - bursts[-1][-1]['t_us'] > cluster_gap_us:
                    bursts.append([])
                bursts[-1].append(r)
            # Several presses may be in the log: pick the burst whose spacing
            # matches the marker toggles of this capture best.
            mgaps = [(b['time_s'] - a['time_s']) * 1e6 for a, b in zip(marks, marks[1:])]

            def mismatch(b):
                gaps = [y['t_us'] - x['t_us'] for x, y in zip(b, b[1:])]
                n = min(len(gaps), len(mgaps))
                return (abs(len(b) - len(marks)), sum(abs(g - m) for g, m in zip(gaps[:n], mgaps[:n])))
            matching = [b for b in bursts if b[0]['level'] == physical[0]['level']] or bursts
            burst = min(matching, key=mismatch)
            offset = marks[0]['time_s'] - burst[0]['t_us'] * 1e-6
            report['uart'] = [{'time_s': r['t_us'] * 1e-6 + offset, 'level': r['level'],
                               't_us': r['t_us']} for r in burst]
            report['uart_rows'] = len(burst)
    return report


def plot(report, destination, button=14, marker=16):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    rows = 3 if 'uart' in report else 2
    fig, axes = plt.subplots(rows, 1, figsize=(11, 1.6 * rows + 1.2), sharex=True,
                             layout='constrained')
    t0 = report['physical'][0]['time_s']
    us = lambda t: (t - t0) * 1e6

    def draw(ax, edges, label, colour):
        if not edges:
            ax.set_ylabel(label); return
        level = 1 - edges[0]['level']
        xs, ys = [us(edges[0]['time_s']) - 50], [level]
        for e in edges:
            xs += [us(e['time_s']), us(e['time_s'])]
            ys += [ys[-1], e['level']]
        xs.append(us(edges[-1]['time_s']) + 50); ys.append(ys[-1])
        ax.plot(xs, ys, color=colour, linewidth=1.4)
        ax.set_ylim(-0.3, 1.3); ax.set_yticks([0, 1]); ax.set_ylabel(label)

    draw(axes[0], report['physical'], f'GP{button}\nbutton pin', '#2563eb')
    for e in report['physical']:
        axes[0].axvline(us(e['time_s']), color='#2563eb', alpha=0.15)
    draw(axes[1], report['markers'], f'GP{marker}\nISR marker', '#16a34a')
    for p in report['pairs']:
        axes[1].annotate('', xy=(us(p['marker_s']), 0.5), xytext=(us(p['edge_s']), 0.5),
                         arrowprops=dict(arrowstyle='->', color='#64748b'))
    if 'uart' in report:
        ax = axes[2]
        for r in report['uart']:
            ax.vlines(us(r['time_s']), 0, 1, color='#b45309')
            ax.text(us(r['time_s']), 1.05, str(r['level']), ha='center', fontsize=8)
        ax.set_ylim(0, 1.3); ax.set_yticks([]); ax.set_ylabel('UART edge\nrows')
    axes[-1].set_xlabel('time from the first physical edge (µs)')
    axes[0].set_title(f"{report['physical_edges']} physical edges, "
                      f"{report['recorded_edges']} recorded by the ISR")
    fig.savefig(destination, dpi=150)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('csv', type=Path, help='la cap CSV with the button and marker pins')
    parser.add_argument('--button', type=int, default=14)
    parser.add_argument('--marker', type=int, default=16)
    parser.add_argument('--uart', type=Path, help='UART log with edge rows of the same press')
    parser.add_argument('--json', type=Path)
    parser.add_argument('--plot', type=Path)
    args = parser.parse_args()
    try:
        report = compare(args.csv.read_text(), args.button, args.marker,
                         args.uart.read_text(errors='replace') if args.uart else None)
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    d = report['edge_to_marker_us']
    print(f"{args.csv.name}: {report['physical_edges']} physical edges over "
          f"{report['physical_span_us']:.1f} us; {report['recorded_edges']} recorded "
          f"by the ISR; edge-to-marker delay "
          f"{'n/a' if d['min'] is None else f'{d['min']:.1f}–{d['max']:.1f} us'} "
          f"(sample interval {report['sample_interval_us']:.2f} us)")
    if 'uart_rows' in report:
        print(f"UART edge rows in that burst: {report['uart_rows']}")
    if args.json:
        args.json.write_text(json.dumps(report, indent=2) + '\n')
    if args.plot:
        plot(report, args.plot, args.button, args.marker)
        print(f'Saved plot: {args.plot}')


if __name__ == '__main__':
    raise SystemExit(main())
