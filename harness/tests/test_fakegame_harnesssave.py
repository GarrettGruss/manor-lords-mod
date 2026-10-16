"""Mock test for the Lua command save_game (spec 24). The fake game records the call. No real save function runs."""

import json
import unittest

import fakegame_path  # noqa: F401
from fakegame import FakeGame, build_manor_lords_state


def start(game, **world_options):
    state = build_manor_lords_state(game, engine_delay=0, **world_options)
    state.loaded_at = game.now() - 1
    state.saves = []
    game.method(state.player, "requestSaveFile", lambda _self, slot, name: state.saves.append((slot, name)) or True)
    game.load_mod("HarnessActions")
    game.advance(1)
    return state


def send(game, number, **request):
    folder = game.run_dir / "commands"
    folder.mkdir(exist_ok=True)
    body = {"id": f"{number:04d}", "command": "save_game", **request}
    (folder / f"{number:04d}.json").write_text(json.dumps(body), encoding="utf-8")
    game.advance(1)
    return json.loads((folder / f"{number:04d}.result.json").read_text(encoding="utf-8"))


class SaveGameCommandTests(unittest.TestCase):
    def test_a_free_slot_is_saved_once(self):
        with FakeGame() as game:
            state = start(game, save_exists=False)
            answer = send(game, 1, save_slot="saveGame_4", save_name="harness test")
            self.assertTrue(answer["ok"], answer)
            self.assertEqual(state.saves, [("saveGame_4", "harness test")])

    def test_an_existing_slot_is_refused_and_not_saved(self):
        with FakeGame() as game:
            state = start(game, save_exists=True)
            answer = send(game, 1, save_slot="saveGame_4", save_name="harness test")
            self.assertFalse(answer["ok"])
            self.assertIn("exists", answer["error"])
            self.assertEqual(state.saves, [])

    def test_bad_slot_and_name_are_refused(self):
        with FakeGame() as game:
            state = start(game, save_exists=False)
            for number, request in enumerate(({"save_slot": "harness_x", "save_name": "a"}, {"save_slot": "saveGame_1/../x", "save_name": "a"},
                                              {"save_slot": "autosave", "save_name": "a"}, {"save_slot": "saveGame_1", "save_name": "a;b"},
                                              {"save_slot": "saveGame_1"}, {"save_name": "a"}), start=1):
                self.assertFalse(send(game, number, **request)["ok"], request)
            self.assertEqual(state.saves, [])


if __name__ == "__main__":
    unittest.main()
