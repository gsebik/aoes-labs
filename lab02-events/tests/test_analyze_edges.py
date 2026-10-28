import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location(
    "edge_analysis", Path(__file__).parents[1] / "analyze_edges.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
analyze = module.analyze


class EdgeAnalysisTests(unittest.TestCase):
    def log(self, status="status,200000,1,0,0,0"):
        return ["edge,1000,14,0,0", "edge,1100,14,1,100",
                "edge,1200,14,0,100", "edge,100000,14,1,98800", status]

    def test_separate_press_and_release(self):
        report = analyze(self.log())
        self.assertEqual(report["summary"]["press"]["observed_span_us"]["max"], 200)
        self.assertEqual(report["summary"]["release"]["observed_span_us"]["max"], 0)
        self.assertEqual(report["summary"]["press"]["edge_count"]["max"], 3)

    def test_incomplete_last_cluster_excluded(self):
        result = analyze(self.log("status,110000,1,0,0,0"))
        self.assertTrue(result["incomplete_final_cluster_excluded"])
        self.assertEqual(result["summary"]["release"]["clusters"], 0)

    def test_loss_rejected(self):
        with self.assertRaises(ValueError):
            analyze(self.log("status,200000,1,0,1,0"))
        with self.assertRaises(ValueError):
            analyze(self.log("status,200000,1,0,0,1"))

    def test_loss_explicitly_retained(self):
        self.assertEqual(analyze(self.log("status,200000,1,0,2,0"),
                                 allow_loss=True)["dropped"], 2)

    def test_delayed_drain_can_follow_a_newer_status(self):
        rows = ["edge,1000,14,0,0", "status,60000,1,0,0,0",
                "edge,50000,14,1,49000", "status,200000,1,0,0,0"]
        self.assertEqual(analyze(rows)["summary"]["release"]["clusters"], 1)

    def test_final_status_must_follow_edges(self):
        with self.assertRaises(ValueError):
            analyze(["status,1000,0,0,0,0", "edge,2000,14,0,0"])

    def test_boot_banner_after_data_rejected(self):
        with self.assertRaises(ValueError):
            analyze(self.log() + ["lab02 experiment=events clock_hz=150000000"])

    def test_reset_rejected(self):
        with self.assertRaises(ValueError):
            analyze(self.log() + ["status,1,0,0,0,0"])

    def test_bad_edge_rejected(self):
        for bad in ("edge,1,14,2,0", "edge,x,14,0,0", "edge,1,14,0"):
            with self.assertRaises(ValueError):
                analyze([bad, "status,200000,0,0,0,0"])

    def test_requires_status_and_selected_pin(self):
        with self.assertRaises(ValueError):
            analyze(self.log()[:-1])
        with self.assertRaises(ValueError):
            analyze(self.log(), pin=15)

    def test_quiet_gap_changes_grouping(self):
        result = analyze(self.log(), gap_us=50)
        self.assertEqual(result["summary"]["press"]["clusters"], 2)


if __name__ == "__main__":
    unittest.main()
