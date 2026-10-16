"""Mock tests for HarnessTune (spec 28): tune_state, tune_set, tune_reset and the re-apply timer, on fake units of four sides."""

import json
import unittest

import fakegame_path  # noqa: F401
from fakegame import FakeGame


def make_unit(game, squad, att=2.0, defence=10.0):
    return game.obj("SMUnit", dead=False, assignedSquadID=game.struct(Value=squad), att=att, **{"def": defence},
                    block=1.0, armorPierce=0.0, morale=1.0, baseDefence=defence, baseBlock=1.0, charge=0.0)


def build_world(game):
    """Player squad 3 (2 units), bandit squad 5 (3 units), AI lord squad 7 (1 unit), a villager with no squad."""
    game.obj("PawnCPP", isMainPlayer=True, isBandit=False, isAI=False, commandedSquads=game.array([game.struct(Value=3)]))
    game.obj("PawnCPP", isMainPlayer=False, isBandit=True, isAI=True, commandedSquads=game.array([game.struct(Value=5)]))
    game.obj("PawnCPP", isMainPlayer=False, isBandit=False, isAI=True, commandedSquads=game.array([game.struct(Value=7)]))
    return {"player": [make_unit(game, 3, defence=10.0) for _ in range(2)],
            "bandit": [make_unit(game, 5, defence=4.0) for _ in range(3)],
            "ai": [make_unit(game, 7)], "civil": [make_unit(game, 0)]}


class TuneTestCase(unittest.TestCase):
    def setUp(self):
        self.game = FakeGame()
        self.game.start()
        self.addCleanup(self.game.close)
        self.units = build_world(self.game)
        self.game.load_mod("HarnessActions")
        self.game.advance(1)
        self.number = 0

    def send(self, command, **fields):
        self.number += 1
        folder = self.game.run_dir / "commands"
        folder.mkdir(exist_ok=True)
        (folder / f"{self.number:04d}.json").write_text(json.dumps({"id": f"{self.number:04d}", "command": command, **fields}), encoding="utf-8")
        self.game.advance(1)
        return json.loads((folder / f"{self.number:04d}.result.json").read_text(encoding="utf-8"))


class StateTests(TuneTestCase):
    def test_state_shows_every_side_without_a_registry(self):
        state = self.send("tune_state")
        self.assertTrue(state["ok"])
        self.assertEqual({side: row["alive"] for side, row in state["sides"].items()}, {"player": 2, "bandit": 3, "ai_lord": 1})
        self.assertEqual(state["sides"]["bandit"]["mean"]["def"], 4.0)
        self.assertEqual([squad["squad"] for squad in state["squads"]], [3, 5, 7])
        self.assertEqual(state["unowned_units"], 1)
        self.assertEqual(state["overrides"], [])


class SetTests(TuneTestCase):
    def test_set_writes_all_living_units_of_the_side_and_nothing_else(self):
        answer = self.send("tune_set", side="bandit", field="att", value=9)
        self.assertEqual((answer["ok"], answer["alive"], answer["changed"]), (True, 3, 3))
        state = self.send("tune_state")
        self.assertEqual(state["sides"]["bandit"]["mean"]["att"], 9.0)
        self.assertEqual(state["sides"]["player"]["mean"]["att"], 2.0)
        self.assertEqual(state["overrides"], [{"scope": "side:bandit", "field": "att", "value": 9}])

    def test_a_dead_unit_is_not_written(self):
        self.units["bandit"][0].dead = True
        self.assertEqual(self.send("tune_set", side="bandit", field="att", value=9)["alive"], 2)

    def test_set_for_one_squad_beats_the_side_value(self):
        self.send("tune_set", side="bandit", field="att", value=9)
        self.send("tune_set", squad=5, field="att", value=4)
        self.assertEqual(self.send("tune_state")["sides"]["bandit"]["mean"]["att"], 4.0)

    def test_bad_input_is_refused(self):
        for fields, text in [({"side": "king", "field": "att", "value": 1}, "side must be"),
                             ({"side": "bandit", "field": "hp", "value": 1}, "not an allowed stat"),
                             ({"side": "bandit", "field": "att", "value": -1}, "value must be"),
                             ({"side": "bandit", "field": "att"}, "value must be"),
                             ({"field": "att", "value": 1}, "side or squad is required"),
                             ({"side": "bandit", "squad": 5, "field": "att", "value": 1}, "not both")]:
            answer = self.send("tune_set", **fields)
            self.assertFalse(answer["ok"], fields)
            self.assertIn(text, answer["error"])


class TimerTests(TuneTestCase):
    def test_a_unit_that_spawns_later_gets_the_override_within_the_period(self):
        self.send("tune_set", side="player", field="def", value=50)
        late = make_unit(self.game, 3, defence=10.0)
        self.game.advance(3)
        self.assertEqual(getattr(late, "def"), 50)

    def test_no_override_means_no_write(self):
        late = make_unit(self.game, 3, defence=10.0)
        self.game.advance(5)
        self.assertEqual(getattr(late, "def"), 10)


class ResetTests(TuneTestCase):
    def test_reset_restores_the_original_values_including_late_units(self):
        self.send("tune_set", side="player", field="def", value=50)
        late = make_unit(self.game, 3, defence=7.0)
        self.game.advance(3)
        answer = self.send("tune_reset")
        self.assertEqual((answer["ok"], answer["removed"], answer["restored"]), (True, 1, 3))
        self.assertEqual([getattr(unit, "def") for unit in self.units["player"]], [10, 10])
        self.assertEqual(getattr(late, "def"), 7)
        self.assertEqual(self.send("tune_state")["overrides"], [])
        self.game.advance(3)
        self.assertEqual(getattr(late, "def"), 7, "the timer must not write again")

    def test_reset_one_side_and_field_keeps_the_others(self):
        self.send("tune_set", side="player", field="def", value=50)
        self.send("tune_set", side="bandit", field="def", value=60)
        self.send("tune_set", side="bandit", field="att", value=9)
        self.send("tune_reset", side="bandit", field="def")
        state = self.send("tune_state")
        self.assertEqual(state["sides"]["bandit"]["mean"]["def"], 4.0)
        self.assertEqual(state["sides"]["bandit"]["mean"]["att"], 9.0)
        self.assertEqual(state["sides"]["player"]["mean"]["def"], 50.0)
        self.assertEqual(len(state["overrides"]), 2)

    def test_the_original_is_the_value_before_the_first_write(self):
        self.send("tune_set", side="player", field="def", value=50)
        self.send("tune_set", side="player", field="def", value=80)
        self.send("tune_reset")
        self.assertEqual([getattr(unit, "def") for unit in self.units["player"]], [10, 10])

    def test_bad_reset_input_is_refused(self):
        self.assertFalse(self.send("tune_reset", side="king")["ok"])
        self.assertFalse(self.send("tune_reset", field="hp")["ok"])


if __name__ == "__main__":
    unittest.main()
