"""Tests for the checking logic of the action kit and the command channel. No game."""

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import runlib_path  # noqa: F401
from runlib import phases
from runlib.actions import (
    NOT_POSSIBLE,
    ActionError,
    ActionNotPossible,
    Actions,
    changed_by,
    equals,
    increased,
    item_id,
    near,
    season_day,
)
from runlib.commands import CommandChannel, CommandError
from runlib.expectations import Expectations
from runlib.game import GameInstall
from runlib.runfolder import create_run_folder
from runlib.runner import PhaseContext
from runlib.scenario import SCENARIOS
from runlib.scenario_context import ScenarioContext

REGION = "Map:Region.Home"
OTHER_REGION = "Map:Region.Far"


class FakeBridge:
    """A fake of the Bridge methods that actions use. `ignore` names calls that have no effect (a broken game)."""

    def __init__(self, ignore=(), world_loaded=True):
        self.ignore = set(ignore)
        self.world_loaded = world_loaded
        self.values = {
            ("player", "silver"): 0, ("player", "influence"): 0, ("player", "kingsFavour"): 0,
            ("player", "InBox"): [],
            ("calendar", "day"): 61, ("calendar", "Season"): 1, ("calendar", "raining"): 0.0,
            (REGION, "Approval"): 50, (REGION, "regionalWealth"): 50, (REGION, "settlementLevel"): 0,
            (REGION, "regionName"): "Home", (OTHER_REGION, "regionName"): "Far",
        }
        self.stock = {16: 5}
        self.units = 10
        self.calls = []

    def engine_path(self):
        if not self.world_loaded:
            raise RuntimeError("No RTSMultiEngineCPP object exists.")
        return "engine"

    def player_path(self):
        return "player"

    def calendar_path(self, engine=None):
        return "calendar"

    def player_region_path(self):
        return REGION

    def region_paths(self, engine=None):
        return [REGION, OTHER_REGION]

    def read_property(self, ref, name):
        return self.values[(ref, name)]

    def write_property(self, ref, name, value):
        self.calls.append(("set", ref, name, value))
        if "set" not in self.ignore:
            self.values[(ref, name)] = value

    def count_objects(self, class_name):
        return self.units

    def call_function(self, ref, function, args=None):
        args = args or []
        self.calls.append((ref, function, args))
        if function in self.ignore:
            return None
        if function == "changeSilver":
            self.values[("player", "silver")] += args[0]
        elif function == "changeInfluence":
            self.values[("player", "influence")] += int(args[0])
        elif function == "changeKingsFavour":
            self.values[("player", "kingsFavour")] += args[0]
        elif function == "setDay":
            self.values[("calendar", "day")] = args[0]
            self.values[("calendar", "Season")] = {10: 0, 100: 1, 200: 2, 300: 3}[args[0]]
        elif function == "addRegionalWealth":
            self.values[(ref, "regionalWealth")] += args[0]
        elif function == "SetSettlementLevel":
            self.values[(REGION, "settlementLevel")] = args[0]
        elif function == "GiveItemByID":
            self.stock[args[0]] = self.stock.get(args[0], 0) + args[1]
        elif function == "getStockOfGood":
            return self.stock.get(args[0], 0)
        elif function == "SpawnBanditSquad":
            self.units += 18
        return None


class FakeChannel:
    def __init__(self, bridge, deliver=True):
        self.bridge = bridge
        self.deliver = deliver
        self.sent = []

    def send(self, command, **fields):
        self.sent.append((command, fields))
        if self.deliver:
            self.bridge.values[("player", "InBox")].append({"paras": fields["paragraphs"]})
        return {"ok": True}


def make_actions(**bridge_options):
    bridge = FakeBridge(**bridge_options)
    expect = Expectations()
    notes = []
    actions = Actions(bridge, expect, notes, commands=FakeChannel(bridge))
    return actions, bridge, expect, notes


