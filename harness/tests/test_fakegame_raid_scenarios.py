"""The six raid stand-in scenarios, run against the REAL Lua files in the fake game kit (spec 10 follow-up of U10).

The chain is the same as in test_fakegame_standin_scenarios: scenario code -> ModState -> ModCommandChannel -> request files ->
the poller of the real HarnessCommands module in the Lua state of the real RaidStandIn mod. Only the game is fake.
Broken-rule tests load a copy of the mod with one changed rule. The scenario that covers the rule must then fail.
This checks the logic of the scenarios without the game. It does NOT prove that the real game loads the mod.
"""

import math
import tempfile
import unittest
from pathlib import Path

import fakegame_path  # noqa: F401
import runlib_path  # noqa: F401
from fakegame import FakeGame
from modstate_support import build_engine
from runlib.commands import ModDidNotAnswer
from runlib.modstate import ModCommandError
from scenarios import raid_behavior, raid_politics, raid_sack, raid_seasons, raid_tiers, raid_timeline
from test_fakegame_standin_scenarios import StackContext

MOD_FILE = Path(__file__).resolve().parents[2] / "mod" / "RaidStandIn" / "Scripts" / "main.lua"
ALL_SCENARIOS = (raid_timeline, raid_seasons, raid_behavior, raid_tiers, raid_sack, raid_politics)
TIER_METRICS = [f"tier{tier}_mean_{kind}" for tier in (1, 2, 3, 4) for kind in ("size", "raids")]


class ScenarioLog:
    def __init__(self):
        self.lines = []

    def info(self, message):
        self.lines.append(message)


class RaidContext(StackContext):
    """The parts of ScenarioContext that the raid scenarios use, on top of the stand-in test context."""

    def __init__(self, game, run_name="20261010-120000-0001"):
        super().__init__(game)
        self.run_dir = Path("runs") / run_name
        self.log = ScenarioLog()
        self.metrics = {}

    def metric(self, name, value):
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
            raise ValueError(f"metric {name!r} must be a finite number, got {value!r}")
        self.metrics[name] = float(value)


def load_raid_mod(game, text=None):
    """Load RaidStandIn. With `text`, load that source instead (a copy with a broken rule)."""
    if text is None:
        game.load_mod("RaidStandIn")
        return
    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder) / "main.lua"
        path.write_text(text, encoding="utf-8")
        game.load_script(path, state="RaidStandIn", fresh=True)


def running_game(text=None, with_mod=True, env=None):
    game = FakeGame(separate_states=True, env=env)
    game.start()
    build_engine(game)
    for name in ("HarnessActions", "HarnessTelemetry"):
        game.load_mod(name)
    if with_mod:
        load_raid_mod(game, text)
    game.advance(1)
    return game


def broken_source(old, new):
    source = MOD_FILE.read_text(encoding="utf-8")
    assert old in source, f"the rule text is not in the mod any more: {old!r}"
    return source.replace(old, new, 1)


