"""Tests for the battle helpers, the battle actions, the unit table actions, `run_fight` and `variant_option` (spec 10, S7, P5, C1, C2). No game."""

import unittest
from types import SimpleNamespace

import runlib_path  # noqa: F401
from runlib import battle
from runlib.actions import ActionNotPossible, Actions
from runlib.expectations import Expectations
from runlib.fights import FightResult, run_fight
from runlib.scenario_context import ScenarioContext
from runlib.waiting import WaitTimeout


def squad(squad_id, side, template, initial, alive, xp_mean=0.0, xp_max=0.0, units=None):
    row = {"id": squad_id, "side": side, "template": template, "initial": initial, "alive": alive, "xp_mean": xp_mean, "xp_max": xp_max}
    if units is not None:
        row["units"] = units
    return row


def state_of(*squads):
    by_side, by_template = {}, {}
    for item in squads:
        for table, key in ((by_side, item["side"]), (by_template, f"{item['side']}:{item['template']}")):
            entry = table.setdefault(key, {"initial": 0, "alive": 0})
            entry["initial"] += item["initial"]
            entry["alive"] += item["alive"]
    return {"squads": list(squads), "by_side": by_side or [], "by_template": by_template or [], "ms": 1}


class HelperTests(unittest.TestCase):
    def setUp(self):
        self.state = state_of(squad(8, "player", "spearMilitia", 32, 20, 1.5), squad(9, "player", "bowMilitia", 32, 32, 0.0),
                              squad(10, "bandit", "militiaFoot", 32, 8, 0.5))

    def test_counts_by_side_and_template(self):
        self.assertEqual((battle.initial(self.state, "player"), battle.alive(self.state, "player")), (64, 52))
        self.assertEqual(battle.casualties(self.state, "player", "spearMilitia"), 12)
        self.assertEqual(battle.casualties(self.state, "bandit"), 24)
        self.assertEqual(battle.alive(self.state, "bandit", "nobody"), 0)

    def test_rates_and_ratio(self):
        self.assertAlmostEqual(battle.casualty_rate(self.state, "bandit"), 0.75)
        self.assertEqual(battle.casualty_rate(self.state, "player", "nobody"), 0.0)
        self.assertAlmostEqual(battle.casualty_ratio(self.state, "bandit", "player"), 24 / 12)

    def test_the_ratio_is_defined_when_the_winner_lost_nobody(self):
        state = state_of(squad(8, "player", "a", 10, 10), squad(9, "bandit", "b", 10, 0))
        self.assertEqual(battle.casualty_ratio(state, "bandit", "player"), 10)

    def test_empty_maps_arrive_as_lists(self):
        empty = {"squads": [], "by_side": [], "by_template": [], "ms": 0}
        self.assertEqual((battle.alive(empty, "player"), battle.casualties(empty, "bandit", "x"), battle.casualty_rate(empty, "player")), (0, 0, 0.0))
        with self.assertRaises(battle.BattleError):
            battle.alive({"by_side": [1], "by_template": {}, "squads": []}, "player")

    def test_mean_experience_weighs_by_living_units(self):
        self.assertAlmostEqual(battle.mean_experience(self.state, "player"), (1.5 * 20 + 0.0 * 32) / 52)
        self.assertEqual(battle.mean_experience(self.state, "player", "nobody"), 0.0)

    def test_unit_experience_needs_detail_rows(self):
        with self.assertRaisesRegex(battle.BattleError, "detail=True"):
            battle.unit_experience(self.state)
        detailed = state_of(squad(8, "player", "a", 2, 2, units=[{"uid": 5, "xp": 1.0}, {"uid": 6, "xp": 2.5}]))
        self.assertEqual(battle.unit_experience(detailed), {5: 1.0, 6: 2.5})

    def test_fight_over_and_signature(self):
        self.assertFalse(battle.fight_is_over(self.state, "player", "bandit"))
        over = state_of(squad(8, "player", "a", 5, 3), squad(9, "bandit", "b", 5, 0))
        self.assertTrue(battle.fight_is_over(over, "player", "bandit"))
        self.assertNotEqual(battle.alive_signature(self.state), battle.alive_signature(over))

    def test_checks(self):
        for call, good, bad in ((battle.check_side, "player", "ai"), (lambda value: battle.check_name("template", value), "spearMilitia", "bad name"), (battle.check_count, 3, 7),
                                (lambda value: battle.check_offset("dx", value), 2500, 30000), (battle.check_experience, 25, -1)):
            self.assertEqual(call(good), good)
            with self.assertRaises(battle.BattleError):
                call(bad)
        for bad in (True, 1.5, "3", 0):
            with self.assertRaises(battle.BattleError):
                battle.check_count(bad)
        with self.assertRaises(battle.BattleError):
            battle.check_name("template", "1abc")

    def test_offers(self):
        offers = [{"name": "a", "cost": 5}, {"name": "b", "cost": 6}]
        self.assertEqual(battle.offer_names(offers), ["a", "b"])
        self.assertEqual(battle.find_offer(offers, "b")["cost"], 6)
        with self.assertRaisesRegex(battle.BattleError, "not on offer"):
            battle.find_offer(offers, "c")

    def test_row_values(self):
        rows = [{"row": "x", "values": {"maxSize": 3}}]
        self.assertEqual(battle.row_values(rows, "x"), {"maxSize": 3})
        with self.assertRaises(battle.BattleError):
            battle.row_values(rows, "y")