class CheckFunctionTest(unittest.TestCase):
    def test_changed_by(self):
        self.assertTrue(changed_by(100)(0, 100))
        self.assertTrue(changed_by(-50)(200, 150))
        self.assertFalse(changed_by(100)(0, 99))

    def test_equals_and_increased(self):
        self.assertTrue(equals(5)(0, 5))
        self.assertFalse(equals(5)(0, 6))
        self.assertTrue(increased(1, 2))
        self.assertFalse(increased(2, 2))

    def test_near_allows_float_noise(self):
        self.assertTrue(near(0.8)(0, 0.800000011920929))
        self.assertFalse(near(0.8)(0, 0.5))
        self.assertFalse(near(0.8)(0, None))

    def test_season_day_and_item_id(self):
        self.assertEqual(season_day("winter"), 10)
        with self.assertRaisesRegex(ActionNotPossible, "unknown season"):
            season_day("monsoon")
        self.assertEqual(item_id(7), 7)
        self.assertEqual(item_id("Timber"), 16)
        with self.assertRaisesRegex(ActionNotPossible, "was not checked"):
            item_id("Gold")


class PlayerActionTest(unittest.TestCase):
    def test_add_silver_returns_the_record_and_a_note(self):
        actions, bridge, expect, notes = make_actions()
        record = actions.add_silver(100)
        self.assertEqual((record["action"], record["ok"], record["before"], record["after"]), ("add_silver", True, 0, 100))
        self.assertEqual(notes, ["add_silver{'amount': 100}: 0 -> 100 ok"])
        self.assertEqual(expect.records, [])  # a good action adds no assertion

    def test_negative_amount(self):
        actions, bridge, _, _ = make_actions()
        actions.add_silver(200)
        self.assertTrue(actions.add_silver(-50)["ok"])
        self.assertEqual(bridge.values[("player", "silver")], 150)

    def test_failed_readback_gives_ok_false_and_a_failed_assertion(self):
        actions, _, expect, notes = make_actions(ignore={"changeSilver"})
        record = actions.add_silver(100)
        self.assertFalse(record["ok"])
        self.assertFalse(expect.result()["passed"])
        self.assertIn("FAILED", notes[0])

    def test_set_silver_and_influence(self):
        actions, bridge, _, _ = make_actions()
        self.assertTrue(actions.set_silver(500)["ok"])
        self.assertTrue(actions.set_influence(50)["ok"])
        self.assertEqual(bridge.values[("player", "influence")], 50)

    def test_set_that_the_game_ignores_fails(self):
        actions, _, expect, _ = make_actions(ignore={"set"})
        self.assertFalse(actions.set_silver(500)["ok"])
        self.assertFalse(expect.result()["passed"])

    def test_influence_is_sent_as_a_float(self):
        actions, bridge, _, _ = make_actions()
        actions.add_influence(10)
        self.assertEqual(bridge.calls[-1], ("player", "changeInfluence", [10.0]))
        self.assertIsInstance(bridge.calls[-1][2][0], float)

    def test_kings_favour(self):
        actions, _, _, _ = make_actions()
        self.assertTrue(actions.add_kings_favour(5)["ok"])


class CalendarActionTest(unittest.TestCase):
    def test_set_day(self):
        actions, _, _, _ = make_actions()
        record = actions.set_day(200)
        self.assertTrue(record["ok"])
        self.assertEqual(record["after"], {"day": 200, "Season": 2})

    def test_set_season_checks_day_and_season(self):
        actions, bridge, _, _ = make_actions()
        self.assertTrue(actions.set_season("autumn")["ok"])
        self.assertEqual(bridge.calls[-1], ("engine", "setDay", [300]))

    def test_set_season_fails_when_the_season_does_not_change(self):
        actions, bridge, expect, _ = make_actions(ignore={"setDay"})
        self.assertFalse(actions.set_season("winter")["ok"])
        self.assertFalse(expect.result()["passed"])

    def test_unknown_season_is_not_possible(self):
        actions, _, _, _ = make_actions()
        with self.assertRaises(ActionNotPossible):
            actions.set_season("monsoon")


class RegionActionTest(unittest.TestCase):
    def test_set_region_value_in_the_player_region(self):
        actions, bridge, _, _ = make_actions()
        record = actions.set_region_value("Approval", 80)
        self.assertEqual((record["ok"], record["before"], record["after"]), (True, 50, 80))

    def test_region_by_name(self):
        actions, bridge, _, _ = make_actions()
        bridge.values[(OTHER_REGION, "Approval")] = 10
        record = actions.set_region_value("Approval", 33, region="Far")
        self.assertEqual((record["before"], record["after"]), (10, 33))

    def test_unknown_region_is_an_error(self):
        actions, _, _, _ = make_actions()
        with self.assertRaisesRegex(ActionError, "no region named"):
            actions.set_region_value("Approval", 33, region="Nowhere")

    def test_value_that_was_not_checked_is_not_possible(self):
        actions, _, _, _ = make_actions()
        with self.assertRaisesRegex(ActionNotPossible, "was not checked"):
            actions.set_region_value("population", 50)

    def test_supplies_food_note_says_the_game_recalculates_it(self):
        actions, bridge, _, _ = make_actions()
        bridge.values[(REGION, "supplies_food")] = 3.0
        record = actions.set_region_value("supplies_food", 55)
        self.assertTrue(record["ok"])
        self.assertIn("recalculates", record["note"])

    def test_add_regional_wealth_and_settlement_level(self):
        actions, _, _, _ = make_actions()
        self.assertTrue(actions.add_regional_wealth(25)["ok"])
        self.assertTrue(actions.set_settlement_level(1)["ok"])


