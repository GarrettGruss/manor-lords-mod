"""Mock test for the autosave protection: the shared module HarnessAutosave and its two HarnessActions commands."""

import json
import unittest

import fakegame_path  # noqa: F401
from fakegame import FakeGame, build_manor_lords_state


def start(game, **world_options):
    """A game that is already loaded, with the helper mod running."""
    state = build_manor_lords_state(game, engine_delay=0, **world_options)
    state.loaded_at = game.now() - 1
    game.load_mod("HarnessActions")
    game.advance(1)
    return state


def send(game, number, command):
    folder = game.run_dir / "commands"
    folder.mkdir(exist_ok=True)
    (folder / f"{number:04d}.json").write_text(json.dumps({"id": f"{number:04d}", "command": command}), encoding="utf-8")
    game.advance(1)
    return json.loads((folder / f"{number:04d}.result.json").read_text(encoding="utf-8"))


class AutosaveCommandTests(unittest.TestCase):
    def test_status_reads_the_timer_and_changes_nothing(self):
        with FakeGame() as game:
            state = start(game)
            answer = send(game, 1, "autosave_status")["status"]
            self.assertEqual((answer["settings_period_s"], answer["timer_exists"]), (600, True))
            self.assertTrue(0 < answer["remaining_s"] <= 600)
            self.assertEqual(state.autosave.calls, [])

    def test_disable_pushes_the_timer_far_away_and_keeps_the_stored_period(self):
        with FakeGame() as game:
            state = start(game)
            changes = send(game, 1, "disable_autosave")["changes"]
            self.assertLess(changes["before"]["remaining_s"], 601)
            self.assertGreater(changes["after"]["remaining_s"], 31000000)
            self.assertNotEqual(changes["before"]["handle_id"], changes["after"]["handle_id"])
            self.assertEqual(changes["after"]["settings_period_s"], 600)  # Settings is not written
            self.assertEqual(state.autosave.calls, ["SetAutosavePeriodOnPawn:3.1536e+07"])

    def test_the_disabled_timer_keeps_counting_down_slowly_not_to_zero(self):
        with FakeGame() as game:
            state = start(game)
            send(game, 1, "disable_autosave")
            game.advance(60)
            self.assertGreater(state.autosave.remaining(), 31000000)

    def test_a_broken_timer_shows_in_the_status_after_the_call(self):
        with FakeGame() as game:
            start(game, autosave_works=False)
            changes = send(game, 1, "disable_autosave")["changes"]
            self.assertLess(changes["after"]["remaining_s"], 601)

    def test_no_game_instance_gives_a_clear_error(self):
        with FakeGame() as game:
            state = start(game)
            game.invalidate(state.autosave.instance)
            answer = send(game, 1, "disable_autosave")
            self.assertFalse(answer["ok"])
            self.assertIn("MLGameInstance", answer["error"])


if __name__ == "__main__":
    unittest.main()
