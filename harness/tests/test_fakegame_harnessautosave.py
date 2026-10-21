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


BEGIN_PLAY = "/Game/CPP_BP/MyPawnCPP_BP3.MyPawnCPP_BP3_C:ReceiveBeginPlay"
BOOT_ENV = {"HARNESS_AUTOBOOT": "1", "HARNESS_TEST_SAVE": "saveGame_0"}


def boot_to_ready(game):
    state = build_manor_lords_state(game)
    game.load_mod("HarnessBoot")
    game.run_until_idle()
    return state


def load_a_world(game, state, works=True):
    """A world load makes a new pawn with a new 600 s timer; the game then runs the BeginPlay event."""
    state.autosave.ends_at = game.now() + 600
    state.autosave.works = works
    game.fire_hook(BEGIN_PLAY)
    game.advance(15)


class AutosaveAfterLoadTests(unittest.TestCase):
    def test_the_timer_is_pushed_away_again_after_a_load(self):
        with FakeGame(env=BOOT_ENV) as game:
            state = boot_to_ready(game)
            calls_at_ready = len(state.autosave.calls)
            load_a_world(game, state)
            self.assertGreater(state.autosave.remaining(), 31000000)
            self.assertEqual(len(state.autosave.calls), calls_at_ready + 1)
            self.assertEqual(game.read_text("mod.log").count("autosave pushed away after a load"), 1)

    def test_a_second_load_is_pushed_away_too(self):
        with FakeGame(env=BOOT_ENV) as game:
            state = boot_to_ready(game)
            load_a_world(game, state)
            load_a_world(game, state)
            self.assertGreater(state.autosave.remaining(), 31000000)
            self.assertEqual(game.read_text("mod.log").count("autosave pushed away after a load"), 2)

    def test_a_failed_push_after_a_load_logs_an_error_after_the_retries(self):
        with FakeGame(env=BOOT_ENV) as game:
            state = boot_to_ready(game)
            calls_at_ready = len(state.autosave.calls)
            load_a_world(game, state, works=False)
            self.assertLess(state.autosave.remaining(), 601)
            self.assertEqual(len(state.autosave.calls), calls_at_ready + 5)
            log = game.read_text("mod.log")
            self.assertIn("autosave timer was not pushed away after a load", log)
            self.assertNotIn("autosave pushed away after a load", log)


if __name__ == "__main__":
    unittest.main()
