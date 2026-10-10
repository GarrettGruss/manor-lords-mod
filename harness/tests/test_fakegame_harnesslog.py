"""A second, independent proof of the kit: test the shared HarnessLog module with it."""

import re
import unittest

import fakegame_path  # noqa: F401
from fakegame import FakeGame

LINE = re.compile(r"^(\d+) (\d+) (INFO|WARN|ERROR) \[(\S+)\] (.*)$")


def log_module(game):
    # require returns two values in Lua 5.4; the parentheses keep one.
    return game.lua.eval('(require("HarnessLog"))')


class HarnessLogTests(unittest.TestCase):
    def test_lines_are_flushed_into_the_run_dir_with_fake_time(self):
        with FakeGame() as game:
            log = log_module(game)
            log.info("Tag", "first")
            game.advance(3)
            log.warn("Tag", "second")
            lines = game.log_lines()  # read while the log file is still open: the lines are flushed
            self.assertEqual(game.files(), ["mod.log"])
            first, second = (LINE.match(line) for line in lines)
            self.assertEqual((first.group(3), first.group(5)), ("INFO", "first"))
            self.assertEqual(int(second.group(1)) - int(first.group(1)), 3)
            self.assertEqual(int(second.group(2)), int(first.group(2)) + 1)

    def test_default_folder_is_used_without_the_env_variable(self):
        with FakeGame(env={"HARNESS_RUN_DIR": None}) as game:
            self.assertEqual(log_module(game).dir(), "ue4ss/harness")

    def test_say_prints_to_the_console(self):
        with FakeGame() as game:
            log_module(game).say("Tag", "hello")
            self.assertEqual(game.printed(), ["[Tag] hello\n"])
            self.assertEqual(len(game.log_lines()), 1)

    def test_try_logs_a_traceback_and_returns_false(self):
        with FakeGame() as game:
            result = game.exec('''
                local log = require("HarnessLog")
                local ok = log.try("Tag", function() error("boom") end)
                return ok''')
            self.assertFalse(result)
            text = game.read_text("mod.log")
            self.assertIn("ERROR [Tag]", text)
            self.assertIn("boom", text)
            self.assertIn("stack traceback", text)


if __name__ == "__main__":
    unittest.main()
