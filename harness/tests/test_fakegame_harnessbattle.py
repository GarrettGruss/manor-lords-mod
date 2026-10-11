"""Mock tests for HarnessBattle and the unit table of HarnessDataTable (spec 10, spikes S7, P5, C1, C2) in the fake game kit."""

import json
import unittest

import fakegame_path  # noqa: F401
from battle_support import BattleWorld


class Commands:
    """Send HarnessActions commands as files, like the Python client does."""

    def __init__(self, world: BattleWorld):
        self.world = world
        self.number = 0

    def send(self, command, **fields):
        self.number += 1
        folder = self.world.game.run_dir / "commands"
        folder.mkdir(exist_ok=True)
        (folder / f"{self.number:04d}.json").write_text(json.dumps({"id": f"{self.number:04d}", "command": command, **fields}), encoding="utf-8")
        self.world.game.advance(1)
        return json.loads((folder / f"{self.number:04d}.result.json").read_text(encoding="utf-8"))


class BattleTestCase(unittest.TestCase):
    def setUp(self):
        self.world = BattleWorld()
        self.addCleanup(self.world.close)
        self.send = Commands(self.world).send


class UnitTableTests(BattleTestCase):
    def test_info_of_the_unit_table_names_the_row_struct(self):
        answer = self.send("datatable_info", table="units")
        self.assertTrue(answer["ok"])
        self.assertIn("UnitTemplate", answer["info"]["row_struct"])
        self.assertEqual(answer["info"]["name_count"], 24)

    def test_rows_skip_the_separator_and_list_the_six_number_fields(self):
        answer = self.send("datatable_rows", table="units")
        names = [row["row"] for row in answer["rows"]]
        self.assertEqual(answer["row_count"], 23)
        self.assertNotIn("--------------------------", names)
        self.assertEqual(sorted(answer["rows"][0]["values"]),
                         ["combatExperience", "cost", "maxSize", "minArcheryTraining", "minHouseLv", "minMeleeTraining"])

    def test_read_and_write_a_field_of_a_unit_row(self):
        self.assertEqual(self.send("datatable_read", row="spearMilitia", field="maxSize", table="units")["values"], {"maxSize": 32})
        change = self.send("datatable_write", row="spearMilitia", field="maxSize", value=10, table="units")["change"]
        self.assertEqual((change["before"], change["after"]), (32, 10))
        self.assertEqual(self.world.world.rows["spearMilitia"].maxSize, 10)

    def test_a_field_of_the_other_table_is_refused(self):
        answer = self.send("datatable_read", row="spearMilitia", field="Value", table="units")
        self.assertFalse(answer["ok"])
        self.assertIn("not allowed", answer["error"])
        refused = self.send("datatable_read", row="spearMilitia", field="maxSize")
        self.assertFalse(refused["ok"], "maxSize is not an item field")

    def test_an_unknown_table_and_an_unknown_row_are_refused(self):
        self.assertIn("unknown table", self.send("datatable_info", table="monsters")["error"])
        self.assertIn("no row named", self.send("datatable_read", row="nope", field="maxSize", table="units")["error"])

    def test_a_text_value_is_not_written(self):
        answer = self.send("datatable_write", row="spearMilitia", field="maxSize", table="units")
        self.assertFalse(answer["ok"])