class RaidScenarioTests(unittest.TestCase):
    def run_scenario(self, module, extra_days=0, run_name="20261010-120000-0001"):
        game = running_game()
        self.addCleanup(game.close)
        ctx = RaidContext(game, run_name)
        ctx.time.extra_days = extra_days
        result = module.run(ctx)
        return result, [a["name"] for a in result["asserts"] if not a["ok"]], ctx

    def test_timeline_passes_and_waits_real_game_days(self):
        result, failed, ctx = self.run_scenario(raid_timeline)
        self.assertEqual(failed, [])
        self.assertGreaterEqual(len(result["asserts"]), 24)
        self.assertEqual(ctx.time.calls, [(raid_timeline.CLOCK_ANNOUNCE_DAYS, raid_timeline.SPEED)] * 2)

    def test_timeline_passes_when_the_clock_overshoots_by_a_day(self):
        _, failed, _ = self.run_scenario(raid_timeline, extra_days=1)
        self.assertEqual(failed, [])

    def test_seasons_passes(self):
        result, failed, _ = self.run_scenario(raid_seasons)
        self.assertEqual(failed, [])
        self.assertGreaterEqual(len(result["asserts"]), 25)

    def test_behavior_passes(self):
        result, failed, _ = self.run_scenario(raid_behavior)
        self.assertEqual(failed, [])
        self.assertGreaterEqual(len(result["asserts"]), 30)

    def test_tiers_passes_and_reports_metrics_for_the_ab_runner(self):
        result, failed, ctx = self.run_scenario(raid_tiers)
        self.assertEqual(failed, [])
        self.assertEqual(sorted(ctx.metrics), sorted(TIER_METRICS))
        self.assertLess(ctx.metrics["tier1_mean_size"], ctx.metrics["tier4_mean_size"])
        self.assertLess(ctx.metrics["tier1_mean_raids"], ctx.metrics["tier4_mean_raids"])

    def test_sack_passes(self):
        result, failed, _ = self.run_scenario(raid_sack)
        self.assertEqual(failed, [])
        self.assertGreaterEqual(len(result["asserts"]), 15)

    def test_politics_passes(self):
        result, failed, _ = self.run_scenario(raid_politics)
        self.assertEqual(failed, [])
        self.assertGreaterEqual(len(result["asserts"]), 26)

    def test_the_size_setting_of_the_ab_suite_changes_the_reported_metrics(self):
        means = {}
        for percent in ("100", "150"):
            game = running_game(env={"RAID_STANDIN_SIZE_PERCENT": percent})
            self.addCleanup(game.close)
            ctx = RaidContext(game)
            self.assertTrue(raid_tiers.run(ctx)["passed"], percent)
            means[percent] = ctx.metrics["tier3_mean_size"]
        self.assertAlmostEqual(means["150"] / means["100"], 1.5, delta=0.15)

    def test_the_random_scenarios_pass_for_many_run_names(self):
        # The seed base comes from the run folder name, so every real run uses other numbers. None may fail by chance.
        for index in range(12):
            for module in (raid_seasons, raid_behavior, raid_tiers):
                _, failed, _ = self.run_scenario(module, run_name=f"20261010-1200{index:02d}-{index:04x}")
                self.assertEqual(failed, [], (module.NAME, index))

    def test_the_scenarios_can_run_one_after_the_other_in_one_game(self):
        game = running_game()
        self.addCleanup(game.close)
        ctx = RaidContext(game)
        for module in ALL_SCENARIOS:
            ctx.next_scenario()
            self.assertTrue(module.run(ctx)["passed"], module.NAME)


