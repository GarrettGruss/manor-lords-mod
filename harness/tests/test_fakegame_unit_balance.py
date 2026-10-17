"""Tests for the feature unit_balance of the pack mod (mod feature M05, iteration 01) in the fake game.

They run the real Lua files. The fake world has a unit list. They do not prove how the real game behaves.
"""

import json
import unittest

import fakegame_path  # noqa: F401
from fakegame import FakeGame
from test_fakegame_modstate import FNAME, HELPERS, find_pack_mod


class UnitBalanceTestCase(unittest.TestCase):
    def setUp(self):
        self.game = FakeGame()
        self.game.start()
        self.addCleanup(self.game.close)
        pack = find_pack_mod()
        self.mod_name = pack.name
        self.game.exec(f'package.path = "{(pack / "Scripts").as_posix()}/?.lua;" .. package.path')
        self.game.exec(FNAME + HELPERS)
        self.units, self.counter = [], 0
        self.game.load_mod(self.mod_name)
        self.game.advance(2)

    def make_unit(self, defence, block, dead=False):
        unit = self.game.obj("SMUnit", dead=dead, **{"def": defence}, block=block)
        number = 5000 + len(self.units)
        self.game.method(unit, "GetAddress", lambda _self, number=number: number)
        self.units.append(unit)
        return unit

    def ask(self, name, **args):
        self.counter += 1
        folder = self.game.run_dir / "modcmd" / self.mod_name
        folder.mkdir(parents=True, exist_ok=True)
        body = {"id": f"{self.counter:04d}", "command": f"{self.mod_name}.{name}", "args": args}
        (folder / f"{self.counter:04d}.json").write_text(json.dumps(body), encoding="utf-8")
        self.game.advance(1)
        return json.loads((folder / f"{self.counter:04d}.result.json").read_text(encoding="utf-8"))

    def apply(self):
        answer = self.ask("unit_balance_apply")
        self.assertTrue(answer["ok"], answer)
        return answer["result"]


class RuleTests(UnitBalanceTestCase):
    def test_unarmored_units_lose_def_and_block(self):
        unit = self.make_unit(7.2, 7.75)
        state = self.apply()
        self.assertEqual((unit["def"], unit["block"]), (0, 0))
        self.assertEqual((state["changed"], state["failed"]), (1, 0))

    def test_armored_units_keep_their_values(self):
        unit = self.make_unit(62.0, 60.0)
        state = self.apply()
        self.assertEqual((unit["def"], unit["block"]), (62.0, 60.0))
        self.assertEqual((state["changed"], state["armored"]), (0, 1))

    def test_the_limit_is_exclusive(self):
        unit = self.make_unit(10.0, 5.0)
        self.apply()
        self.assertEqual(unit["def"], 10.0)

    def test_a_unit_with_nothing_to_reduce_is_skipped(self):
        self.make_unit(0.0, 0.0)
        self.assertEqual(self.apply()["changed"], 0)

    def test_a_dead_unit_is_left_alone(self):
        unit = self.make_unit(5.0, 5.0, dead=True)
        self.apply()
        self.assertEqual(unit["def"], 5.0)

    def test_a_unit_is_changed_once(self):
        self.make_unit(5.0, 5.0)
        self.apply()
        self.assertEqual(self.apply()["changed"], 1)

    def test_the_poll_changes_a_unit_that_spawns_later(self):
        self.make_unit(5.0, 5.0)
        self.game.advance(3)
        late = self.make_unit(4.0, 3.0)
        self.game.advance(3)
        self.assertEqual((late["def"], late["block"]), (0, 0))

    def test_factors_scale_the_values(self):
        self.ask("unit_balance_set", def_factor=0.5, block_factor=0.25)
        unit = self.make_unit(8.0, 8.0)
        self.apply()
        self.assertEqual((unit["def"], unit["block"]), (4.0, 2.0))


class SwitchTests(UnitBalanceTestCase):
    def test_off_restores_and_stops_the_rule(self):
        unit = self.make_unit(7.0, 6.0)
        self.apply()
        answer = self.ask("unit_balance_set", enabled=False)["result"]
        self.assertEqual((answer["restored"], unit["def"], unit["block"]), (1, 7.0, 6.0))
        later = self.make_unit(5.0, 5.0)
        self.game.advance(3)
        self.assertEqual(later["def"], 5.0)
        self.assertEqual(self.apply()["changed"], 1)

    def test_a_bad_factor_is_refused(self):
        self.assertFalse(self.ask("unit_balance_set", def_factor=2)["ok"])
        self.assertFalse(self.ask("unit_balance_set", enabled="yes")["ok"])


if __name__ == "__main__":
    unittest.main()
