"""The three stand-in scenarios and ModState, run against the REAL Lua files in the fake game kit (spec 10, U10).

The chain is: scenario code -> ModState -> ModCommandChannel -> request files in modcmd/InvasionStandIn/ -> the poller of the real
HarnessCommands module inside the Lua state of the real InvasionStandIn mod, and back through the result files.
Every mod runs in its own Lua state (separate_states), as in UE4SS. Only the game is fake: the engine, the clock and the game days.
This checks the logic of the scenarios without the game. It does NOT prove that the real game loads the mods.
"""

import unittest

import fakegame_path  # noqa: F401
import runlib_path  # noqa: F401
from fakegame import FakeGame
from modstate_support import build_engine, mod_channel, set_days, sleep_in
from runlib.expectations import Expectations
from runlib.commands import ModDidNotAnswer
from runlib.modstate import ModCommandError, ModState
from scenarios import standin_captives, standin_outposts, standin_tribute

GAME_DAY_FAKE_SECONDS = 5  # one game day at speed 3 takes 5 wall seconds in the real game


class StackContext:
    """The parts of ScenarioContext that the stand-in scenarios use. `ctx.time` moves the fake game days."""

    def __init__(self, game):
        sleep = sleep_in(game)
        self._new_expectations = lambda: Expectations(sleep=sleep, monotonic=game.now)
        self.expect = self._new_expectations()
        self.mod_commands = mod_channel(game)
        self.mod = ModState(self, sleep=sleep, monotonic=game.now)
        self.time = FakeTime(game)
        self.ensure_alive = lambda where="scenario": None

    def result(self):
        return self.expect.result()

    def next_scenario(self):
        """The mod counts the request files, so a second scenario in the same game must use the same channel."""
        self.expect = self._new_expectations()


class FakeTime:
    """Like TimeControl.run_game_days: the day counter grows and the game runs for a while. `extra_days` simulates an overshoot."""

    def __init__(self, game, extra_days=0):
        self._game = game
        self.extra_days = extra_days
        self.calls = []

    def run_game_days(self, days, speed=1):
        start = self._game.exec("return FindFirstOf('RTSMultiEngineCPP').TemporalComponent.daysTotal")
        end = start + days + self.extra_days
        set_days(self._game, end)
        self._game.advance((days + self.extra_days) * GAME_DAY_FAKE_SECONDS)
        self.calls.append((days, speed))
        return {"days_start": start, "days_end": end}


def running_game():
    """A fake game with the three real mods loaded in the order of the real mods folder."""
    game = FakeGame(separate_states=True)
    game.start()
    build_engine(game)
    for name in ("HarnessActions", "HarnessTelemetry", "InvasionStandIn"):
        game.load_mod(name)
    game.advance(1)
    return game


class StandInScenarioTests(unittest.TestCase):
    def run_scenario(self, module, extra_days=0):
        game = running_game()
        self.addCleanup(game.close)
        ctx = StackContext(game)
        ctx.time.extra_days = extra_days
        result = module.run(ctx)
        failed = [a for a in result["asserts"] if not a["ok"]]
        return result, failed, ctx

    def test_outposts_scenario_passes_on_the_stand_in(self):
        result, failed, ctx = self.run_scenario(standin_outposts)
        self.assertEqual(failed, [])
        self.assertGreaterEqual(len(result["asserts"]), 20)
        self.assertEqual(ctx.time.calls, [(standin_outposts.WAIT_DAYS, standin_outposts.SPEED)])

    def test_captives_scenario_passes_on_the_stand_in(self):
        result, failed, _ = self.run_scenario(standin_captives)
        self.assertEqual(failed, [])
        self.assertGreaterEqual(len(result["asserts"]), 9)

    def test_tribute_scenario_passes_on_the_stand_in(self):
        result, failed, _ = self.run_scenario(standin_tribute)
        self.assertEqual(failed, [])
        self.assertGreaterEqual(len(result["asserts"]), 15)

    def test_tribute_scenario_passes_when_the_clock_overshoots_by_a_day(self):
        _, failed, _ = self.run_scenario(standin_tribute, extra_days=1)
        self.assertEqual(failed, [])

    def test_the_scenarios_can_run_twice_in_one_game(self):
        game = running_game()
        self.addCleanup(game.close)
        ctx = StackContext(game)
        for module in (standin_captives, standin_captives, standin_outposts):
            ctx.next_scenario()
            self.assertTrue(module.run(ctx)["passed"], module.NAME)


