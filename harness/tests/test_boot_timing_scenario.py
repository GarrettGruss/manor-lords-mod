"""The test scenario boot-timing against a fake run folder (change add-boot-timing-regression-tests). No game."""

import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

import runlib_path  # noqa: F401
from runlib.expectations import Expectations
from scenarios import boot_timing

STATES = boot_timing.SAVE_STATES


def make_ctx(folder, history=STATES, state="READY", seconds=31, pause_lines=1, clock_change=0.0):
    boot = {"state": state, "slot": "saveGame_0", "started": 1000, "updated": 1000 + seconds,
            "reason": None, "history": [{"state": name, "time": 1000} for name in history]}
    (folder / "boot.json").write_text(json.dumps(boot), encoding="utf-8")
    (folder / "mod.log").write_text("[HarnessBoot] calling pauseGame\n" * pause_lines, encoding="utf-8")
    expect = Expectations(sleep=lambda s: None, monotonic=lambda: 0.0)
    metrics = {}
    return SimpleNamespace(
        run=SimpleNamespace(path=folder, boot_path=folder / "boot.json"),
        check=lambda name, ok, value=None, range=None: expect.record(name, ok, value, ""),
        check_range=expect.in_range,
        metric=lambda name, value: metrics.__setitem__(name, value),
        read_clock=lambda wait_s=3.0: {"clock": 5.0, "change": clock_change, "seconds": wait_s,
                                       "paused": abs(clock_change) < 0.001},
        result=expect.result,
    )


class BootTimingTest(unittest.TestCase):
    def run_case(self, **options):
        with tempfile.TemporaryDirectory() as tmp:
            return boot_timing.run(make_ctx(Path(tmp), **options))

    def test_good_boot_passes(self):
        self.assertTrue(self.run_case()["passed"])

    def test_two_pause_calls_pass(self):
        self.assertTrue(self.run_case(pause_lines=2)["passed"])

    def test_wrong_state_order_fails(self):
        self.assertFalse(self.run_case(history=STATES[:2] + STATES[3:])["passed"])

    def test_slow_boot_fails(self):
        self.assertFalse(self.run_case(seconds=130)["passed"])

    def test_too_many_pause_calls_fail(self):
        self.assertFalse(self.run_case(pause_lines=4)["passed"])

    def test_moving_clock_fails(self):
        self.assertFalse(self.run_case(clock_change=1.5)["passed"])


if __name__ == "__main__":
    unittest.main()
