"""Tests for the OS mouse helper and the place_building action. No game and no real input: all Windows calls are fakes."""

import unittest

import runlib_path  # noqa: F401
from runlib import osinput
from runlib.actions import ActionNotPossible, Actions
from runlib.expectations import Expectations

GAME = 100
WINDOW = (100, 100, 1100, 800)


class FakeApi:
    def __init__(self, foreground=GAME, cursor=(5, 5), grabs_focus=True):
        self.foreground = foreground
        self.cursor = cursor
        self.grabs_focus = grabs_focus
        self.events = []

    def foreground_window(self):
        return self.foreground

    def bring_to_front(self, hwnd):
        self.events.append("front")
        if self.grabs_focus:
            self.foreground = hwnd

    def window_rect(self, hwnd):
        return WINDOW

    def get_cursor(self):
        return self.cursor

    def set_cursor(self, x, y):
        self.cursor = (x, y)
        self.events.append(("cursor", x, y))

    def release_cursor_clip(self):
        self.events.append("unclip")

    def button(self, down):
        self.events.append("down" if down else "up")


def no_sleep(_seconds):
    pass


def make_steps(log, ground=True):
    return osinput.PlacementSteps(
        activate=lambda: log.append("activate"), cancel=lambda: log.append("cancel"),
        ground_under_cursor=lambda: ground, unpause=lambda: log.append("unpause"), pause=lambda: log.append("pause"))


class PointTest(unittest.TestCase):
    def test_point_in_window(self):
        self.assertEqual(osinput.point_in_window(WINDOW, 0.5, 0.5), (600, 450))

    def test_fraction_out_of_range_is_an_error(self):
        with self.assertRaises(osinput.InputError):
            osinput.point_in_window(WINDOW, 1.2, 0.5)

    def test_check_inside(self):
        osinput.check_inside(WINDOW, (600, 450))
        for outside in ((50, 450), (600, 805), (101, 450), (1099, 450)):
            with self.assertRaises(osinput.InputError):
                osinput.check_inside(WINDOW, outside)

    def test_is_ground_point(self):
        self.assertTrue(osinput.is_ground_point({"X": 1, "Y": 2, "Z": 3000.0}))
        self.assertFalse(osinput.is_ground_point({"X": 0, "Y": 0, "Z": -100000}))


class FocusTest(unittest.TestCase):
    def test_focus_ok(self):
        api = FakeApi(foreground=7)
        osinput.focus_game(api, GAME, no_sleep)
        self.assertEqual(api.foreground, GAME)

    def test_focus_refused_is_an_error(self):
        api = FakeApi(foreground=7, grabs_focus=False)
        with self.assertRaisesRegex(osinput.InputError, "not in the foreground"):
            osinput.focus_game(api, GAME, no_sleep)

    def test_no_click_when_another_window_is_in_front(self):
        api = FakeApi(foreground=7, cursor=(600, 450))
        with self.assertRaises(osinput.InputError):
            osinput.left_click(api, GAME, no_sleep)
        self.assertNotIn("down", api.events)

    def test_no_click_when_the_cursor_is_outside(self):
        api = FakeApi(cursor=(5, 5))
        with self.assertRaises(osinput.InputError):
            osinput.left_click(api, GAME, no_sleep)
        self.assertNotIn("down", api.events)

    def test_button_is_released_when_the_wait_fails(self):
        api = FakeApi(cursor=(600, 450))

        def failing_sleep(_seconds):
            raise RuntimeError("stop")

        with self.assertRaises(RuntimeError):
            osinput.left_click(api, GAME, failing_sleep)
        self.assertEqual(api.events[-1], "up")


class PlaceWithMouseTest(unittest.TestCase):
    def test_full_sequence_and_cursor_restored(self):
        api, log = FakeApi(foreground=7), []
        osinput.place_with_mouse(api, GAME, make_steps(log), 0.5, 0.5, no_sleep)
        self.assertEqual(log, ["activate", "unpause", "pause", "cancel"])
        self.assertLess(api.events.index("down"), api.events.index("up"))
        self.assertEqual(api.cursor, (5, 5))

    def test_no_ground_means_no_click(self):
        api, log = FakeApi(), []
        with self.assertRaisesRegex(osinput.InputError, "no terrain"):
            osinput.place_with_mouse(api, GAME, make_steps(log, ground=False), 0.5, 0.5, no_sleep)
        self.assertNotIn("down", api.events)
        self.assertEqual(log, ["activate", "cancel"])
        self.assertEqual(api.cursor, (5, 5))

    def test_no_focus_means_nothing_is_done(self):
        api, log = FakeApi(foreground=7, grabs_focus=False), []
        with self.assertRaises(osinput.InputError):
            osinput.place_with_mouse(api, GAME, make_steps(log), 0.5, 0.5, no_sleep)
        self.assertEqual(log, [])
        self.assertEqual(api.cursor, (5, 5))

    def test_game_is_paused_again_after_a_click_error(self):
        api, log = FakeApi(), []
        steps = make_steps(log)
        api.button = lambda down: (_ for _ in ()).throw(RuntimeError("boom")) if down else None
        with self.assertRaises(RuntimeError):
            osinput.place_with_mouse(api, GAME, steps, 0.5, 0.5, no_sleep)
        self.assertEqual(log[-2:], ["pause", "cancel"])


class FakeBridge:
    def __init__(self, places=True):
        self.count = 3
        self.places = places

    def engine_path(self):
        return "engine"

    def player_region_path(self):
        return "region"

    def call_function(self, ref, function, args=None):
        assert function == "getBuildingCount" and args == [30, False]
        return self.count


class PlaceBuildingActionTest(unittest.TestCase):
    def make(self, places=True):
        bridge = FakeBridge()
        calls = []

        def placer(type_id, fx, fy):
            calls.append((type_id, fx, fy))
            if places:
                bridge.count += 1

        expect = Expectations()
        return Actions(bridge, expect, [], mouse_placer=placer), expect, calls

    def test_placed(self):
        actions, _, calls = self.make()
        record = actions.place_building(30)
        self.assertTrue(record["ok"])
        self.assertEqual((record["before"], record["after"]), (3, 4))
        self.assertEqual(calls[0][0], 30)

    def test_nothing_placed_fails_the_read_back(self):
        actions, expect, _ = self.make(places=False)
        self.assertFalse(actions.place_building(30)["ok"])
        self.assertFalse(expect.result()["passed"])

    def test_no_placer_is_not_possible(self):
        with self.assertRaisesRegex(ActionNotPossible, "no OS mouse"):
            Actions(FakeBridge()).place_building(30)


if __name__ == "__main__":
    unittest.main()
