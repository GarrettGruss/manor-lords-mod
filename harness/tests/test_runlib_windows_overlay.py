"""The game window is the UnrealWindow. Debug windows of the same process must not be captured by mistake."""

import tempfile
import unittest
from pathlib import Path
from unittest import mock

import runlib_path  # noqa: F401
from runlib import screenshot
from runlib.windows import overlay_windows, pick_game_window

SCREEN = {"left": 0, "top": 0, "width": 3840, "height": 2160}


def win(hwnd, cls, title, rect, pid=7, visible=True, iconic=False):
    return {"hwnd": hwnd, "pid": pid, "class": cls, "title": title, "visible": visible, "iconic": iconic, "rect": rect}


GAME = win(1, "UnrealWindow", "Manor Lords  ", (629, 285, 3211, 1781))
GUI = win(2, "GLFW30", "UE4SS Debugging Tools (OpenGL 3) - ExternalThread", (342, 342, 1622, 1142))
CONSOLE = win(3, "ConsoleWindowClass", "C:\\...\\ManorLords-Win64-Shipping.exe", (100, 100, 1500, 700))
HIDDEN = win(4, "NVOpenGLPbuffer", "NVOGLDC invisible", (0, 0, 2880, 1546), visible=False)


class PickByClassTest(unittest.TestCase):
    def test_the_unreal_window_wins_even_if_a_debug_window_is_larger(self):
        big_gui = win(2, "GLFW30", "UE4SS Debugging Tools", (0, 0, 3000, 2000))
        self.assertEqual(pick_game_window([big_gui, GAME], {7})["hwnd"], 1)

    def test_a_minimized_game_window_is_reported_not_replaced_by_a_debug_window(self):
        minimized = dict(GAME, iconic=True)
        with self.assertRaisesRegex(LookupError, "minimized"):
            pick_game_window([GUI, CONSOLE, minimized], {7})

    def test_a_hidden_game_window_is_reported(self):
        with self.assertRaisesRegex(LookupError, "not visible"):
            pick_game_window([GUI, dict(GAME, visible=False)], {7})

    def test_without_an_unreal_window_the_largest_visible_window_is_used(self):
        other = win(5, "SomeClass", "other game", (0, 0, 800, 600))
        self.assertEqual(pick_game_window([other, win(6, "X", "small", (0, 0, 10, 10))], {7})["hwnd"], 5)

    def test_windows_of_other_processes_are_ignored(self):
        with self.assertRaisesRegex(LookupError, "no window belongs"):
            pick_game_window([dict(GAME, pid=99)], {7})


class OverlayTest(unittest.TestCase):
    def test_finds_the_ue4ss_gui_and_the_console(self):
        found = {w["hwnd"] for w in overlay_windows([GAME, GUI, CONSOLE, HIDDEN], {7})}
        self.assertEqual(found, {2, 3})

    def test_ignores_other_processes_hidden_and_minimized_windows(self):
        windows = [dict(GUI, pid=99), dict(CONSOLE, visible=False), dict(GUI, hwnd=9, iconic=True)]
        self.assertEqual(overlay_windows(windows, {7}), [])

    def test_a_window_with_another_title_is_not_an_overlay(self):
        self.assertEqual(overlay_windows([win(8, "GLFW30", "Something else", (0, 0, 100, 100))], {7}), [])


class FakeGrab:
    size = (10, 10)
    rgb = b"x"


class FakeGrabber:
    monitors = [SCREEN]

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def grab(self, region):
        return FakeGrab()


class CaptureMinimizesOverlaysTest(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.path = Path(temp.name) / "shot.png"

    def test_overlays_are_minimized_before_the_grab(self):
        minimized = []
        order = []
        sleeps = []
        grabber = FakeGrabber()
        real_grab = grabber.grab
        grabber.grab = lambda region: (order.append("grab"), real_grab(region))[1]

        def minimize(hwnd):
            minimized.append(hwnd)
            order.append("minimize")

        with mock.patch.object(screenshot.time, "sleep", sleeps.append):
            note = screenshot.capture_game_window(
                self.path, {7}, windows_fn=lambda: [GAME, GUI, CONSOLE],
                grabber_factory=lambda: grabber, png_writer=lambda shot, path: None, minimize_fn=minimize)
        self.assertIsNone(note)
        self.assertEqual(sorted(minimized), [2, 3])
        self.assertEqual(order, ["minimize", "minimize", "grab"])
        self.assertEqual(sleeps, [screenshot.REPAINT_WAIT_S])

    def test_no_overlay_means_no_minimize_and_no_wait(self):
        sleeps = []
        with mock.patch.object(screenshot.time, "sleep", sleeps.append):
            note = screenshot.capture_game_window(
                self.path, {7}, windows_fn=lambda: [GAME], grabber_factory=FakeGrabber,
                png_writer=lambda shot, path: None, minimize_fn=lambda hwnd: self.fail("nothing to minimize"))
        self.assertIsNone(note)
        self.assertEqual(sleeps, [])

    def test_a_minimized_game_window_gives_a_clear_note_and_does_not_capture_the_gui(self):
        written = []
        note = screenshot.capture_game_window(
            self.path, {7}, windows_fn=lambda: [dict(GAME, iconic=True), GUI], grabber_factory=FakeGrabber,
            png_writer=lambda shot, path: written.append(path), minimize_fn=lambda hwnd: None)
        self.assertIn("minimized", note)
        self.assertEqual(written, [])


if __name__ == "__main__":
    unittest.main()
