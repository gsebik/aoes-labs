#!/usr/bin/env python3
"""Decode a complete aoes-timing-v1 UART run; no board control or pass threshold."""
import argparse
import json
from pathlib import Path
import statistics

CASES = ('empty_bracket', 'gpio_xor_mask', 'gpio_put', 'sio_xor_write',
         'timer_callback_period', 'adc_read')


def decode(text, selected_run=None):
    runs = {}
    completed = []
    for number, line in enumerate(text.splitlines(), 1):
        if not line.startswith(('@@BEGIN ', '@@SAMPLE ', '@@END ', '@@ABORT ')):
            continue
        try:
            kind, *tokens = line.split()
            fields = dict(token.split('=', 1) for token in tokens)
            run_id = int(fields['run'])
            if kind == '@@BEGIN':
                if run_id in runs:
                    raise ValueError('repeated run ID; start a separate capture after reset')
                if fields['schema'] != 'aoes-timing-v1':
                    raise ValueError('unsupported timing schema')
                clock = int(fields['clock_hz'])
                count = int(fields['n'])
                if clock <= 0 or not 0 < count <= 100000:
                    raise ValueError('invalid clock or sample count')
                runs[run_id] = {'metadata': fields, 'samples': {c: {} for c in CASES},
                                'aborted': False}
            elif run_id not in runs:
                # A capture may start in the middle of an earlier run.
                continue
            elif kind == '@@ABORT':
                runs[run_id]['aborted'] = True
            elif kind == '@@SAMPLE':
                run = runs[run_id]
                case = fields['case']
                index = int(fields['index'])
                cycles = int(fields['cycles'])
                if case not in CASES or not 0 <= cycles <= 0xffffffff:
                    raise ValueError('invalid case or cycle count')
                if not 0 <= index < int(run['metadata']['n']):
                    raise ValueError('sample index outside declared window')
                if index in run['samples'][case]:
                    raise ValueError('duplicate sample')
                run['samples'][case][index] = cycles
            elif kind == '@@END':
                run = runs[run_id]
                count = int(run['metadata']['n'])
                if not run['aborted'] and all(len(v) == count for v in run['samples'].values()):
                    completed.append(run_id)
        except (KeyError, ValueError) as exc:
            raise ValueError(f'line {number}: {exc}') from exc
    if selected_run is None:
        if not completed:
            raise ValueError('no complete run: retain @@BEGIN, all six cases and @@END')
        selected_run = completed[-1]
    if selected_run not in completed:
        raise ValueError(f'run {selected_run} is absent, aborted or incomplete')
    run = runs[selected_run]
    clock = int(run['metadata']['clock_hz'])
    output = {'schema': 'aoes-timing-v1', 'metadata': run['metadata'], 'cases': {}}
    for case, indexed in run['samples'].items():
        values = [indexed[i] for i in range(len(indexed))]
        output['cases'][case] = {
            'cycles': values, 'n': len(values),
            'min_cycles': min(values), 'mean_cycles': statistics.fmean(values),
            'max_cycles': max(values), 'sd_cycles': statistics.pstdev(values),
            'mean_us': statistics.fmean(values) * 1000000.0 / clock,
        }
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('capture', type=Path)
    parser.add_argument('--run', type=int, help='select a complete run; default: last complete')
    parser.add_argument('-o', '--output', type=Path, help='write JSON; default: standard output')
    args = parser.parse_args()
    try:
        output = decode(args.capture.read_text(), args.run)
    except (OSError, ValueError) as exc:
        parser.exit(1, f'{exc}\n')
    result = json.dumps(output, indent=2) + '\n'
    if args.output:
        args.output.write_text(result)
    else:
        print(result, end='')


if __name__ == '__main__':
    main()
