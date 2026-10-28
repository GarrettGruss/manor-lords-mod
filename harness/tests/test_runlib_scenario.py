"""Tests for the bridge client, the scenario context, the registry and the real scenarios. No game."""

import tempfile
import unittest
from pathlib import Path
from unittest import mock

import runlib_path  # noqa: F401
from runlib.bridge_client import Bridge, object_path
from runlib.runfolder import create_run_folder
from runlib.runner import PhaseContext, PhaseFailed
from runlib.scenario import LONG_LIMIT_S, MAX_LIMIT_S, SCENARIO_INFO, get_limit_s, list_scenarios, register
from runlib.scenario_context import ScenarioContext
from scenarios import selftest_fail, smoke

# A limit above LONG_LIMIT_S (300 s) needs a LONG_REASON in the module, and MAX_LIMIT_S is the last word (spec 10, U3).
LIMIT_CAP_S = MAX_LIMIT_S

ENGINE = "Map.Map:PersistentLevel.RTSGameManager"
PLAYER = "Map.Map:PersistentLevel.MyPawnCPP_BP3_C_77"
CALENDAR = ENGINE + ".TemporalComponent"


class FakeGame:
    """A fake bridge. The clock runs while `running` is true. Each sleep moves the clock."""

    def __init__(self, running=False, calendar=(61, 3, 1), obeys_pause=True, obeys_unpause=True):
        self.running = running
        self.clock = 10.0
        self.calendar = dict(zip(("day", "month", "Year"), calendar))
        self.obeys_pause = obeys_pause
        self.obeys_unpause = obeys_unpause
        self.calls = []

    def sleep(self, seconds):
        if self.running:
            self.clock += seconds

    def one(self, op, **args):
        self.calls.append((op, args))
        if op == "objects":
            return {"result": {"objects": [f"MyRTSMultiEngineCPP_BP_C {ENGINE}"]}}
        if op == "get":
            return {"result": self._get(args["ref"], args["name"])}
        if op == "call":
            return {"result": self._call(args["ref"], args["function"])}
        raise AssertionError(f"unexpected op {op}")

    def _get(self, ref, name):
        if name == "playerRef":
            return {"__object": f"MyPawnCPP_BP3_C {PLAYER}", "address": 1}
        if name == "TemporalComponent":
            return {"__object": f"TemporalComponent {CALENDAR}", "address": 2}
        assert ref == CALENDAR
        return self.calendar[name]

    def _call(self, ref, function):
        if function == "getGameTimeAdjusted":
            return self.clock
        assert ref == PLAYER
        if function == "pauseGame" and self.obeys_pause:
            self.running = False
        if function == "unPauseGame" and self.obeys_unpause:
            self.running = True
        return None


def make_bridge(game):
    return Bridge(game.one, sleep=game.sleep)


class ObjectPathTest(unittest.TestCase):
    def test_dict_and_string(self):
        self.assertEqual(object_path({"__object": "A /x/y"}), "/x/y")
        self.assertEqual(object_path("A /x/y"), "/x/y")

    def test_bad_value(self):
        with self.assertRaises(ValueError):
            object_path("nospace")


class BridgeTest(unittest.TestCase):
    def test_paths_are_looked_up(self):
        bridge = make_bridge(FakeGame())
        self.assertEqual(bridge.engine_path(), ENGINE)
        self.assertEqual(bridge.player_path(), PLAYER)

    def test_no_engine_object(self):
        game = FakeGame()
        game.one = lambda op, **a: {"result": {"objects": []}}
        with self.assertRaisesRegex(RuntimeError, "not loaded"):
            make_bridge(game).engine_path()

    def test_calendar(self):
        self.assertEqual(make_bridge(FakeGame()).read_calendar(), {"day": 61, "month": 3, "year": 1})

    def test_measure_clock_stopped_and_running(self):
        self.assertTrue(make_bridge(FakeGame(running=False)).measure_clock(3)["paused"])
        moving = make_bridge(FakeGame(running=True)).measure_clock(3)
        self.assertFalse(moving["paused"])
        self.assertEqual(moving["change"], 3.0)

    def test_pause_works(self):
        game = FakeGame(running=True)
        result = make_bridge(game).pause()
        self.assertTrue(result["ok"])
        self.assertEqual(result["attempts"], 1)
        self.assertIn(("call", {"ref": PLAYER, "function": "pauseGame", "args": []}), game.calls)

    def test_pause_retries_then_gives_up(self):
        result = make_bridge(FakeGame(running=True, obeys_pause=False)).pause(attempts=3)
        self.assertFalse(result["ok"])
        self.assertEqual(result["attempts"], 3)

    def test_unpause_works(self):
        result = make_bridge(FakeGame(running=False)).unpause()
        self.assertTrue(result["ok"])
        self.assertGreater(result["change"], 0)

    def test_unpause_fails_when_the_clock_stays(self):
        result = make_bridge(FakeGame(running=False, obeys_unpause=False)).unpause(timeout_s=2, attempts=2)
        self.assertFalse(result["ok"])


