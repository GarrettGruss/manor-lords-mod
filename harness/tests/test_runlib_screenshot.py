"""Tests for window picking and the screenshot code with fake windows and a fake mss."""

import tempfile
import unittest
from pathlib import Path

import runlib_path  # noqa: F401
from runlib.screenshot import capture_game_window, clip_to_bounds
from runlib.windows import pick_game_window

SCREEN = {"left": 0, "top": 0, "width": 1920, "height": 1080}


def window(pid, rect, visible=True, iconic=False, title="w"):
    return {"hwnd": 1, "pid": pid, "title": title, "visible": visible, "iconic": iconic, "rect": rect}


class PickWindowTest(unittest.TestCase):
    def test_picks_the_largest_window_of_the_game(self):
        windows = [
            window(1, (0, 0, 100, 100), title="other process"),
            window(7, (0, 0, 200, 100), title="small"),
            window(7, (0, 0, 1920, 1080), title="Manor Lords"),
        ]
        self.assertEqual(pick_game_window(windows, {7})["title"], "Manor Lords")

    def test_any_pid_of_the_set(self):
        self.assertEqual(pick_game_window([window(9, (0, 0, 10, 10))], {7, 9})["pid"], 9)

    def test_no_window(self):
        with self.assertRaisesRegex(LookupError, "no window belongs"):
            pick_game_window([window(1, (0, 0, 10, 10))], {7})

    def test_invisible_or_empty_window(self):
        with self.assertRaisesRegex(LookupError, "no visible"):
            pick_game_window([window(7, (0, 0, 10, 10), visible=False), window(7, (5, 5, 5, 5))], {7})

    def test_minimized_window(self):
        with self.assertRaisesRegex(LookupError, "minimized"):
            pick_game_window([window(7, (-32000, -32000, -31840, -31972), iconic=True)], {7})


class ClipTest(unittest.TestCase):
    def test_inside(self):
        self.assertEqual(clip_to_bounds((10, 20, 110, 220), SCREEN), {"left": 10, "top": 20, "width": 100, "height": 200})

    def test_partly_outside(self):
        self.assertEqual(clip_to_bounds((-8, -8, 1928, 1088), SCREEN), SCREEN)

    def test_second_monitor_in_the_virtual_screen(self):
        bounds = {"left": -1920, "top": 0, "width": 3840, "height": 1080}
        region = clip_to_bounds((-1920, 0, 0, 1080), bounds)
        self.assertEqual(region["left"], -1920)

    def test_fully_outside(self):
        self.assertIsNone(clip_to_bounds((3000, 0, 3100, 100), SCREEN))


class FakeGrabber:
    monitors = [SCREEN]

    def __init__(self):
        self.regions = []

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def grab(self, region):
        self.regions.append(region)
        return "shot"


class CaptureTest(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.path = Path(temp.name) / "start.png"
        self.written = []

    def writer(self, shot, path):
        self.written.append((shot, path))

    def test_success(self):
        grabber = FakeGrabber()
        note = capture_game_window(
            self.path, {7}, windows_fn=lambda: [window(7, (0, 0, 800, 600))],
            grabber_factory=lambda: grabber, png_writer=self.writer,
        )
        self.assertIsNone(note)
        self.assertEqual(grabber.regions, [{"left": 0, "top": 0, "width": 800, "height": 600}])
        self.assertEqual(self.written, [("shot", self.path)])

    def test_no_window_gives_a_note(self):
        note = capture_game_window(self.path, {7}, windows_fn=lambda: [], grabber_factory=FakeGrabber, png_writer=self.writer)
        self.assertIn("no window", note)
        self.assertEqual(self.written, [])

    def test_window_outside_the_screen(self):
        note = capture_game_window(
            self.path, {7}, windows_fn=lambda: [window(7, (5000, 0, 5100, 100))],
            grabber_factory=FakeGrabber, png_writer=self.writer,
        )
        self.assertIn("outside the screen", note)

    def test_any_error_becomes_a_note(self):
        def broken():
            raise OSError("screen is locked")

        note = capture_game_window(self.path, {7}, windows_fn=lambda: [window(7, (0, 0, 9, 9))], grabber_factory=broken)
        self.assertEqual(note, "OSError: screen is locked")


if __name__ == "__main__":
    unittest.main()