class StandInScenarioFailureTests(unittest.TestCase):
    """A scenario must fail when the mod breaks a rule. These tests change the Lua rule on purpose."""

    def run_broken(self, module, lua_patch):
        game = running_game()
        self.addCleanup(game.close)
        game.exec(lua_patch, state="InvasionStandIn")
        return module.run(StackContext(game))

    def test_a_mod_that_does_not_register_its_commands_fails_the_outposts_scenario_loudly(self):
        game = FakeGame(separate_states=True)
        game.start()
        self.addCleanup(game.close)
        build_engine(game)
        for name in ("HarnessActions", "HarnessTelemetry"):
            game.load_mod(name)
        game.advance(1)
        with self.assertRaises(ModDidNotAnswer) as caught:
            standin_outposts.run(StackContext(game))
        self.assertIn("mod did not answer: InvasionStandIn", str(caught.exception))

    def test_a_blind_outpost_that_still_sees_fails_the_scenario(self):
        result = self.run_broken(standin_outposts, """
            local commands = require("HarnessCommands")
            commands.unregister("InvasionStandIn.reveal")
            commands.register("InvasionStandIn.reveal", function() return { sees = true, scouting_range = 99 } end,
                { region_id = { type = "integer", required = true }, distance = { type = "number", required = true } })
        """)
        failed = [a["name"] for a in result["asserts"] if not a["ok"]]
        self.assertIn("O1 raid outside the border is not seen", failed)
        self.assertIn("O3 lost outpost is blind even at distance 0", failed)

    def test_a_tribute_that_is_never_charged_fails_the_scenario(self):
        game = running_game()
        self.addCleanup(game.close)
        game.exec("""
            local commands = require("HarnessCommands")
            commands.unregister("InvasionStandIn.accept_tribute")
            commands.register("InvasionStandIn.accept_tribute", function()
                return { treasury = 1000, paid_total = 0, hostages_given = 0, vassal = false, yearly_amount = 0, years_paid = 0,
                         year_days = 2, pending = "none" }
            end, {})
        """, state="InvasionStandIn")
        ctx = StackContext(game)
        with self.assertRaises(ModCommandError):  # the broken mod leaves the offer pending, so the next offer is refused
            standin_tribute.run(ctx)
        self.assertIn("S5 the payment left the treasury", [a["name"] for a in ctx.expect.records if not a["ok"]])

    def test_a_metric_that_stays_zero_fails_the_captives_scenario(self):
        result = self.run_broken(standin_captives, """
            require("HarnessCommands").metric("InvasionStandIn.captives", function() return 0 end)
        """)
        failed = [a["name"] for a in result["asserts"] if not a["ok"]]
        self.assertIn("R5 metric captives is 5", failed)


class ScenarioMetadataTests(unittest.TestCase):
    def test_each_scenario_has_a_limit_a_description_and_covers(self):
        for module, covers in ((standin_outposts, ["O1", "O2", "O3", "O4", "S4"]), (standin_captives, ["R5"]), (standin_tribute, ["S5"])):
            self.assertLessEqual(module.LIMIT_S, 120)
            self.assertIn("stand-in mod: a toy model that proves the harness method, not the real mod", module.DESCRIPTION.lower())
            self.assertEqual(module.COVERS, covers)
            self.assertFalse(getattr(module, "HIDDEN", False))


if __name__ == "__main__":
    unittest.main()