class FakePopen:
    def __init__(self, exit_code=None):
        self.exit_code = exit_code

    def poll(self):
        return self.exit_code


class ContextTestCase(unittest.TestCase):
    def make_context(self, game, popen=None):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        run = create_run_folder(Path(temp.name) / "runs", "r1")
        phase_ctx = PhaseContext(run=run, config={})
        phase_ctx.state["game_popen"] = popen or FakePopen(None)
        return ScenarioContext(phase_ctx, make_bridge(game))


class ScenarioContextTest(ContextTestCase):
    def test_checks_and_result(self):
        ctx = self.make_context(FakeGame())
        ctx.check("a", True, 1)
        ctx.check_range("b", 5, 1, 3)
        result = ctx.result()
        self.assertFalse(result["passed"])
        self.assertEqual(result["asserts"][1], {"name": "b", "ok": False, "value": 5, "rule": "1..3"})
        self.assertNotIn("range", result["asserts"][0])

    def test_empty_result_passes(self):
        self.assertTrue(self.make_context(FakeGame()).result()["passed"])

    def test_log_file_is_written(self):
        ctx = self.make_context(FakeGame())
        ctx.check("a", True)
        text = (ctx.run_dir / "scenario.log").read_text(encoding="utf-8")
        self.assertIn("assert ok: a", text)

    def test_dead_game_is_a_crash(self):
        ctx = self.make_context(FakeGame(), popen=FakePopen(1))
        with self.assertRaises(PhaseFailed):
            ctx.read_clock()
        self.assertIn("scenario", ctx.phase.state["crash"]["reason"])

    def test_screenshot_helper_uses_callback(self):
        ctx = self.make_context(FakeGame())
        ctx._screenshot_fn = mock.Mock()
        ctx.screenshot("mid")
        ctx._screenshot_fn.assert_called_once_with(ctx.phase, "mid")


class RealScenarioTest(ContextTestCase):
    def test_smoke_passes_on_a_good_game(self):
        ctx = self.make_context(FakeGame(running=False))
        result = smoke.run(ctx)
        self.assertTrue(result["passed"], result)
        self.assertEqual(len(result["asserts"]), 6)

    def test_smoke_fails_when_unpause_does_not_work(self):
        ctx = self.make_context(FakeGame(running=False, obeys_unpause=False))
        self.assertFalse(smoke.run(ctx)["passed"])

    def test_smoke_fails_on_a_wrong_calendar(self):
        ctx = self.make_context(FakeGame(running=False, calendar=(0, 13, 1)))
        result = smoke.run(ctx)
        self.assertFalse(result["passed"])
        self.assertEqual(
            [a["name"] for a in result["asserts"] if not a["ok"]],
            ["calendar day is sane", "calendar month is sane"],
        )

    def test_smoke_fails_when_the_game_starts_running(self):
        self.assertFalse(smoke.run(self.make_context(FakeGame(running=True)))["passed"])

    def test_selftest_fail_always_fails_on_a_paused_game(self):
        self.assertFalse(selftest_fail.run(self.make_context(FakeGame(running=False)))["passed"])


