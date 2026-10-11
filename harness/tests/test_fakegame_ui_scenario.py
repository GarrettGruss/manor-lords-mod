"""The scenario ui-countdown against the REAL Lua files (HarnessActions, HarnessUi) in the fake game kit (spec 10, spike S9, criterion T4).

Only the game is fake. This checks the logic of the scenario, the action and the mod. The real runs are in spike-S9.md.
"""

import unittest
from types import SimpleNamespace

import fakegame_path  # noqa: F401
import runlib_path  # noqa: F401
from fakegame import FakeGame
from modstate_support import sleep_in
from runlib.actions import Actions, ActionError
from runlib.commands import CommandChannel
from runlib.expectations import Expectations
from scenarios import ui_countdown
from test_fakegame_harnessactions import add_banner_maker, start


class FakeCalendarBridge:
    """Only the raid timer. The fake time lowers it by one for each game day."""

    def __init__(self):
        self.timer = 0
        self.since = 0

    def engine_path(self):
        return "engine"

    def calendar_path(self):
        return "calendar"

    def read_property(self, ref, name):
        return {"daysUntilNextRaid": self.timer, "daysSinceLastRaid": self.since}[name]

    def write_property(self, ref, name, value):
        if name == "daysUntilNextRaid":
            self.timer = value
        else:
            self.since = value


class FakeDayTime:
    def __init__(self, bridge):
        self.bridge = bridge
        self.days = 0

    def run_game_days(self, days, speed=1):
        self.days += days
        self.bridge.timer -= days


class UiContext:
    def __init__(self, game):
        sleep = sleep_in(game)
        self.expect = Expectations(sleep=sleep, monotonic=game.now)
        self.notes, self.metrics, self.shots = [], {}, []
        self.log = SimpleNamespace(info=lambda message: None)
        self.bridge = FakeCalendarBridge()
        self.time = FakeDayTime(self.bridge)
        commands = CommandChannel(game.run_dir / "commands", sleep=sleep, monotonic=game.now)
        self.actions = Actions(self.bridge, self.expect, self.notes, commands=commands)

    def metric(self, name, value):
        self.metrics[name] = value

    def screenshot(self, name):
        self.shots.append(name)

    def result(self):
        result = self.expect.result()
        result["notes"] = list(self.notes)
        return result


class UiCountdownTests(unittest.TestCase):
    def run_scenario(self, banner_works=True):
        game = FakeGame()
        game.start()
        self.addCleanup(game.close)
        player, _ = start(game)
        made = add_banner_maker(game, player, fail=not banner_works)
        ctx = UiContext(game)
        return ui_countdown.run(ctx), ctx, made

    def test_passes_and_shows_one_banner_for_each_day(self):
        result, ctx, made = self.run_scenario()
        self.assertEqual([a["name"] for a in result["asserts"] if not a["ok"]], [])
        self.assertEqual(made, ["Default"] * 3)
        self.assertEqual(ctx.shots, ["countdown-4", "countdown-3", "countdown-2"])
        self.assertEqual(ctx.time.days, 2, "the scenario stops before the day that brings the timer to 0")
        self.assertEqual(ctx.metrics, {"countdown_steps": 3})

    def test_a_game_that_shows_no_banner_fails(self):
        result, _, _ = self.run_scenario(banner_works=False)
        self.assertFalse(result["passed"])
        self.assertIn("a new banner widget appeared for 4 days", [a["name"] for a in result["asserts"] if not a["ok"]])

    def test_the_action_refuses_markup_before_it_calls_the_mod(self):
        game = FakeGame()
        game.start()
        self.addCleanup(game.close)
        player, _ = start(game)
        made = add_banner_maker(game, player)
        ctx = UiContext(game)
        for bad in ("<b>x</b>", "a;b", "x" * 61, ""):
            with self.assertRaises(ActionError):
                ctx.actions.show_message(bad)
        with self.assertRaises(ActionError):
            ctx.actions.show_message("fine", "bad;")
        self.assertEqual(made, [])


if __name__ == "__main__":
    unittest.main()
