"""Physical edges against ISR marker toggles, on a synthetic capture."""
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from analyze_bounce import compare, uart_edges


def capture(button, marker, dt=1e-6):
    rows = ['time_s,ch12,ch14']
    for i, (b, m) in enumerate(zip(button, marker)):
        rows.append(f'{i * dt:.9f},{b},{m}')
    return '\n'.join(rows) + '\n'


class BounceTests(unittest.TestCase):
    def test_counts_and_delays(self):
        # Button: 1 -> 0 at 10, -> 1 at 20, -> 0 at 30. Marker toggles at 12 and 33 only.
        button = [1] * 10 + [0] * 10 + [1] * 10 + [0] * 20
        marker = [0] * 12 + [1] * 21 + [0] * 17
        r = compare(capture(button, marker))
        self.assertEqual(r['physical_edges'], 3)
        self.assertEqual(r['recorded_edges'], 2)
        self.assertEqual(r['sampled_edge_count_excess'], 1)
        self.assertAlmostEqual(r['edge_to_marker_us']['min'], 2.0, places=3)
        self.assertAlmostEqual(r['edge_to_marker_us']['max'], 2.0, places=3)
        self.assertEqual(r['unpaired_markers'], 1)

    def test_uart_burst_requires_explicit_selection(self):
        button = [1] * 10 + [0] * 10 + [1] * 10 + [0] * 20
        marker = [0] * 12 + [1] * 10 + [0] * 28
        log = '\n'.join(['edge,1000,14,0,0', 'edge,1050,14,1,50',      # other press
                         'edge,900000,14,0,0', 'edge,900010,14,1,10',  # this press
                         'edge,900020,15,0,0'])
        with self.assertRaisesRegex(ValueError, 'Select --uart-burst'):
            compare(capture(button, marker), uart=log)
        r = compare(capture(button, marker), uart=log, uart_burst=2)
        self.assertEqual([u['t_us'] for u in r['uart']], [900000, 900010])

    def test_marker_without_input_edge_is_not_paired_again(self):
        button = [1] * 10 + [0] * 40
        marker = [0] * 12 + [1] * 8 + [0] * 30
        result = compare(capture(button, marker))
        self.assertEqual(len(result['pairs']), 1)
        self.assertEqual(result['unpaired_markers'], 1)

    def test_inconsistent_uart_burst_is_rejected(self):
        button = [1] * 10 + [0] * 40
        marker = [0] * 12 + [1] * 38
        log = 'edge,100,14,0,0\nedge,110,14,1,10'
        with self.assertRaisesRegex(ValueError, 'count/direction'):
            compare(capture(button, marker), uart=log, uart_burst=1)

    def test_malformed_or_reset_uart_is_rejected(self):
        for text in ('edge,broken', 'edge,1,14,2,0',
                     'edge,100,14,0,0\nedge,50,14,1,0',
                     'edge,100,14,0,0\nlab02 experiment=events'):
            with self.subTest(text=text), self.assertRaises(ValueError):
                uart_edges(text, 14)

    def test_uart_rows_filter_pin(self):
        rows = uart_edges('edge,1,14,0,0\nedge,2,15,1,0\nbutton,x\n', 14)
        self.assertEqual(rows, [{'t_us': 1, 'level': 0}])


if __name__ == '__main__':
    unittest.main()