class FakeChannel:
    def __init__(self):
        self.sent = []
        self.answers = {}

    def send(self, command, **fields):
        self.sent.append((command, fields))
        answer = self.answers[command]
        return {"ok": True, **(answer(fields) if callable(answer) else answer)}


class FakeBridge:
    def engine_path(self):
        return "engine"


def make_actions(channel):
    expect = Expectations()
    return Actions(FakeBridge(), expect, [], commands=channel), expect


class ActionTests(unittest.TestCase):
    def test_spawn_units_sends_checked_fields_and_records_the_squads(self):
        channel = FakeChannel()
        channel.answers["spawn_units"] = {"squads": [{"id": 8, "side": "player", "template": "spearMilitia", "units": 32}], "units": 32}
        actions, expect = make_actions(channel)
        record = actions.spawn_units("player", "spearMilitia", dx=2500)
        self.assertTrue(record["ok"])
        self.assertEqual(record["answer"]["units"], 32)
        self.assertEqual(channel.sent[0], ("spawn_units", {"side": "player", "template": "spearMilitia", "count": 1, "dx": 2500, "dy": 0}))
        self.assertTrue(expect.result()["passed"])

    def test_spawn_units_fails_the_scenario_when_no_unit_appears(self):
        channel = FakeChannel()
        channel.answers["spawn_units"] = {"squads": [{"id": 8, "side": "player", "template": "x", "units": 0}], "units": 0}
        actions, expect = make_actions(channel)
        self.assertFalse(actions.spawn_units("player", "spearMilitia")["ok"])
        self.assertFalse(expect.result()["passed"])

    def test_bad_arguments_never_reach_the_game(self):
        channel = FakeChannel()
        actions, _ = make_actions(channel)
        for call in (lambda: actions.spawn_units("ai", "spearMilitia"), lambda: actions.spawn_units("player", "a b"),
                     lambda: actions.spawn_units("player", "x", count=9), lambda: actions.spawn_units("player", "x", dx=1e9),
                     lambda: actions.clear_battle(side="civil"), lambda: actions.set_squad_experience(8, -2),
                     lambda: actions.hire_mercenaries("bad name")):
            with self.assertRaises(battle.BattleError):
                call()
        self.assertEqual(channel.sent, [])

    def test_clear_battle_and_experience(self):
        channel = FakeChannel()
        channel.answers["clear_battle"] = {"killed": 12, "squads_forgotten": 2}
        channel.answers["set_squad_experience"] = lambda fields: {"alive": 5, "changed": 5, "squad": fields["squad"], "value": fields["value"]}
        actions, expect = make_actions(channel)
        self.assertEqual(actions.clear_battle(side="bandit")["after"], 12)
        self.assertEqual(channel.sent[0], ("clear_battle", {"side": "bandit"}))
        self.assertTrue(actions.set_squad_experience(8, 25)["ok"])
        self.assertEqual(channel.sent[1], ("set_squad_experience", {"squad": 8, "value": 25}))
        channel.answers["set_squad_experience"] = {"alive": 5, "changed": 4}
        self.assertFalse(actions.set_squad_experience(8, 25)["ok"])
        self.assertFalse(expect.result()["passed"])

    def hire_channel(self, silver=100, paid=90, offers_after=1, hired_after=1):
        channel = FakeChannel()
        offers = [{"name": "greencaps", "cost": 90, "arrives_in": 11, "units": ["a"]}, {"name": "other", "cost": 50, "arrives_in": 3, "units": ["b"]}]
        channel.answers["mercenary_offers"] = {"offers": offers, "silver": silver, "hired": 0}
        channel.answers["hire_mercenaries"] = {"silver_before": silver, "silver_after": silver - paid, "units": 72, "squads": [],
                                               "hired_before": 0, "hired_after": hired_after, "offers_after": offers_after}
        return channel

    def test_hire_checks_the_cost_the_units_and_the_offer_list(self):
        actions, expect = make_actions(self.hire_channel())
        record = actions.hire_mercenaries("greencaps")
        self.assertTrue(record["ok"])
        self.assertEqual((record["before"], record["after"]), (100, 10))
        self.assertTrue(expect.result()["passed"])

    def test_hire_with_too_little_silver_is_refused_before_the_game_is_asked(self):
        channel = self.hire_channel(silver=89)
        actions, _ = make_actions(channel)
        with self.assertRaisesRegex(battle.BattleError, "not enough silver"):
            actions.hire_mercenaries("greencaps")
        self.assertEqual([command for command, _ in channel.sent], ["mercenary_offers"])

    def test_hire_of_a_company_that_is_not_offered_is_refused(self):
        actions, _ = make_actions(self.hire_channel())
        with self.assertRaisesRegex(battle.BattleError, "not on offer"):
            actions.hire_mercenaries("nobody")

    def test_hire_fails_the_scenario_on_a_wrong_price_or_an_offer_that_stays(self):
        for channel in (self.hire_channel(paid=95), self.hire_channel(offers_after=2), self.hire_channel(hired_after=0)):
            actions, expect = make_actions(channel)
            self.assertFalse(actions.hire_mercenaries("greencaps")["ok"])
            self.assertFalse(expect.result()["passed"])

    def test_the_unit_table_actions_send_the_table_only_when_it_is_not_items(self):
        channel = FakeChannel()
        channel.answers["datatable_info"] = {"info": {"name_count": 24}}
        channel.answers["datatable_read"] = lambda fields: {"values": {fields["field"]: 5}}
        channel.answers["datatable_rows"] = {"rows": [{"row": "a", "values": {}}]}
        channel.answers["datatable_write"] = lambda fields: {"change": {"before": 32, "after": fields["value"]}}
        actions, expect = make_actions(channel)
        actions.datatable_info()
        actions.datatable_read(17, "Value")
        self.assertEqual(channel.sent[0], ("datatable_info", {}))
        self.assertEqual(channel.sent[1], ("datatable_read", {"row": "17", "field": "Value"}))
        actions.datatable_info("units")
        self.assertEqual(actions.datatable_read("spearMilitia", "maxSize", table="units"), 5)
        self.assertEqual(channel.sent[3], ("datatable_read", {"row": "spearMilitia", "field": "maxSize", "table": "units"}))
        self.assertEqual(len(actions.datatable_rows()), 1)
        self.assertEqual(channel.sent[4], ("datatable_rows", {"table": "units"}))
        self.assertTrue(actions.datatable_write("spearMilitia", "maxSize", 10)["ok"])
        self.assertEqual(channel.sent[5][1], {"row": "spearMilitia", "field": "maxSize", "value": 10, "table": "units"})
        self.assertTrue(expect.result()["passed"])

    def test_a_write_that_does_not_hold_fails_the_scenario(self):
        channel = FakeChannel()
        channel.answers["datatable_write"] = {"change": {"before": 32, "after": 32}}
        actions, expect = make_actions(channel)
        self.assertFalse(actions.datatable_write("spearMilitia", "maxSize", 10)["ok"])
        self.assertFalse(expect.result()["passed"])

    def test_an_unknown_table_is_not_possible(self):
        actions, _ = make_actions(FakeChannel())
        with self.assertRaisesRegex(ActionNotPossible, "unknown table"):
            actions.datatable_info("monsters")

    def test_the_new_actions_are_listed(self):
        actions, _ = make_actions(FakeChannel())
        for name in ("spawn_units", "battle_state", "clear_battle", "set_squad_experience", "mercenary_offers", "hire_mercenaries",
                     "datatable_rows", "datatable_write"):
            self.assertIn(name, actions.available())


