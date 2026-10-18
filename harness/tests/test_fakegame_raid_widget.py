"""Tests for the feature raid_widget (M02 iteration 05) in the fake game.

They run the real Lua files. The widget asset is a pak file, so the fake game cannot show it: these tests cover the text rules,
the information table and the failure message when the pak is missing.
"""

import unittest

import fakegame_path  # noqa: F401
from fakegame import FakeGame
from test_fakegame_invasion import InvasionTestCase
from test_fakegame_modstate import find_pack_mod


class LinesTests(unittest.TestCase):
    def run_lua(self, code):
        game = FakeGame()
        game.start()
        self.addCleanup(game.close)
        game.exec(f'package.path = "{(find_pack_mod() / "Scripts").as_posix()}/?.lua;" .. package.path')
        return game.lua.eval(f"(function() local lines = require('features.raid_widget.lines'); {code} end)")()

    def test_next_raid_and_size(self):
        text = self.run_lua("local i = { raid_days_left = 12, raiders = 54, squads = 3 }; return lines.next_raid(i) .. '|' .. lines.size_estimate(i)")
        self.assertEqual(text, "Next raid: in 12 days|Size estimate: about 54 raiders (3 squads)")

    def test_unplanned_raid(self):
        self.assertEqual(self.run_lua("return lines.next_raid({}) .. '|' .. lines.size_estimate({})"), "Next raid: not planned yet|Size estimate: not known yet")

    def test_great_raid_clock_and_phases(self):
        self.assertEqual(self.run_lua("return lines.great_raid({ great_phase = 0, great_days_left = 1 })"), "Great raid: in 1 day")
        self.assertEqual(self.run_lua("return lines.great_raid({ great_phase = 1, great_wave = 2, great_waves = 3 })"), "Great raid: wave 2 of 3")
        self.assertEqual(self.run_lua("return lines.great_raid({ great_phase = 2 })"), "Great raid: final battle")
        self.assertEqual(self.run_lua("return lines.great_raid({ great_phase = 3 })"), "Great raid: won")

    def test_difficulty_and_terms(self):
        self.assertEqual(self.run_lua("return lines.difficulty({ difficulty = 2, difficulty_chosen = false })"), "Difficulty: 2 (not picked yet)")
        self.assertEqual(self.run_lua("return lines.terms(nil)"), "Terms: not in this game")
        self.assertEqual(self.run_lua("return lines.terms({ state = 1, offer = { payment = 200, tribute = 60 } })"),
                         "Terms: offered, 200 silver or vassalage (60 a year)")
        self.assertEqual(self.run_lua("return #lines.all({ difficulty = 1 }, nil)"), 5)


class WidgetFeatureTests(InvasionTestCase):
    def test_open_without_the_pak_gives_a_clear_message(self):
        answer = self.ask("raid_widget_open")
        self.assertTrue(answer["ok"], answer)
        self.assertFalse(answer["result"]["ok"])
        self.assertTrue(answer["result"]["error"])

    def test_state_wants_the_five_lines(self):
        answer = self.ask("raid_widget_state")
        self.assertTrue(answer["ok"], answer)
        wanted = answer["result"]["wanted_lines"]
        self.assertEqual(len(wanted), 5)
        self.assertTrue(wanted[0].startswith("Next raid"), wanted)
        self.assertTrue(wanted[3].startswith("Difficulty: 1 (not picked"), wanted)

    def test_a_pick_shows_in_the_difficulty_line(self):
        self.ask("invasion_pick_difficulty", value=3)
        wanted = self.ask("raid_widget_state")["result"]["wanted_lines"]
        self.assertEqual(wanted[3], "Difficulty: 3")


if __name__ == "__main__":
    unittest.main()
