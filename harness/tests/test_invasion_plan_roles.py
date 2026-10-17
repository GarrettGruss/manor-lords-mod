"""Tests for the pure role rules of the raid plan (M05 iteration 02). They run the real plan.lua in Lua, without a game."""

import unittest

import fakegame_path  # noqa: F401
from fakegame import FakeGame
from test_fakegame_modstate import find_pack_mod

ROLES = """
roles = {
  templates = { melee = { {"A1","A2"}, {"B1","B2"}, {"C1","C2"} }, ranged = { {"R1","R2"}, {"X1","X2"} } },
  ranged_share = 0.25, crossbow_share = { 0.0, 0.5, 0.75 },
  melee_tier_weights = { {70,30,0}, {40,40,20}, {20,40,40} },
}
first = function(a, b) return a end
"""


class RoleRulesTest(unittest.TestCase):
    def setUp(self):
        self.game = FakeGame()
        self.game.start()
        self.addCleanup(self.game.close)
        scripts = (find_pack_mod() / "Scripts").as_posix()
        self.game.exec(f'package.path = "{scripts}/?.lua;" .. package.path\n' + ROLES + 'plan = require("features.invasion.plan")')

    def compose(self, squads, difficulty):
        self.game.exec(f"result = table.concat(plan.composition({squads}, {difficulty}, roles, first), '-')")
        return self.game.lua.eval("result").split("-")

    def test_one_template_for_each_squad(self):
        for squads in (1, 2, 3, 4, 6, 9):
            for difficulty in (1, 2, 3):
                self.assertEqual(len(self.compose(squads, difficulty)), squads)

    def test_ranged_count_is_the_rounded_share(self):
        expected = {1: 0, 2: 1, 3: 1, 4: 1, 6: 2, 9: 2}
        for squads, ranged in expected.items():
            names = self.compose(squads, 2)
            self.assertEqual(sum(1 for n in names if n[0] in "RX"), ranged, (squads, names))

    def test_no_tier_three_at_difficulty_one(self):
        for squads in (1, 2, 3, 6, 9):
            self.assertFalse([n for n in self.compose(squads, 1) if n.startswith("C")])

    def test_difficulty_three_has_heavier_melee(self):
        low = [n for n in self.compose(9, 1) if n.startswith("C")]
        high = [n for n in self.compose(9, 3) if n.startswith("C")]
        self.assertGreater(len(high), len(low))

    def test_difficulty_one_has_no_crossbows(self):
        self.assertFalse([n for n in self.compose(9, 1) if n.startswith("X")])

    def test_join_and_split_round_trip(self):
        self.game.exec("result = table.concat(plan.split(plan.join({'a','b_c'})), '|')")
        self.assertEqual(self.game.lua.eval("result"), "a|b_c")

    def test_bad_input_fails_loudly(self):
        self.game.exec("ok, err = pcall(plan.composition, 0, 1, roles, first)")
        self.assertFalse(self.game.lua.eval("ok"))
        self.game.exec("ok, err = pcall(plan.composition, 3, 4, roles, first)")
        self.assertIn("difficulty 4", self.game.lua.eval("err"))
        self.game.exec("ok, err = pcall(plan.expected_units, {'zzz'}, {})")
        self.assertIn("zzz", self.game.lua.eval("err"))


if __name__ == "__main__":
    unittest.main()