class FightTests(unittest.TestCase):
    """`run_fight` with a scripted state: the fight ends when a side is gone, when it is calm, or at the time limit."""

    class Context:
        def __init__(self, states, raise_timeout=False):
            self.states = list(states)
            self.calls = []
            self.raise_timeout = raise_timeout
            self.time = SimpleNamespace(set_speed=lambda speed: self.calls.append(("speed", speed)), pause=lambda: self.calls.append(("pause",)))
            self.actions = SimpleNamespace(battle_state=self.battle_state)
            self.log = SimpleNamespace(info=lambda message: None)
            self.popups = lambda: None

        def battle_state(self, detail=False):
            state = self.states.pop(0) if len(self.states) > 1 else self.states[0]
            return state

        def run_until(self, predicate, timeout_s, **options):
            for polls in range(1, 50):
                if predicate():
                    return SimpleNamespace(wall_s=float(polls))
            raise WaitTimeout("timeout: scripted")

    def test_ends_when_one_side_is_gone(self):
        ctx = self.Context([state_of(squad(8, "player", "a", 5, 5), squad(9, "bandit", "b", 5, 3)),
                            state_of(squad(8, "player", "a", 5, 4), squad(9, "bandit", "b", 5, 0))])
        result = run_fight(ctx)
        self.assertEqual((result.reason, result.finished), ("one side gone", True))
        self.assertEqual(ctx.calls, [("speed", 3), ("pause",)])

    def test_ends_when_no_squad_loses_a_unit_for_the_calm_polls(self):
        still = state_of(squad(8, "player", "a", 5, 4), squad(9, "bandit", "b", 5, 3))
        result = run_fight(self.Context([still]), calm_polls=3)
        self.assertEqual(result.reason, "calm")

    def test_a_timeout_is_a_result_and_the_game_is_paused(self):
        busy = [state_of(squad(8, "player", "a", 99, 99 - n), squad(9, "bandit", "b", 99, 99)) for n in range(60)]
        ctx = self.Context(busy)
        result = run_fight(ctx)
        self.assertEqual((result.reason, result.finished), ("timeout", False))
        self.assertEqual(ctx.calls[-1], ("pause",))
        self.assertIsInstance(result, FightResult)


