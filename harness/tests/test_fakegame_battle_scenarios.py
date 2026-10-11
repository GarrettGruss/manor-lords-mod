"""The four battle scenarios (unit-data, mercenary-hire, veterancy, counters-ab) against the REAL Lua files in the fake game kit.

The chain: scenario code -> Actions -> CommandChannel -> request files -> HarnessActions -> HarnessBattle / HarnessDataTable -> a fake world.
Only the game is fake, and so is the fight (a fixed number of deaths in each step). This checks the logic of the scenarios and the Lua modules.
It does NOT prove that the real game behaves the same: the real runs are listed in spike-S7.md, spike-P5.md, spike-C2.md and spike-C1.md.
"""

import unittest

import fakegame_path  # noqa: F401
import runlib_path  # noqa: F401
from battle_support import BattleContext, BattleWorld
from scenarios import counters_ab, mercenary_hire, unit_data, veterancy


class ScenarioTestCase(unittest.TestCase):
    def run_scenario(self, module, world_options=None, **context_options):
        world = BattleWorld(**(world_options or {}))
        self.addCleanup(world.close)
        ctx = BattleContext(world, **context_options)
        result = module.run(ctx)
        return result, [a["name"] for a in result["asserts"] if not a["ok"]], ctx


class UnitDataTests(ScenarioTestCase):
    def test_passes_and_restores_the_row(self):
        result, failed, ctx = self.run_scenario(unit_data)
        self.assertEqual(failed, [])
        self.assertGreaterEqual(len(result["asserts"]), 15)
        self.assertEqual(ctx.world.world.rows["spearMilitia"].maxSize, 32)
        self.assertEqual(ctx.metrics, {"squad_size_changed": 10})

    def test_a_table_with_too_few_rows_fails(self):
        world = BattleWorld()
        self.addCleanup(world.close)
        ctx = BattleContext(world)
        saved = unit_data.MIN_ROWS
        unit_data.MIN_ROWS = 50
        self.addCleanup(setattr, unit_data, "MIN_ROWS", saved)
        result = unit_data.run(ctx)
        self.assertFalse(result["passed"])

    def test_the_row_is_restored_even_when_a_check_raises(self):
        world = BattleWorld()
        self.addCleanup(world.close)
        ctx = BattleContext(world)
        original = unit_data.squad_size
        calls = []

        def broken(ctx_, template):
            calls.append(template)
            if len(calls) == 2:
                raise RuntimeError("boom")
            return original(ctx_, template)

        unit_data.squad_size = broken
        self.addCleanup(setattr, unit_data, "squad_size", original)
        with self.assertRaisesRegex(RuntimeError, "boom"):
            unit_data.run(ctx)
        self.assertEqual(world.world.rows["spearMilitia"].maxSize, 32)


class MercenaryHireTests(ScenarioTestCase):
    def test_passes_with_a_priced_company(self):
        result, failed, ctx = self.run_scenario(mercenary_hire)
        self.assertEqual(failed, [])
        self.assertEqual(ctx.metrics["mercenary_cost"], 50)
        self.assertEqual(ctx.metrics["mercenary_units"], 54)
        self.assertEqual(ctx.world.world.living("player"), 0, "the scenario clears the hired units")

    def test_the_cheapest_offer_is_chosen(self):
        self.assertEqual(mercenary_hire.cheapest([{"name": "a", "cost": 90}, {"name": "b", "cost": 50}])["name"], "b")

    def test_a_game_that_charges_more_than_the_listed_cost_fails(self):
        result, failed, _ = self.run_scenario(mercenary_hire, world_options={"overcharge": 5})
        self.assertFalse(result["passed"])
        self.assertIn("silver paid", failed)

    def test_no_offer_fails_with_a_clear_reason(self):
        result, failed, _ = self.run_scenario(mercenary_hire, world_options={"no_offers": True})
        self.assertFalse(result["passed"])
        self.assertIn("companies on offer", failed)


