import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).parents[1]

def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

timing = load('analyze_timing')
legacy = load('legacy_timing')
pins = load('analyze_pins')

HEADER = 'window mode=r half_period_us=500000 busy_iterations=5 work_us=0 callback_enabled=1\n'
def row(elapsed=1000100, main=2, irq=2, phase=100, work=0):
    return (f'timing,mode=r,elapsed_us={elapsed},main_count={main},main_phase_us={phase},'
            f'irq_count={irq},irq_phase_us=5,work_us={work},work_elapsed_us={work}\n')

class TimingTests(unittest.TestCase):
    def test_last_announced_window_is_explicit(self):
        report = legacy.analyze('monitor banner\n' + HEADER + row() + HEADER + row(2000200, 4, 4, 200))
        self.assertEqual(report['selected_window'], 2)
        self.assertEqual(report['summary']['main']['final_phase_us'], 200)
        self.assertEqual(len(report['rows']), 1)  # never invent intervening edges
        self.assertEqual(legacy.analyze(HEADER+row()+HEADER+row(), 1)['selected_window'], 1)

    def test_bad_or_inconsistent_records_fail(self):
        for data in (row(), HEADER, HEADER+'timing,garbled\n', HEADER+row(work=20),
                     HEADER+row()+row(100, 1, 1)):
            with self.subTest(data=data), self.assertRaises(ValueError):
                legacy.analyze(data)

    def test_negative_phase_is_valid(self):
        self.assertEqual(legacy.analyze(HEADER+row(phase=-3))['summary']['main']['final_phase_us'], -3)

    def test_disabled_callback_is_not_drawn_as_zero_latency(self):
        report = legacy.analyze(HEADER.replace('enabled=1', 'enabled=0')+row(irq=0))
        self.assertIsNone(report['summary']['irq']['final_phase_us'])

    def test_observed_points_plot(self):
        try:
            import matplotlib
        except ImportError:
            self.skipTest('optional matplotlib unavailable')
        report = legacy.analyze(HEADER + row() + row(2000200,4,4,200))
        report['label'] = 'synthetic parser fixture, not board data'
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)/'plot.svg'
            legacy.plot([report], output)
            self.assertIn('<svg', output.read_text())

class PinTests(unittest.TestCase):
    CSV = 'time_s,ch14,ch15\n0,0,0\n0.1,1,0\n0.2,1,1\n0.3,0,1\n0.4,0,0\n0.5,1,0\n0.6,1,1\n'
    def test_toggle_interval_and_full_period_differ(self):
        report = pins.analyze(self.CSV, [16,17])
        signal = report['signals']['16']
        self.assertAlmostEqual(signal['median_transition_interval_s'], .2)
        self.assertAlmostEqual(signal['median_full_period_s'], .4)
        self.assertEqual(len(signal['complete_widths']), 2)
        self.assertAlmostEqual(report['sample_interval_s'], .1)

    def test_missing_channel_nonuniform_and_invalid_values_fail(self):
        for data, selected in ((self.CSV,[12]), (self.CSV.replace('0.3,','0.31,'),[16]),
                                (self.CSV.replace('0.1,1','0.1,2'),[16]),
                                (self.CSV.replace('0.1,','nan,'),[16])):
            with self.subTest(data=data), self.assertRaises(ValueError):
                pins.analyze(data, selected)

    def test_channel_mapping_includes_upper_inputs(self):
        self.assertEqual(pins.channel(16),14)
        self.assertEqual(pins.channel(28),23)
        with self.assertRaises(ValueError): pins.channel(23)

class DirectLEDLogTests(unittest.TestCase):
    def test_relative_edges_give_interval_and_drift(self):
        result=timing.analyze('led,relative,500,20,1,500000\nled,relative,500,20,2,1020000\n')
        self.assertEqual(result['schema'],'aoes-led-transitions-v1')
        self.assertEqual(result['summary']['main']['final_phase_us'],20000)
        self.assertEqual(result['summary']['interval']['median_us'],520000)
    def test_callback_count_is_not_a_timestamp(self):
        result=timing.analyze('led,interrupt,500,650,1,500000,1\nled,interrupt,500,650,2,1150000,2\n')
        self.assertEqual(result['summary']['irq']['final_count'],2)
        self.assertIsNone(result['summary']['irq']['final_phase_us'])
    def test_bad_reset_or_changed_settings_are_rejected(self):
        for data in ('led,relative,500,0,1,bad\n',
                     'led,relative,500,0,2,1000000\nled,relative,500,0,1,500000\n',
                     'led,relative,500,0,1,500000\nled,relative,500,20,2,1020000\n'):
            with self.subTest(data=data),self.assertRaises(ValueError):timing.analyze(data)
    def test_start_marker_excludes_stale_bridge_data(self):
        result=timing.analyze('led,relative,500,0,9,4500000\nstart,absolute\nled,absolute,500,20,1,500001\n')
        self.assertEqual(result['settings']['experiment'],'absolute')
        self.assertEqual(len(result['rows']),1)

    def test_missing_transition_does_not_invent_an_interval(self):
        result = timing.analyze('led,absolute,500,0,1,500001\nled,absolute,500,0,3,1500001\n')
        self.assertEqual(result['summary']['interval']['count'], 0)
        self.assertIsNone(result['summary']['interval']['median_us'])

    def test_current_transition_comparison_plot(self):
        try:
            import matplotlib
        except ImportError:
            self.skipTest('optional matplotlib unavailable')
        reports = []
        for kind, work, second in [('relative', 20, 1020000), ('interrupt', 650, 1150000)]:
            suffix = ',1' if kind == 'interrupt' else ''
            suffix2 = ',2' if kind == 'interrupt' else ''
            text = (f'led,{kind},500,{work},1,500000{suffix}\n'
                    f'led,{kind},500,{work},2,{second}{suffix2}\n')
            report = timing.analyze(text)
            report['label'] = kind + ' synthetic fixture, not board data'
            reports.append(report)
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'comparison.svg'
            timing.plot(reports, output)
            self.assertIn('Timer callback progress observed by main', output.read_text())
