#!/usr/bin/env python3
"""Compare sampled button transitions with the supplied ISR recorder marker.

GP14 is the button input; GP16 toggles after a record is stored. A gap is
reported only when exactly one sampled input edge occurred since the previous
marker. Several edges before a marker make the causal association ambiguous.
These gaps include software work and sample uncertainty, not isolated IRQ latency.

Optional UART overlay requires an explicit --uart-burst selection. Its first
record is aligned to the first marker, rather than synchronizing the clocks.
"""
import argparse
import hashlib
import json
from pathlib import Path

from analyze_pins import analyze as analyze_samples


def uart_edges(text, pin):
    """Board timestamps (us) of `edge,t_us,pin,level,delta` rows for one pin."""
    rows = []
    for number, line in enumerate(text.splitlines(), 1):
        line = line.strip()
        if line.startswith('lab02 experiment=') and rows:
            raise ValueError('Reset banner after UART data; select one run')
        if not line.startswith('edge,') or line.startswith('edge,t_us,'):
            continue
        parts = line.split(',')
        try:
            if len(parts) != 5:
                raise ValueError('Expected timestamp, pin, level and delta')
            t_us, p, level, delta = map(int, parts[1:])
            if t_us < 0 or p not in (14, 15) or level not in (0, 1) or delta < 0:
                raise ValueError('Invalid edge field')
        except ValueError as exc:
            raise ValueError(f'UART line {number}: {exc}') from exc
        if p == pin:
            if rows and t_us <= rows[-1]['t_us']:
                raise ValueError('UART timestamps repeat or move backwards')
            rows.append({'t_us': t_us, 'level': level})
    return rows


def compare(csv_text, button=14, marker=16, uart=None, cluster_gap_us=50000, uart_burst=None):
    if button == marker or cluster_gap_us <= 0:
        raise ValueError('Use distinct button/marker pins and a positive cluster gap')
    samples = analyze_samples(csv_text, [button, marker])
    physical = samples['signals'][str(button)]['edges']
    marks = samples['signals'][str(marker)]['edges']
    if not physical:
        raise ValueError(f'GP{button} has no transitions in this capture: '
                         'trigger on the button and press within the window')
    pairs = []
    previous_marker = float('-inf')
    for m in marks:
        candidates = [e for e in physical
                      if previous_marker < e['time_s'] <= m['time_s']]
        if len(candidates) == 1:
            pairs.append({'marker_s': m['time_s'],
                          'edge_s': candidates[0]['time_s'],
                          'delay_us': (m['time_s'] - candidates[0]['time_s']) * 1e6})
        previous_marker = m['time_s']
    report = {
        'schema': 'aoes-lab02-bounce-v2',
        'sample_interval_us': samples['sample_interval_s'] * 1e6,
        'window_ms': (samples['end_s'] - samples['start_s']) * 1e3,
        'physical_edges': len(physical),
        'physical_span_us': (physical[-1]['time_s'] - physical[0]['time_s']) * 1e6,
        'recorded_edges': len(marks),
        'sampled_edge_count_excess': len(physical) - len(marks),
        'unpaired_markers': len(marks) - len(pairs),
        'edge_to_marker_us': {
            'min': min((p['delay_us'] for p in pairs), default=None),
            'max': max((p['delay_us'] for p in pairs), default=None)},
        'physical': physical, 'markers': marks, 'pairs': pairs,
        'interpretation': ('Physical edges are sampled at the stated interval; edges closer '
                           'than one sample may be missed. Count differences alone do not identify '
                           'lost records. Gaps use only single-candidate sampled associations and are '
                           'not IRQ-entry latency.'),
    }
    if uart is not None:
        rows = uart_edges(uart, button)
        if not rows or not marks:
            raise ValueError('UART overlay requires edge rows and captured marker transitions')
        bursts = [[rows[0]]]
        for row in rows[1:]:
            if row['t_us'] - bursts[-1][-1]['t_us'] > cluster_gap_us:
                bursts.append([])
            bursts[-1].append(row)
        choices = ', '.join(f"{i}: {len(b)} rows at {b[0]['t_us']} us"
                            for i, b in enumerate(bursts, 1))
        if uart_burst is None:
            raise ValueError('Select --uart-burst N using your action record; candidates: ' + choices)
        if not 1 <= uart_burst <= len(bursts):
            raise ValueError('Selected UART burst is absent; candidates: ' + choices)
        burst = bursts[uart_burst - 1]
        if len(burst) != len(marks) or burst[0]['level'] != physical[0]['level']:
            raise ValueError('Selected burst count/direction disagrees with the capture')
        for before, after in zip(burst, burst[1:]):
            if after['t_us'] <= before['t_us']:
                raise ValueError('UART timestamps repeat or move backwards')
        # Translation only: differences retain the board clock's original scale.
        offset = marks[0]['time_s'] - burst[0]['t_us'] * 1e-6
        report['uart'] = [{'time_s': r['t_us'] * 1e-6 + offset, 'level': r['level'],
                           't_us': r['t_us']} for r in burst]
        report['uart_rows'] = len(burst)
        report['uart_burst'] = uart_burst
        report['uart_alignment'] = 'User-selected burst, first record aligned to first marker; not clock synchronization'
    elif uart_burst is not None:
        raise ValueError('--uart-burst requires --uart')
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
        ax.set_ylim(0, 1.3); ax.set_yticks([]); ax.set_ylabel('UART rows\naligned')
    axes[-1].set_xlabel('time from the first physical edge (µs)')
    axes[0].set_title(f"{report['physical_edges']} sampled input edges, "
                      f"{report['recorded_edges']} ISR marker toggles")
    fig.savefig(destination, dpi=150)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('csv', type=Path, help='la cap CSV with the button and marker pins')
    parser.add_argument('--button', type=int, default=14)
    parser.add_argument('--marker', type=int, default=16)
    parser.add_argument('--uart', type=Path, help='Optional UART log; requires --uart-burst')
    parser.add_argument('--uart-burst', type=int, help='1-based burst selected from the action record')
    parser.add_argument('--json', type=Path)
    parser.add_argument('--plot', type=Path)
    args = parser.parse_args()
    try:
        report = compare(args.csv.read_text(), args.button, args.marker,
                         args.uart.read_text(errors='replace') if args.uart else None,
                         uart_burst=args.uart_burst)
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    report['source_csv_sha256'] = hashlib.sha256(args.csv.read_bytes()).hexdigest()
    if args.uart:
        report['source_uart_sha256'] = hashlib.sha256(args.uart.read_bytes()).hexdigest()
    gaps = report['edge_to_marker_us']
    gap_text = ('n/a' if gaps['min'] is None
                else f"{gaps['min']:.1f}–{gaps['max']:.1f} us")
    print(f"{args.csv.name}: {report['physical_edges']} sampled input edges over "
          f"{report['physical_span_us']:.1f} us; {report['recorded_edges']} marker toggles; "
          f"single-candidate sampled gaps {gap_text}; "
          f"unpaired markers={report['unpaired_markers']} "
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
