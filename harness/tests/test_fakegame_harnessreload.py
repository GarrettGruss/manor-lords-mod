"""Mock test for the HarnessReload mod (spec 06, part A): request file in, RestartMod call, result file out."""

import json
import re
import unittest

import fakegame_path  # noqa: F401
from fakegame import FakeGame

NEW_CODE_LINE = "function(name) require('HarnessLog').info(name, 'loaded version 7, more text') end"


def request(game, mod, request_id):
    (game.run_dir / "reload.json").write_text(json.dumps({"mod": mod, "id": request_id}), encoding="utf-8")


def start(game, restarted_mod_logs=True):
    game.load_mod("HarnessReload")
    if restarted_mod_logs:
        game.fg.on_restart = game.lua.eval(NEW_CODE_LINE)
    game.advance(1)


class HarnessReloadTests(unittest.TestCase):
    def test_restart_waits_for_the_version_line_and_writes_the_result(self):
        with FakeGame() as game:
            start(game)
            request(game, "HarnessLogTest", "id-1")
            game.advance(2)
            result = game.read_json("reload.result.json")
            self.assertEqual(list(game.fg.restarts.values()), ["HarnessLogTest"])
            self.assertEqual((result["id"], result["ok"], result["version"]), ("id-1", True, "7"))
            self.assertIn("[HarnessLogTest] loaded version 7", result["line"])
            self.assertNotIn("reload.json", game.files())
            self.assertNotIn("reload.result.json.tmp", game.files())

    def test_an_old_version_line_is_not_taken_as_the_answer(self):
        with FakeGame() as game:
            start(game, restarted_mod_logs=False)
            game.exec("require('HarnessLog').info('HarnessLogTest', 'loaded version 1')")
            request(game, "HarnessLogTest", "id-2")
            game.advance(25)
            result = game.read_json("reload.result.json")
            self.assertFalse(result["ok"])
            self.assertIn("no 'loaded version' line", result["error"])
            self.assertEqual(len(game.fg.restarts), 1)

    def test_the_same_id_runs_once(self):
        with FakeGame() as game:
            start(game)
            request(game, "HarnessLogTest", "same")
            game.advance(2)
            request(game, "HarnessLogTest", "same")
            game.advance(2)
            self.assertEqual(len(game.fg.restarts), 1)
            request(game, "HarnessLogTest", "other")
            game.advance(2)
            self.assertEqual(len(game.fg.restarts), 2)

    def test_bad_requests_are_refused_without_a_restart(self):
        cases = {"Bad Name": "no valid mod name", "..": "no valid mod name",
                 "HarnessReload": "cannot restart itself"}
        for name, message in cases.items():
            with self.subTest(name=name), FakeGame() as game:
                start(game)
                request(game, name, "id-x")
                game.advance(1)
                result = game.read_json("reload.result.json")
                self.assertFalse(result["ok"])
                self.assertIn(message, result["error"])
                self.assertEqual(len(game.fg.restarts), 0)

    def test_a_request_without_an_id_is_refused(self):
        with FakeGame() as game:
            start(game)
            (game.run_dir / "reload.json").write_text('{"mod": "HarnessLogTest"}', encoding="utf-8")
            game.advance(1)
            self.assertIn("no valid id", game.read_json("reload.result.json")["error"])

    def test_restart_error_is_reported(self):
        with FakeGame() as game:
            start(game)
            game.fg.on_restart = game.lua.eval("function(name) error('boom') end")
            request(game, "HarnessLogTest", "id-3")
            game.advance(2)
            result = game.read_json("reload.result.json")
            self.assertFalse(result["ok"])
            self.assertIn("RestartMod failed", result["error"])

    def test_a_second_request_waits_until_the_first_is_done(self):
        with FakeGame() as game:
            start(game, restarted_mod_logs=False)
            request(game, "HarnessLogTest", "first")
            game.advance(1)
            request(game, "HarnessLogTest", "second")
            game.advance(5)
            self.assertEqual(len(game.fg.restarts), 1)  # still waiting for the first answer
            game.advance(20)  # the first times out, then the second starts
            game.advance(1)
            self.assertEqual(len(game.fg.restarts), 2)


class VersionLineTests(unittest.TestCase):
    """The mods that can be reloaded must log 'loaded version <v>' with their folder name as tag."""

    def test_reloadable_mods_log_a_version_line(self):
        for name in ("HarnessLogTest", "HarnessReload", "HarnessTelemetry", "HarnessLoadProbe"):
            with self.subTest(mod=name), FakeGame() as game:
                game.load_mod(name)
                game.advance(1)
                pattern = re.compile(rf"\[{name}\] loaded version [\w.-]+")
                self.assertTrue(any(pattern.search(line) for line in game.log_lines()), game.log_lines())


if __name__ == "__main__":
    unittest.main()
