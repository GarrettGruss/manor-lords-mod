"""Tests for the Outlaws init module (features/bandits/outlaws.lua) in the fake game.

ensure_outlaw_pawn() makes the bandit pawn "Outlaws" with spawnBanditCamp, kills the 18 camp Brigands, hides their bodies and
demolishes the camp. The fake game plays the camp call (see BanditsTestCase). It does not prove the real game; the real check
is the test scenario bandits-outlaws-init.
"""

import unittest

import fakegame_path  # noqa: F401
from test_fakegame_bandits import BanditsTestCase

ENSURE = 'local ok, info = require("features.bandits.outlaws").ensure(); return ok, info and info.created'


class OutlawsExistTests(BanditsTestCase):
    def test_the_pawn_exists_so_nothing_is_called(self):
        ok = self.game.exec('return require("features.bandits.outlaws").ensure()')
        self.assertTrue(ok)
        self.assertEqual((self.camp_calls, self.relation_calls, self.demolish_calls), (0, [], []))

    def test_the_poll_calls_nothing_while_the_pawn_exists(self):
        self.game.advance(20)
        self.assertEqual(self.camp_calls, 0)




class OutlawsMissingTests(BanditsTestCase):
    HAS_PAWN = False

    def ensure(self):
        return self.game.lua.eval(f"(function() {ENSURE} end)")()

    def camp_units(self):
        return [u for u in self.bandit_units if u.dead is not None]

    def test_a_missing_pawn_is_made_at_once(self):
        ok, created = self.ensure()
        self.assertTrue(ok)
        self.assertTrue(created)
        self.assertEqual(self.camp_calls, 1)
        self.assertEqual(len(self.bandit_pawns), 1)
        self.assertEqual(len(self.relation_calls), 1)  # addPawnRelations for the new pawn
        self.assertEqual(len(self.bandit_units), 18)
        self.assertFalse(any(u.dead for u in self.bandit_units))  # a camp is built by its Brigands: they live until it is built
        self.assertEqual(self.demolish_calls, [])

    def test_a_built_camp_loses_its_brigands_and_is_demolished_on_the_next_polls(self):
        self.ensure()
        self.game.advance(3)
        self.assertTrue(all(u.dead and u.hidden for u in self.bandit_units))  # killed and hidden
        self.assertEqual(self.demolish_calls, [True])  # demolish(true)
        self.assertFalse(self.game.exec('return require("features.bandits.outlaws").camp_pending()'))
        self.assertTrue(any("OUTLAWS camp is gone" in line for line in self.game.log_lines()))

    def test_the_brigands_live_while_the_camp_is_not_built(self):
        self.camp_built = False
        self.ensure()
        self.game.advance(20)
        self.assertFalse(any(u.dead for u in self.bandit_units))
        self.assertEqual(self.demolish_calls, [])
        self.camp_built = True
        self.game.advance(3)
        self.assertTrue(all(u.dead for u in self.bandit_units))
        self.assertEqual(self.demolish_calls, [True])

    def test_a_camp_that_is_never_built_loses_its_brigands_after_120_polls(self):
        self.camp_built = False
        self.ensure()
        self.game.advance(130)
        self.assertTrue(all(u.dead for u in self.bandit_units))
        self.assertTrue(any("camp built=false" in line for line in self.game.log_lines()))

    def test_a_second_call_does_nothing(self):
        self.ensure()
        ok, created = self.ensure()
        self.assertTrue(ok)
        self.assertFalse(created)
        self.assertEqual((self.camp_calls, len(self.relation_calls)), (1, 1))

    def test_the_poll_makes_the_pawn_at_game_start_once(self):
        self.game.advance(15)
        self.assertEqual((self.camp_calls, self.demolish_calls), (1, [True]))
        self.game.advance(20)
        self.assertEqual(self.camp_calls, 1)
        self.assertTrue(self.state()["outlaws"]["ready"])

    def test_a_pawn_that_is_gone_after_a_load_is_made_again(self):
        self.game.advance(15)
        for pawn in self.bandit_pawns:
            self.game.invalidate(pawn)
        self.bandit_pawns.clear()
        self.pawn_address = 2  # a load gives the player pawn a new address
        self.game.advance(15)
        self.assertEqual(self.camp_calls, 2)

    def test_a_pawn_that_survives_a_load_is_left_alone(self):
        self.game.advance(15)
        self.pawn_address = 2
        self.game.advance(12)
        self.assertEqual(self.camp_calls, 1)

    def test_a_failed_camp_call_is_an_error_and_ensure_returns_nil(self):
        self.camp_works = False
        ok = self.game.exec('local ok, why = require("features.bandits.outlaws").ensure(); return tostring(ok) .. ":" .. tostring(why)')
        self.assertTrue(ok.startswith("nil:spawnBanditCamp"), ok)
        self.assertTrue(any("OUTLAWS camp call failed" in line for line in self.game.log_lines()))

    def test_the_poll_gives_up_after_the_max_tries(self):
        self.camp_works = False
        self.game.advance(30)
        self.assertTrue(any("OUTLAWS gave up after 5 tries" in line for line in self.game.log_lines()))
        self.assertEqual(self.camp_calls, 5)

    def test_a_failed_demolish_is_an_error(self):
        def refuse(_self, _flag):
            raise RuntimeError("refused")

        def spawn_refusing(_self):
            self.camp_calls += 1
            self.bandit_pawns.append(self.game.obj("PawnCPP", isBandit=True))
            camp = self.game.obj("SMBuildingMaster", Data=self.game.struct(bType=100))
            self.game.method(camp, "GetAddress", lambda _s: 99999)
            self.game.method(camp, "IsConstructed", lambda _s: True)
            self.game.method(camp, "demolish", refuse)
        self.game.method(self.engine, "spawnBanditCamp", spawn_refusing)
        self.ensure()
        self.game.advance(3)
        self.assertTrue(any("OUTLAWS camp removal failed" in line and "demolish" in line for line in self.game.log_lines()))

    def test_a_camp_that_stays_after_the_first_demolish_is_tried_again(self):
        self.demolish_needs = 3
        self.ensure()
        self.game.advance(8)
        self.assertEqual(self.demolish_calls, [True, True, True])  # the third call removed it
        self.assertFalse(self.game.exec('return require("features.bandits.outlaws").camp_pending()'))

    def test_a_camp_that_never_goes_is_an_error_after_240_polls(self):
        self.demolish_needs = 10 ** 6
        self.ensure()
        self.game.advance(260)
        self.assertTrue(any("camp still stands after 240 polls" in line for line in self.game.log_lines()))
        self.assertFalse(self.game.exec('return require("features.bandits.outlaws").camp_pending()'))

    def test_the_guard_before_a_rebellion_makes_the_pawn_first_and_does_not_kill_the_rebels(self):
        self.arm(6)
        answer = self.ask("bandits_leave_now", count=6)
        result = answer["result"]
        self.assertEqual(self.camp_calls, 1)  # the pawn first
        self.assertTrue(result["last_leave"]["pawn_created"])
        self.assertEqual(result["last_leave"]["removed"], 6)
        self.assertEqual(self.spawn_calls(), 1)
        self.assertTrue(result["last_leave"]["spawned"])
        log = self.game.log_lines()
        created = next(i for i, line in enumerate(log) if "OUTLAWS pawn created" in line)
        left = next(i for i, line in enumerate(log) if "BANDITS leave day=" in line)
        self.assertLess(created, left)
        self.game.advance(5)
        self.assertEqual(self.demolish_calls, [True])
        living = [u for u in self.bandit_units if not u.dead]
        self.assertEqual(len(living), 18)  # the 18 rebels live; the 18 camp Brigands are dead

    def test_a_failed_guard_blocks_the_rebellion_and_removes_nothing(self):
        self.camp_works = False
        self.arm(6)
        result = self.ask("bandits_leave_now", count=6)["result"]
        self.assertIn("no Outlaws pawn", result["last_leave"]["blocked"])
        self.assertEqual(self.dead_members(), 0)
        self.assertEqual(self.spawn_calls(), 0)


if __name__ == "__main__":
    unittest.main()
