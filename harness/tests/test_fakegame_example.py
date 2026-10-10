"""The example from fakegame/README.md: test the mod HarnessLoadProbe in under 30 lines."""

import unittest

import fakegame_path  # noqa: F401
from fakegame import FakeGame, build_manor_lords_state


class LoadProbeTests(unittest.TestCase):
    def test_f8_loads_the_wanted_slot(self):
        with FakeGame(env={"HARNESS_TEST_SAVE": "saveGame_0"}) as game:
            state = build_manor_lords_state(game)
            game.load_mod("HarnessLoadProbe")
            game.advance(3)  # the menu appears after 2 s
            self.assertEqual(game.press("F8"), 1)
            game.advance(10)
            self.assertEqual(state.calls, ["SwitchToLoadScreen", "LoadGame:2"])
            self.assertTrue(any("LoadGame returned without error" in line for line in game.log_lines()))

    def test_f8_reports_a_missing_slot(self):
        with FakeGame() as game:
            state = build_manor_lords_state(game, wanted_slot_listed=False)
            game.load_mod("HarnessLoadProbe")
            game.advance(3)
            game.press("F8")
            game.advance(5)
            self.assertNotIn("LoadGame:2", state.calls)
            self.assertTrue(any("is not in the list" in line for line in game.log_lines()))


if __name__ == "__main__":
    unittest.main()