class SpawnTests(BattleTestCase):
    def test_spawn_makes_a_squad_of_the_row_size_and_registers_it(self):
        answer = self.send("spawn_units", side="player", template="spearMilitia", count=2)
        self.assertTrue(answer["ok"])
        self.assertEqual([squad["units"] for squad in answer["squads"]], [32, 32])
        self.assertEqual(answer["units"], 64)
        state = self.send("battle_state")
        self.assertEqual(state["by_side"]["player"], {"initial": 64, "alive": 64})
        self.assertEqual(state["by_template"]["player:spearMilitia"]["alive"], 64)

    def test_the_side_follows_the_owner_pawn(self):
        self.send("spawn_units", side="player", template="militiaFoot")
        self.send("spawn_units", side="bandit", template="Brigands")
        state = self.send("battle_state")
        self.assertEqual((state["by_side"]["player"]["alive"], state["by_side"]["bandit"]["alive"]), (32, 18))

    def test_a_smaller_row_size_gives_a_smaller_squad(self):
        self.send("datatable_write", row="militiaFoot", field="maxSize", value=10, table="units")
        self.assertEqual(self.send("spawn_units", side="bandit", template="militiaFoot")["units"], 10)

    def test_bad_input_is_refused_and_nothing_is_spawned(self):
        bad = (
            {"side": "ai", "template": "spearMilitia"},
            {"side": "player"},
            {"side": "player", "template": "no_such_unit"},
            {"side": "player", "template": "spearMilitia", "count": 7},
            {"side": "player", "template": "spearMilitia", "count": 0},
            {"side": "player", "template": "spearMilitia", "dx": 99999},
        )
        for fields in bad:
            self.assertFalse(self.send("spawn_units", **fields)["ok"], fields)
        self.assertEqual(self.world.world.spawnCalls, 0)

    def test_a_failing_spawn_call_is_reported(self):
        world = BattleWorld(spawn_fails=True)
        self.addCleanup(world.close)
        answer = Commands(world).send("spawn_units", side="player", template="spearMilitia")
        self.assertFalse(answer["ok"])
        self.assertIn("spawnArmy", answer["error"])


class CasualtyTests(BattleTestCase):
    def test_casualties_are_the_start_size_minus_the_living_units(self):
        self.send("spawn_units", side="player", template="spearMilitia")
        self.send("spawn_units", side="bandit", template="militiaFoot")
        self.world.tick(5, 7, 0.0)
        state = self.send("battle_state")
        self.assertEqual((state["by_side"]["player"]["alive"], state["by_side"]["bandit"]["alive"]), (27, 25))
        self.assertEqual(state["by_side"]["bandit"]["initial"], 32)

    def test_experience_is_read_per_squad_and_per_unit_with_detail(self):
        self.send("spawn_units", side="player", template="spearMilitia")
        self.send("spawn_units", side="bandit", template="militiaFoot")
        self.world.tick(1, 1, 2.0)
        plain = self.send("battle_state")
        player = [squad for squad in plain["squads"] if squad["side"] == "player"][0]
        self.assertEqual((player["xp_mean"], player["xp_max"]), (2.0, 2.0))
        self.assertNotIn("units", player)
        detailed = self.send("battle_state", detail=1)
        rows = [squad for squad in detailed["squads"] if squad["side"] == "player"][0]["units"]
        self.assertEqual(len(rows), 31)
        self.assertEqual(len({row["uid"] for row in rows}), 31, "unit ids are unique")

    def test_detail_rows_are_capped(self):
        self.send("spawn_units", side="player", template="spearMilitia", count=3)
        rows = [squad["units"] for squad in self.send("battle_state", detail=1)["squads"]]
        self.assertTrue(all(len(unit_rows) == 32 for unit_rows in rows))
        self.send("datatable_write", row="militiaFoot", field="maxSize", value=100, table="units")
        self.send("spawn_units", side="player", template="militiaFoot")
        big = [squad for squad in self.send("battle_state", detail=1)["squads"] if squad["template"] == "militiaFoot"][0]
        self.assertEqual((big["alive"], len(big["units"])), (100, 64))

    def test_an_empty_registry_gives_empty_maps(self):
        state = self.send("battle_state")
        self.assertTrue(state["ok"])
        self.assertEqual(state["squads"], [])


class ClearTests(BattleTestCase):
    def setUp(self):
        super().setUp()
        self.send("spawn_units", side="player", template="spearMilitia")
        self.send("spawn_units", side="bandit", template="militiaFoot")

    def test_clear_kills_everything_and_forgets_the_squads(self):
        answer = self.send("clear_battle")
        self.assertEqual((answer["killed"], answer["squads_forgotten"]), (64, 2))
        self.assertEqual(self.world.world.living("player") + self.world.world.living("bandit"), 0)
        self.assertEqual(self.send("battle_state")["squads"], [])

    def test_clear_one_side_leaves_the_other(self):
        answer = self.send("clear_battle", side="bandit")
        self.assertEqual((answer["killed"], answer["squads_forgotten"]), (32, 1))
        self.assertEqual((self.world.world.living("player"), self.world.world.living("bandit")), (32, 0))
        self.assertEqual([squad["side"] for squad in self.send("battle_state")["squads"]], ["player"])

    def test_clear_with_a_bad_side_is_refused(self):
        self.assertFalse(self.send("clear_battle", side="ai")["ok"])
        self.assertEqual(self.world.world.living("player"), 32)

    def test_units_that_were_not_spawned_here_are_not_touched(self):
        killed = []
        other = self.world.game.obj("SMUnit", dead=False, assignedSquadID=self.world.game.struct(Value=3), combatExperience=0.0, UniqueID=1)
        self.world.game.method(other, "just_die", lambda _self: killed.append(True))
        self.send("clear_battle")
        self.assertEqual(killed, [])