class RegistryTest(unittest.TestCase):
    def test_hidden_scenarios_are_not_listed_by_default(self):
        self.assertEqual(sorted(list_scenarios()), [
            "autosave-after-load", "autosave-protection", "bandits-banditry-banners", "bandits-banditry-timer", "bandits-buy-back", "bandits-homes-inventory", "bandits-order-tick", "bandits-outlaws-init", "bandits-rebellion-loot", "bandits-rebellion-loot-roundtrip", "bandits-rebellion-raid", "boot-timing", "combat-levers", "counters-ab", "datatable-vanilla", "finite-resources-iron", "finite-resources-vassal-supply", "invasion-difficulty-pick", "invasion-first-raid", "invasion-great-raid-clock", "invasion-great-raid-waves", "invasion-no-double-raid", "invasion-raid-anchor-manor", "invasion-raid-composition", "invasion-raid-widget", "invasion-subjugation-raid", "invasion-vassal-targets", "invasion-yearly-raid", "letter-delivery", "liege-arms-shipment", "liege-influence-roundtrip", "liege-send-tribute", "liege-tribute-menu", "loot-drop-recovery", "manor-stronghold-retinue", "manor-stronghold-retinue-squads", "manor-stronghold-storage", "menu-base", "menu-smoke", "mercenary-hire", "meshy-agent-house", "mod-state-default-load", "mod-state-roundtrip", "mod-state-two-saves", "noop", "order-tooltip-rows", "probe-difficulty-setting", "probe-raid-loot-cap",
            "raid-behavior", "raid-behavior-baron-steal", "raid-behavior-carry-caps", "raid-behavior-lord-leave-reason", "raid-behavior-pit-loot", "raid-behavior-region-guard", "raid-behavior-role-leave", "raid-behavior-storage-tiers", "raid-load", "raid-loot", "raid-politics",
            "raid-sack", "raid-seasons", "raid-spawn", "raid-tiers",
            "raid-timeline", "raid-timer", "refugees-housing-and-timeout", "refugees-wave", "sack-and-terms-pay-terms", "sack-and-terms-raid-sack", "sack-and-terms-sack", "sack-and-terms-sack-region", "sack-ruins", "sack-store-trip", "sack-village", "scenario-settings-first-raid-delay", "scenario-settings-game-settings-guard", "scenario-settings-great-raids-off", "scenario-settings-hussite-template", "scenario-settings-load-keeps-settings", "scenario-settings-new-game-menu", "scenario-settings-player-launch-pause", "scenario-settings-start-kit", "silver-change", "smoke",
            "soak-days", "standin-captives", "standin-outposts", "standin-tribute",
            "tech-tree-laws", "tech-tree-militia-factor", "tech-tree-path-choice", "tech-tree-widget", "tech-tree-widget-clicks", "tech-tree-widget-key", "tech-tree-widget-laws", "tech-tree-widget-tooltip", "telemetry-sanity", "time-advance", "tribute-payout", "ui-countdown", "unit-balance-armored-fight", "unit-balance-armored-kept", "unit-balance-lethality", "unit-balance-matchup", "unit-balance-role-templates", "unit-data", "vassals-claim-without-victory", "vassals-loss-and-submission", "vassals-policies-and-orders", "vassals-sack-end", "vassals-settled-vassal", "vassals-wipe", "veterancy", "winter-region"])
        self.assertIn("selftest-timeout", list_scenarios(include_hidden=True))
        self.assertIn("selftest-action", list_scenarios(include_hidden=True))
        self.assertIn("selftest-crash", list_scenarios(include_hidden=True))
        self.assertIn("probe-actions", list_scenarios(include_hidden=True))
        self.assertIn("manor-storage", list_scenarios(include_hidden=True))  # real mouse: hidden
        self.assertIn("manor-storage-workers", list_scenarios(include_hidden=True))  # real mouse: hidden
        self.assertIn("place-building", list_scenarios(include_hidden=True))  # takes over the real mouse: hidden on purpose

    def test_every_scenario_has_a_limit_under_the_cap(self):
        for name, info in list_scenarios(include_hidden=True).items():
            self.assertTrue(0 < info.limit_s <= LIMIT_CAP_S, name)
            self.assertTrue(info.limit_s <= LONG_LIMIT_S or info.long_reason, name)
        self.assertEqual(get_limit_s("selftest-timeout"), 5)
        self.assertEqual(get_limit_s("unknown"), 90)

    def test_double_registration_is_refused(self):
        with self.assertRaises(ValueError):
            register("smoke")(lambda ctx: {})
        self.assertIn("smoke", SCENARIO_INFO)


if __name__ == "__main__":
    unittest.main()