class VeterancyTests(ScenarioTestCase):
    def test_passes_and_restores_the_attacker_size(self):
        result, failed, ctx = self.run_scenario(veterancy)
        self.assertEqual(failed, [])
        self.assertEqual(ctx.world.world.rows["militiaFoot"].maxSize, 32)
        self.assertGreater(ctx.metrics["experience_after_fight_2"], ctx.metrics["experience_after_fight_1"])
        self.assertIn(("run_game_days", 1, veterancy.DAY_SPEED), ctx.time.calls)

    def test_a_game_that_forgets_experience_fails(self):
        world = BattleWorld()
        self.addCleanup(world.close)
        ctx = BattleContext(world)
        original_tick = world.tick

        def forgetful(*args):
            alive = original_tick(*args)
            if ctx.time.running and world.world.living("bandit") == 0:
                world.game.exec("for _, o in ipairs(FindAllOf('SMUnit') or {}) do o.combatExperience = 0.0 end")
            return alive

        world.tick = forgetful
        result = veterancy.run(ctx)
        self.assertFalse(result["passed"])

    def test_a_fight_without_casualties_fails(self):
        world = BattleWorld()
        self.addCleanup(world.close)
        ctx = BattleContext(world, kills=(0, 0, 0.0))
        result = veterancy.run(ctx)
        self.assertFalse(result["passed"])
        failed = [a["name"] for a in result["asserts"] if not a["ok"]]
        self.assertIn("player casualties in fight 1", failed)

    def test_a_wiped_out_defender_side_fails_loudly(self):
        world = BattleWorld()
        self.addCleanup(world.close)
        ctx = BattleContext(world, kills=(60, 1, 0.4))
        with self.assertRaises(StopIteration):
            veterancy.run(ctx)
        self.assertEqual(world.world.rows["militiaFoot"].maxSize, 32, "the row is restored")


class CountersTests(ScenarioTestCase):
    def test_default_variant_reports_loss_rates(self):
        result, failed, ctx = self.run_scenario(counters_ab)
        self.assertEqual(failed, [])
        self.assertEqual(set(ctx.metrics), {"player_loss_rate", "bandit_loss_rate", "loss_ratio", "player_casualties", "bandit_casualties", "fight_wall_s"})
        self.assertAlmostEqual(ctx.metrics["bandit_loss_rate"], 1.0)
        self.assertEqual(sum(1 for call in ctx.time.calls if call[0] == "set_speed"), counters_ab.DEFAULT_ROUNDS)

    def test_the_variant_chooses_the_templates_and_the_rounds(self):
        variant = {"COUNTERS_PLAYER": "retinue_tier3", "COUNTERS_BANDIT": "Brigands", "COUNTERS_ROUNDS": "2"}
        result, failed, ctx = self.run_scenario(counters_ab, variant=variant)
        self.assertEqual(failed, [])
        self.assertEqual(sum(1 for call in ctx.time.calls if call[0] == "set_speed"), 2)
        self.assertTrue(any("retinue_tier3 against bandit Brigands, 2 rounds" in line for line in ctx.logged))

    def test_a_loss_rate_follows_the_fight_rule(self):
        _, _, strong = self.run_scenario(counters_ab, kills=(1, 4, 0.0))
        _, _, weak = self.run_scenario(counters_ab, kills=(4, 1, 0.0))
        self.assertLess(strong.metrics["player_loss_rate"], weak.metrics["player_loss_rate"])

    def test_bad_options_raise(self):
        for variant in ({"COUNTERS_ROUNDS": "0"}, {"COUNTERS_ROUNDS": "9"}, {"COUNTERS_ROUNDS": "x"}, {"COUNTERS_PLAYER": "bad name"}):
            world = BattleWorld()
            self.addCleanup(world.close)
            with self.assertRaises(ValueError, msg=variant):
                counters_ab.run(BattleContext(world, variant=variant))

    def test_squads_that_never_meet_fail_the_scenario(self):
        result, failed, _ = self.run_scenario(counters_ab, kills=(0, 0, 0.0))
        self.assertFalse(result["passed"])
        self.assertTrue(any("casualties of both sides" in name for name in failed))

    def test_a_fight_that_never_ends_is_a_timeout_result_and_the_game_is_paused(self):
        world = BattleWorld()
        self.addCleanup(world.close)
        ctx = BattleContext(world, kills=(0, 0, 0.0), max_polls=2)
        result = counters_ab.run(ctx)
        self.assertFalse(result["passed"])
        self.assertIn("round 1: the fight ended", [a["name"] for a in result["asserts"] if not a["ok"]])
        self.assertEqual(ctx.time.calls[-1], ("pause",))
        self.assertFalse(ctx.time.running)


class MetadataTests(unittest.TestCase):
    def test_scenarios_carry_the_metadata_the_coverage_tool_reads(self):
        for module, covers in ((unit_data, ["C3"]), (mercenary_hire, ["P5"]), (veterancy, ["C2"]), (counters_ab, ["C1"])):
            self.assertEqual(module.COVERS, covers)
            self.assertIsInstance(module.LIMIT_S, int)
            self.assertLessEqual(module.LIMIT_S, 300, "no LONG_REASON needed")
            self.assertTrue(module.NAME and module.DESCRIPTION)


if __name__ == "__main__":
    unittest.main()