class ExperienceWriteTests(BattleTestCase):
    def setUp(self):
        super().setUp()
        self.squad = self.send("spawn_units", side="player", template="spearMilitia")["squads"][0]["id"]

    def test_the_value_is_written_on_every_living_unit_and_read_back(self):
        answer = self.send("set_squad_experience", squad=self.squad, value=25)
        self.assertEqual((answer["alive"], answer["changed"]), (32, 32))
        self.assertEqual(self.send("battle_state")["squads"][0]["xp_mean"], 25)

    def test_an_unknown_squad_and_a_bad_value_are_refused(self):
        self.assertFalse(self.send("set_squad_experience", squad=999, value=5)["ok"])
        self.assertFalse(self.send("set_squad_experience", squad=self.squad, value=5000)["ok"])
        self.assertFalse(self.send("set_squad_experience", squad=self.squad)["ok"])


class MercenaryTests(BattleTestCase):
    def test_offers_list_name_cost_days_and_units(self):
        answer = self.send("mercenary_offers")
        self.assertEqual([offer["name"] for offer in answer["offers"]], ["greencaps", "battle_brothers"])
        first = answer["offers"][0]
        self.assertEqual((first["cost"], first["arrives_in"], first["units"]), (90, 11, ["mercenary_infantry", "mercenary_infantry", "Mercenary_Archers"]))
        self.assertEqual(answer["hired"], 0)

    def test_hire_takes_the_cost_and_makes_one_squad_for_each_unit_name(self):
        self.world.world.set_silver(200)
        answer = self.send("hire_mercenaries", company="greencaps")
        self.assertTrue(answer["ok"])
        self.assertEqual((answer["silver_before"], answer["silver_after"]), (200, 110))
        self.assertEqual([squad["template"] for squad in answer["squads"]], ["mercenary_infantry", "mercenary_infantry", "Mercenary_Archers"])
        self.assertEqual(answer["units"], 108)
        self.assertEqual((answer["hired_before"], answer["hired_after"], answer["offers_after"]), (0, 1, 1))
        self.assertEqual(self.send("battle_state")["by_side"]["player"]["alive"], 108)

    def test_hire_is_refused_when_the_silver_is_below_the_cost(self):
        self.world.world.set_silver(89)
        answer = self.send("hire_mercenaries", company="greencaps")
        self.assertFalse(answer["ok"])
        self.assertIn("not enough silver", answer["error"])
        self.assertEqual(self.world.world.silver(), 89)
        self.assertEqual(self.send("battle_state")["squads"], [])

    def test_an_unknown_company_and_a_missing_name_are_refused(self):
        self.world.world.set_silver(500)
        self.assertIn("no offered company", self.send("hire_mercenaries", company="nobody")["error"])
        self.assertIn("company is required", self.send("hire_mercenaries")["error"])
        self.assertEqual(self.world.world.silver(), 500)

    def test_a_company_cannot_be_hired_twice(self):
        self.world.world.set_silver(500)
        self.assertTrue(self.send("hire_mercenaries", company="battle_brothers")["ok"])
        self.assertFalse(self.send("hire_mercenaries", company="battle_brothers")["ok"])
        self.assertEqual(self.world.world.silver(), 450)


class LuaFilesTests(unittest.TestCase):
    def test_the_new_module_is_in_the_repo_and_loaded_by_the_actions_mod(self):
        from pathlib import Path
        root = Path(__file__).resolve().parents[2] / "mod"
        self.assertTrue((root / "shared" / "HarnessBattle" / "HarnessBattle.lua").is_file())
        self.assertIn('require("HarnessBattle")', (root / "HarnessActions" / "Scripts" / "main.lua").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