class GoodsAndWorldActionTest(unittest.TestCase):
    def test_give_item_by_id_and_by_name(self):
        actions, bridge, _, _ = make_actions()
        self.assertTrue(actions.give_item(1, 40)["ok"])
        record = actions.give_item("Timber", 7)
        self.assertEqual((record["before"], record["after"]), (5, 12))
        self.assertEqual(bridge.calls[-2], ("first:MLCheatManager", "GiveItemByID", [16, 7]))

    def test_give_item_with_unknown_name(self):
        actions, _, _, _ = make_actions()
        with self.assertRaises(ActionNotPossible):
            actions.give_item("Gold", 1)

    def test_set_weather(self):
        actions, _, _, _ = make_actions()
        record = actions.set_weather("raining", 1)
        self.assertTrue(record["ok"])
        self.assertIn("back toward", record["note"])
        with self.assertRaises(ActionNotPossible):
            actions.set_weather("lava", 1)

    def test_spawn_bandit_squad(self):
        actions, _, _, _ = make_actions()
        record = actions.spawn_bandit_squad()
        self.assertEqual((record["before"], record["after"]), (10, 28))

    def test_spawn_that_adds_no_unit_fails(self):
        actions, _, expect, _ = make_actions(ignore={"SpawnBanditSquad"})
        self.assertFalse(actions.spawn_bandit_squad()["ok"])
        self.assertFalse(expect.result()["passed"])


class LetterActionTest(unittest.TestCase):
    def test_send_letter_checks_the_inbox(self):
        actions, _, _, _ = make_actions()
        record = actions.send_letter(["welcome_from_hildebolt"])
        self.assertTrue(record["ok"])
        self.assertEqual((record["before"]["count"], record["after"]["count"]), (0, 1))

    def test_letter_that_does_not_arrive_fails(self):
        bridge = FakeBridge()
        expect = Expectations()
        actions = Actions(bridge, expect, [], commands=FakeChannel(bridge, deliver=False))
        self.assertFalse(actions.send_letter(["welcome_from_hildebolt"])["ok"])
        self.assertFalse(expect.result()["passed"])

    def test_paragraph_that_was_not_checked(self):
        actions, _, _, _ = make_actions()
        with self.assertRaisesRegex(ActionNotPossible, "was not checked"):
            actions.send_letter(["some_other_paragraph"])

    def test_no_channel(self):
        actions = Actions(FakeBridge())
        with self.assertRaisesRegex(ActionNotPossible, "no command channel"):
            actions.send_letter(["welcome_from_hildebolt"])


class BanditActionInputTest(unittest.TestCase):
    """The checks run before any command is sent (spec 15)."""

    def test_bad_inputs_are_refused_before_a_command_is_sent(self):
        actions = Actions(FakeBridge())
        with self.assertRaisesRegex(ActionError, "tag must be"):
            actions.bandit_tag("peace_treaty")
        for silver in (-1, 1000000, 2.5, True):
            with self.assertRaisesRegex(ActionError, "silver must be"):
                actions.bandit_settle_offer(silver)
        with self.assertRaisesRegex(ActionError, "mode must be"):
            actions.homeless_rebel(1, mode="fly")
        for count in (0, 7, True):
            with self.assertRaisesRegex(ActionError, "count must be"):
                actions.homeless_rebel(count)
        with self.assertRaisesRegex(ActionError, "source must be"):
            actions.bandit_turn(1, source="sky")
        with self.assertRaisesRegex(ActionError, "count must be"):
            actions.bandit_spawn_at(0, 0, count=0)
        with self.assertRaisesRegex(ActionError, "squad must be"):
            actions.bandit_kill_squads(0)
        with self.assertRaisesRegex(ActionError, "count must be"):
            actions.bandit_kill_squads(5, count=11)
        with self.assertRaisesRegex(ActionError, "max_dist must be"):
            actions.forest_spot(min_dist=9000, max_dist=3000)
        with self.assertRaisesRegex(ActionError, "min_dist must be"):
            actions.forest_spot(min_dist=-1)


