"""Tests for the table and the result parsing of run_series. No game."""

import json
import unittest

import runlib_path  # noqa: F401
from runlib.series import build_row, format_table, parse_run_line, run_series, tally

LINE = r"20261010-0600-ab12 pass reason=- summary=C:\runs\20261010-0600-ab12\summary.json"


class ParseTest(unittest.TestCase):
    def test_parses_the_last_result_line(self):
        parsed = parse_run_line("noise\n" + LINE + "\n")
        self.assertEqual(parsed["run_id"], "20261010-0600-ab12")
        self.assertEqual(parsed["verdict"], "pass")
        self.assertTrue(parsed["summary"].endswith("summary.json"))

    def test_reason_with_spaces(self):
        parsed = parse_run_line("r1 fail reason=the scenario failed its assertions summary=x.json")
        self.assertEqual(parsed["reason"], "the scenario failed its assertions")

    def test_no_line(self):
        self.assertIsNone(parse_run_line("Traceback ..."))


class RowTest(unittest.TestCase):
    def read_text(self, boot_seconds):
        return lambda path, encoding=None: json.dumps({"boot": {"seconds": boot_seconds}})

    def test_good_row(self):
        row = build_row(1, 0, 61.234, LINE, read_text=self.read_text(33.1))
        self.assertEqual(
            (row["verdict"], row["exit"], row["total_s"], row["boot_s"], row["reason"]), ("pass", 0, 61.2, 33.1, None)
        )

    def test_unreadable_summary(self):
        def missing(path, encoding=None):
            raise FileNotFoundError(path)

        row = build_row(1, 0, 1, LINE, read_text=missing)
        self.assertIn("not readable", row["reason"])

    def test_no_result_line_is_a_harness_error(self):
        row = build_row(2, 4, 1, "boom")
        self.assertEqual(row["verdict"], "harness_error")
        self.assertIn("boom", row["reason"])


class TableTest(unittest.TestCase):
    def test_table_and_tally(self):
        rows = [
            {"n": 1, "run_id": "a", "verdict": "pass", "exit": 0, "total_s": 60.0, "boot_s": 33.0, "reason": None},
            {"n": 2, "run_id": "b", "verdict": "fail", "exit": 1, "total_s": 5.5, "boot_s": None, "reason": "x"},
        ]
        lines = format_table(rows).splitlines()
        self.assertEqual(len(lines), 3)
        self.assertTrue(lines[0].startswith("n"))
        self.assertIn("fail", lines[2])
        self.assertEqual(tally(rows), {"pass": 1, "fail": 1})

    def test_empty_table(self):
        self.assertEqual(len(format_table([]).splitlines()), 1)


class SeriesTest(unittest.TestCase):
    def test_runs_the_launcher_count_times(self):
        calls = []

        def fake_run(run_py, scenario, extra):
            calls.append((scenario, extra))
            return 0, LINE

        ticks = iter(range(0, 100, 5))  # two clock reads per run: the start and the end
        rows = run_series("run.py", "smoke", 3, ["--max-runs", "9"], run_once=fake_run, clock=lambda: next(ticks))
        self.assertEqual(len(rows), 3)
        self.assertEqual(calls, [("smoke", ["--max-runs", "9"])] * 3)
        self.assertEqual({row["total_s"] for row in rows}, {5.0})


if __name__ == "__main__":
    unittest.main()
