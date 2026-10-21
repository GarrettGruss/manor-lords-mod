"""HarnessClickHooks: the click hook must not raise a Lua error for a dead widget (#323)."""

import unittest

import fakegame_path  # noqa: F401
from fakegame import FakeGame


class ClickHookTests(unittest.TestCase):
    def test_dead_widget_does_not_raise_and_live_widget_is_queued(self):
        with FakeGame() as game:
            ok = game.exec('''
                local callback
                RegisterHook = function(path, fn) callback = fn end
                local hooks = require("HarnessClickHooks")
                StaticFindObject = function()
                    return { IsValid = function() return true end,
                             Create = function() return { IsValid = function() return true end,
                                 GetFullName = function() return "W1" end,
                                 GetFName = function() return { ToString = function() return "W1" end } end } end }
                end
                hooks.attach({ SetContent = function() end }, {}, { owner = "o" })
                local dead = { IsValid = function() return false end,
                               GetFullName = function() error("dead object") end }
                local live = { IsValid = function() return true end, GetFullName = function() return "W1" end }
                local no_error = pcall(callback, { get = function() return dead end })
                callback({ get = function() return live end })
                return no_error and #hooks.drain("o") == 1''')
            self.assertTrue(ok)


if __name__ == "__main__":
    unittest.main()