class ScriptedChannel:
    """Answers each command with a fixed dict and remembers what was sent."""

    def __init__(self, answers):
        self.answers = answers
        self.sent = []

    def send(self, command, **fields):
        self.sent.append((command, fields))
        return {"ok": True, **self.answers.get(command, {})}


class RebelRallyTest(unittest.TestCase):
    SPOTS = {"spots": [{"x": -35225, "y": -66708, "z": 5143, "trees": 10}, {"x": -26236, "y": -26266, "z": -154, "trees": 10}]}

    def test_the_rally_uses_the_forest_spot_nearest_to_the_waypoint(self):
        channel = ScriptedChannel({"forest_spot": self.SPOTS, "bandit_spawn_at": {"squads": [{"id": 32}]}})
        actions = Actions(FakeBridge(), Expectations(), [], commands=channel)
        answer = actions.rebel_rally(count=2)
        self.assertEqual(answer["spot"]["x"], -26236)
        self.assertEqual([name for name, _ in channel.sent], ["forest_spot", "sack_people", "bandit_spawn_at"])
        self.assertEqual(channel.sent[1][1], {"count": 2})

    def test_no_forest_spot_fails_loudly(self):
        actions = Actions(FakeBridge(), Expectations(), [], commands=ScriptedChannel({"forest_spot": {"spots": []}}))
        with self.assertRaisesRegex(ActionError, "no forest spot"):
            actions.rebel_rally()

    def test_the_fallback_kills_the_squad_then_sends_a_raid(self):
        channel = ScriptedChannel({"bandit_kill_squads": {"killed": 18}})
        actions = Actions(FakeBridge(), Expectations(), [], commands=channel)
        answer = actions.rebel_fallback_attack(32)
        self.assertEqual(answer["killed"], 18)
        self.assertEqual([name for name, _ in channel.sent], ["bandit_kill_squads", "spawn_raiders"])


class RebelRaidRallyTest(unittest.TestCase):
    def test_it_sends_the_count(self):
        channel = ScriptedChannel({"rebel_raid_rally": {"ok": True, "squads": [34]}})
        actions = Actions(FakeBridge(), Expectations(), [], commands=channel)
        self.assertEqual(actions.rebel_raid_rally(count=3)["squads"], [34])
        self.assertEqual(channel.sent, [("rebel_raid_rally", {"count": 3})])

    def test_bad_counts_are_refused_before_any_command(self):
        channel = ScriptedChannel({})
        actions = Actions(FakeBridge(), Expectations(), [], commands=channel)
        for count in (0, 7, True, "2"):
            with self.assertRaisesRegex(ActionError, "count must be"):
                actions.rebel_raid_rally(count=count)
        self.assertEqual(channel.sent, [])


class DispatchTest(unittest.TestCase):
    def test_every_not_possible_name_raises_with_its_reason(self):
        actions, _, _, _ = make_actions()
        for name, reason in NOT_POSSIBLE.items():
            with self.assertRaises(ActionNotPossible) as caught:
                getattr(actions, name)("x")
            self.assertIn(reason, str(caught.exception))

    def test_unknown_action_lists_the_available_ones(self):
        actions, _, _, _ = make_actions()
        with self.assertRaisesRegex(ActionNotPossible, "unknown action.*add_silver"):
            actions.fly_to_moon()

    def test_run_by_name(self):
        actions, _, _, _ = make_actions()
        self.assertTrue(actions.run("add_silver", 5)["ok"])
        with self.assertRaises(ActionNotPossible):
            actions.run("_perform")
        with self.assertRaises(ActionNotPossible):
            actions.run("get_item_info", "x")

    def test_available_has_no_helpers(self):
        names = make_actions()[0].available()
        self.assertIn("add_silver", names)
        self.assertNotIn("run", names)
        self.assertFalse([n for n in names if n.startswith("_")])

    def test_no_world_is_a_precondition_error(self):
        actions, bridge, _, _ = make_actions(world_loaded=False)
        with self.assertRaisesRegex(ActionError, "not loaded"):
            actions.add_silver(1)
        self.assertEqual(bridge.calls, [])  # nothing was changed

    def test_dead_game_stops_the_action(self):
        def dead():
            raise RuntimeError("game is gone")

        actions = Actions(FakeBridge(), ensure_alive=dead)
        with self.assertRaisesRegex(RuntimeError, "game is gone"):
            actions.add_silver(1)

    def test_long_notes_are_cut(self):
        actions, _, _, notes = make_actions()
        actions._record("custom", {}, True, "x" * 500, "y" * 500)
        self.assertLessEqual(len(notes[0]), 140)