class RaidScenarioFailureTests(unittest.TestCase):
    """A scenario must fail when the mod breaks a rule. Each case loads the mod with one changed rule."""

    CASES = (
        (raid_timeline, "the announcement comes a day late",
         "arrivalDay - S.config.announce_days)", "arrivalDay - S.config.announce_days + 1)", "T1 cuman: it is announced N days before arrival"),
        (raid_timeline, "the announced kind is not the dominant unit", "kind = dominantUnit(composition),", 'kind = "scouts",',
         "T3 cuman: the announced kind is the expected one"),
        (raid_seasons, "raids ignore the season rule", "while not seasonAllows(faction, day) do", "while false do",
         "T5 every raid day follows its season rule"),
        (raid_seasons, "winter does not pause fighting", "if isWinter() then\n        raid.paused_days", "if false then\n        raid.paused_days",
         "P6 winter pauses fighting: no loot"),
        (raid_seasons, "winter does not strain the food", "return 10 + (isWinter() and 5 or 0) + lawUpkeep()", "return 10 + lawUpkeep()",
         "P6 the town eats more in winter"),
        (raid_behavior, "full loot does not end a raid", 'if raid.loot >= raid.capacity then return "full_loot" end',
         'if raid.loot >= raid.capacity then return nil end', "R4 full loot: the raid retreats"),
        (raid_behavior, "the leader death does not end a raid", 'if not raid.leader_alive then return "leader_dead" end',
         'if not raid.leader_alive then return nil end', "R4 leader dead: the raid retreats"),
        (raid_behavior, "raiders go for the farthest pile", "pile.distance < S.stockpiles[best].distance", "pile.distance > S.stockpiles[best].distance",
         "R6 raiders choose the nearest high value stockpile"),
        (raid_behavior, "a raid has no objective", "objective = info.objective,", 'objective = "",',
         "R1 each raid has exactly one objective of its faction"),
        (raid_tiers, "all tiers bring the same size", "local size = tier.size *", "local size = 20 *", "D1 size: tier 3 is bigger than tier 1 (relative)"),
        (raid_tiers, "all tiers bring one unit type", "composeUnits(info.units, size, tier.variety)", "composeUnits(info.units, size, 1)",
         "D1 variety: tier 2 raids have 2 unit types"),
        (raid_tiers, "the warlord never returns stronger", "S.warlord.level = math.min(MAX_WARLORD_LEVEL, S.warlord.level + 1)",
         "S.warlord.level = 0", "D2 the warlord level is 1"),
        (raid_tiers, "the top tier retreats for other reasons", "breaking_point = 0, leader_only = true", "breaking_point = 0, leader_only = false",
         "D3 full loot does not make the top tier retreat"),
        (raid_sack, "one sack is fatal", "if sacksInWindow() >= S.config.sack_limit then", "if true then", "S2 no game over after one sack"),
        (raid_sack, "sacks are never fatal", "if sacksInWindow() >= S.config.sack_limit then", "if false then", "S3 the second sack is fatal"),
        (raid_sack, "old sacks never leave the window", "if S.day - day < S.config.sack_window_days then", "if true then",
         "S3 the old sack left the window"),
        (raid_politics, "conscription gives no defense", "upkeep = 3, defense = 20", "upkeep = 3, defense = 0", "P1 conscription adds defense"),
        (raid_politics, "the pact does not cut the size", "size = size * LAWS.cuman_pact.cuman_size_percent / 100", "size = size",
         "P1 the cuman pact cuts cuman raid size (ratio)"),
        (raid_politics, "fear never grows", "(threatIsNear() and -2 or 1)", "1", "P2 fear grows while a raid is announced"),
        (raid_politics, "the war economy moves nobody", "local WAR_ECONOMY_SHIFT = 10", "local WAR_ECONOMY_SHIFT = 0",
         "P4 farmers move to the military"),
    )

    def failed_names(self, module, text):
        """The names of the failed assertions. A broken mod may also make a command fail: that is a loud failure too."""
        game = running_game(text)
        self.addCleanup(game.close)
        ctx = RaidContext(game)
        try:
            module.run(ctx)
        except ModCommandError:
            pass
        return [a["name"] for a in ctx.expect.records if not a["ok"]]

    def test_each_broken_rule_fails_the_scenario_that_covers_it(self):
        for module, label, old, new, expected in self.CASES:
            with self.subTest(label):
                failed = self.failed_names(module, broken_source(old, new))
                self.assertNotEqual(failed, [], label)
                if expected:
                    self.assertIn(expected, failed)

    def test_a_missing_mod_fails_loudly(self):
        game = running_game(with_mod=False)
        self.addCleanup(game.close)
        with self.assertRaises(ModDidNotAnswer) as caught:
            raid_timeline.run(RaidContext(game))
        self.assertIn("mod did not answer: RaidStandIn", str(caught.exception))


class SuiteFileTests(unittest.TestCase):
    def test_the_ab_suite_compares_two_size_settings_of_the_tiers_scenario(self):
        from suitelib.suitefile import load_suite
        entry = load_suite("raid-size-ab", Path(__file__).resolve().parent.parent / "suites").entries[0]
        self.assertEqual(entry.scenario, raid_tiers.NAME)
        self.assertEqual([v.env for v in entry.variants], [{"RAID_STANDIN_SIZE_PERCENT": "100"}, {"RAID_STANDIN_SIZE_PERCENT": "150"}])


class ScenarioMetadataTests(unittest.TestCase):
    def test_each_scenario_has_a_limit_a_description_and_covers(self):
        expected = {raid_timeline: ["T1", "T3"], raid_seasons: ["T5", "P6"], raid_behavior: ["R1", "R4", "R6"],
                    raid_tiers: ["D1", "D2", "D3"], raid_sack: ["S2", "S3"], raid_politics: ["P1", "P2", "P4"]}
        for module, covers in expected.items():
            self.assertLessEqual(module.LIMIT_S, 120)
            self.assertIn("stand-in mod: a toy model that proves the harness method, not the real mod", module.DESCRIPTION.lower())
            self.assertEqual(module.COVERS, covers)
            self.assertFalse(getattr(module, "HIDDEN", False))
            self.assertEqual(module.NAME, module.__name__.split(".")[-1].replace("_", "-"))


if __name__ == "__main__":
    unittest.main()