class VariantOptionTests(unittest.TestCase):
    def option(self, env):
        return ScenarioContext.variant_option(SimpleNamespace(phase=SimpleNamespace(config={"env": env})), "COUNTERS_PLAYER", "spearMilitia")

    def test_the_value_of_the_run_or_the_default(self):
        self.assertEqual(self.option({"COUNTERS_PLAYER": "retinue_tier3"}), "retinue_tier3")
        self.assertEqual(self.option({}), "spearMilitia")

    def test_a_masked_value_is_an_error(self):
        with self.assertRaisesRegex(ValueError, "no usable value"):
            self.option({"COUNTERS_PLAYER": "***"})




class SuiteFileTests(unittest.TestCase):
    def test_the_counters_suite_compares_two_player_templates_and_expects_fewer_losses_for_the_heavy_one(self):
        from pathlib import Path
        from suitelib.suitefile import load_suite
        entry = load_suite("counters-ab", Path(__file__).resolve().parent.parent / "suites").entries[0]
        self.assertEqual(entry.scenario, "counters-ab")
        self.assertEqual([variant.env["COUNTERS_PLAYER"] for variant in entry.variants], ["spearMilitia", "retinue_tier3"])
        self.assertEqual((entry.expect.metric, entry.expect.direction), ("player_loss_rate", "lower"))
        for variant in entry.variants:
            for name in ("COUNTERS_PLAYER", "COUNTERS_BANDIT"):
                battle.check_name(name, variant.env[name])


if __name__ == "__main__":
    unittest.main()