class CommandChannelTest(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.folder = Path(temp.name) / "commands"
        self.wall = 0.0
        self.answer = None

    def sleep(self, seconds):
        """Moves the fake time. Then a fake mod answers each request that has no result yet."""
        self.wall += seconds
        if self.answer:
            for request in sorted(self.folder.glob("*.json")):
                if request.name.endswith(".result.json"):
                    continue
                result = self.folder / (request.stem + ".result.json")
                if not result.exists():
                    result.write_text(json.dumps({"id": request.stem, **self.answer}), encoding="utf-8")

    def channel(self, answer, timeout_s=5.0, check_alive=lambda: None):
        self.answer = answer
        return CommandChannel(self.folder, timeout_s, self.sleep, lambda: self.wall, check_alive)

    def test_numbers_count_up_and_the_request_has_the_fields(self):
        channel = self.channel({"ok": True})
        channel.send("ping")
        channel.send("send_letter", sender=2, paragraphs=["a"])
        self.assertEqual(sorted(p.name for p in self.folder.iterdir()),
                         ["0001.json", "0001.result.json", "0002.json", "0002.result.json"])
        request = json.loads((self.folder / "0002.json").read_text(encoding="utf-8"))
        self.assertEqual(request, {"id": "0002", "command": "send_letter", "sender": 2, "paragraphs": ["a"]})

    def test_refusal_raises_with_the_reason(self):
        with self.assertRaisesRegex(CommandError, "refused by the game: no AI lord"):
            self.channel({"ok": False, "error": "no AI lord"}).send("send_letter")

    def test_no_answer_times_out_with_a_hint(self):
        with self.assertRaisesRegex(CommandError, "HarnessActions"):
            self.channel(None, timeout_s=1.0).send("ping")
        self.assertGreaterEqual(self.wall, 1.0)

    def test_a_dead_game_stops_the_wait(self):
        def dead():
            raise RuntimeError("game ended")

        with self.assertRaisesRegex(RuntimeError, "game ended"):
            self.channel(None, check_alive=dead).send("ping")

    def test_no_temp_file_is_left(self):
        self.channel({"ok": True}).send("ping")
        self.assertEqual([p for p in self.folder.iterdir() if p.suffix == ".tmp"], [])


class ScenarioIntegrationTest(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.temp = Path(temp.name)
        self.ctx = PhaseContext(run=create_run_folder(self.temp / "runs", "r1"), config={})
        self.ctx.state["game_popen"] = mock.Mock(poll=mock.Mock(return_value=None))

    def test_result_holds_the_action_notes(self):
        scenario_ctx = ScenarioContext(self.ctx, FakeBridge())
        scenario_ctx.actions.add_silver(10)
        result = scenario_ctx.result()
        self.assertTrue(result["passed"])
        self.assertEqual(len(result["notes"]), 1)

    def test_result_has_no_notes_without_actions(self):
        self.assertNotIn("notes", ScenarioContext(self.ctx, FakeBridge()).result())

    def test_a_scenario_with_an_impossible_action_fails_clearly(self):
        def scenario(ctx):
            ctx.actions.get_item_info("x")
            return ctx.result()

        install = GameInstall(root=self.temp / "game", saved_dir=self.temp / "saved")
        with mock.patch.dict(SCENARIOS, {"impossible": scenario}):
            with mock.patch.object(phases, "configure_bridge_client", return_value=FakeBridge()):
                with mock.patch.object(phases, "take_screenshot"):
                    phases._scenario(install, "impossible")(self.ctx)
        result = self.ctx.state["scenario_result"]
        self.assertFalse(result["passed"])
        self.assertEqual(result["asserts"][0]["name"], "action is possible")
        self.assertIn("get_item_info", result["asserts"][0]["value"])
        self.assertTrue((self.ctx.run.path / "scenario.json").is_file())


if __name__ == "__main__":
    unittest.main()
