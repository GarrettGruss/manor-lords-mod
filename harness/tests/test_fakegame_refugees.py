"""Tests for the feature refugees of the pack mod (mod feature M09) in the fake game.

They run the real Lua files. ManorCore.settle_region is a stub that adds 5 families a call and 3 homeless families.
They do not prove how the real game behaves (see the real-game runs in the iteration files).
"""

import unittest

import fakegame_path  # noqa: F401
from test_fakegame_vassals import HandoverBase

SETTLE_STUB = """
SETTLE_CALLS = {}
local core = require("ManorCore")
core.settle_region = function(request)
    SETTLE_CALLS[#SETTLE_CALLS + 1] = request.region
    HOME_FAMILIES = HOME_FAMILIES + 5
    HOME_HOMELESS = HOME_HOMELESS + 3
    return { ok = true }
end
HOME_FAMILIES, HOME_HOMELESS = 10, 0
"""


class RefugeeTestCase(HandoverBase):
    def setUp(self):
        super().setUp()
        self.game.exec(SETTLE_STUB)
        self.game.method(self.home, "getTotalNumFamilies", lambda _self: self.game.exec("return HOME_FAMILIES"))
        self.game.method(self.home, "getNumHomelessFamilies", lambda _self: self.game.exec("return HOME_HOMELESS"))
        self.home.Approval = 70
        region = self.add_region("Eichenhau", True, 4)
        self.game.method(region, "getTotalNumFamilies", lambda _self: 5)
        self.game.advance(10)

    def refugees(self):
        answer = self.ask("refugees_state")
        self.assertTrue(answer["ok"], answer)
        return answer["result"]

    def settle_calls(self):
        return self.game.exec("return #SETTLE_CALLS")


class WaveTests(RefugeeTestCase):
    def test_a_vassal_wave_makes_one_settle_call_for_5_families_at_30_percent(self):
        answer = self.ask("refugees_vassal_lost", slot=1, share=30)
        self.assertTrue(answer["ok"], answer)
        result = answer["result"]
        self.assertEqual(self.settle_calls(), 1)
        self.assertEqual(result["last_wave"]["wanted"], 2)
        self.assertTrue(result["active"])
        self.assertEqual((result["wave_families"], result["base_homeless"]), (5, 0))

    def test_the_wave_is_sent_to_the_home_region(self):
        self.ask("refugees_vassal_lost", slot=1, share=30)
        self.assertEqual(self.game.exec("return SETTLE_CALLS[1]"), "Home")

    def test_a_second_wave_is_refused_while_one_is_active(self):
        self.ask("refugees_vassal_lost", slot=1, share=30)
        answer = self.ask("refugees_vassal_lost", slot=1, share=30)
        self.assertFalse(answer["ok"])
        self.assertIn("active", answer["error"])
        self.assertEqual(self.settle_calls(), 1)

    def test_a_large_wave_uses_more_calls_up_to_the_limit(self):
        self.ask("refugees_send_wave", families=30, share=60)
        self.assertEqual(self.settle_calls(), 3)

    def test_the_state_is_kept_in_the_pawn_tags(self):
        self.ask("refugees_vassal_lost", slot=1, share=30)
        tags = self.tags()
        self.assertIn("invasion:refugee_active=true", tags)
        self.assertIn("invasion:refugee_waves=1", tags)

    def test_an_empty_slot_is_refused(self):
        self.assertFalse(self.ask("refugees_vassal_lost", slot=3, share=30)["ok"])


    def test_the_random_share_stays_between_30_and_60_percent(self):
        shares = self.game.exec(
            "local r = require('features.refugees.rules'); local out = {}; for i = 0, 200 do out[#out + 1] = r.share_from_roll(i / 200, 0.30, 0.60) end; return math.min(table.unpack(out)), math.max(table.unpack(out))")
        low, high = tuple(shares)
        self.assertAlmostEqual(low, 0.30)
        self.assertAlmostEqual(high, 0.60)

    def test_wave_families_round_up_and_calls_round_to_nearest(self):
        values = self.game.exec(
            "local r = require('features.refugees.rules'); return r.wave_families(5, 0.3), r.wave_families(1, 0.3), r.calls_for(2, 5, 3), r.calls_for(8, 5, 3), r.calls_for(40, 5, 3)")
        self.assertEqual(tuple(values), (2, 1, 1, 2, 3))


if __name__ == "__main__":
    unittest.main()
