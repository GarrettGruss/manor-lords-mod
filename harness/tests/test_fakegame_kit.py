"""Tests for the fake game kit itself. Run from the repo root:
  uv run --no-project --python 3.12 --with lupa python -m unittest discover -s harness/tests -p "test_fakegame*.py"
"""

import os
import unittest

import fakegame_path  # noqa: F401
from fakegame import FakeGame, FakeGameClock, build_manor_lords_state
from lupa import LuaError

import boot_state_machine


class KitCase(unittest.TestCase):
    def make_game(self, **options):
        game = FakeGame(**options)
        game.start()
        self.addCleanup(game.close)
        return game


class ObjectTests(KitCase):
    def test_nil_key_read_and_write_fail(self):
        game = self.make_game()
        game.obj("Thing", size=3)
        with self.assertRaisesRegex(LuaError, "nil key"):
            game.exec("return FindFirstOf('Thing')[nil]")
        with self.assertRaisesRegex(LuaError, "nil key"):
            game.exec("local t = FindFirstOf('Thing'); t[nil] = 1")

    def test_properties_methods_and_builtins(self):
        game = self.make_game()
        thing = game.obj("Thing", size=3)
        game.method(thing, "Double", lambda self: self["size"] * 2)
        self.assertEqual(game.exec("return FindFirstOf('Thing'):Double()"), 6)
        self.assertTrue(game.exec("return FindFirstOf('Thing'):IsValid()"))
        self.assertIn("Thing", game.exec("return FindFirstOf('Thing'):GetFullName()"))
        self.assertIsNone(game.exec("return FindFirstOf('Missing')"))

    def test_invalid_object_fails_on_property_access_but_not_on_IsValid(self):
        game = self.make_game()
        thing = game.obj("Thing", size=3)
        game.invalidate(thing)
        self.assertIsNone(game.exec("return FindFirstOf('Thing')"))
        with self.assertRaisesRegex(LuaError, "invalid"):
            game.exec("return StaticFindObject('/Game/Fake/Thing_1').size")
        self.assertFalse(game.exec("return StaticFindObject('/Game/Fake/Thing_1'):IsValid()"))


class ArrayAndTextTests(KitCase):
    def test_plain_array_is_one_based_and_checks_range(self):
        game = self.make_game()
        game.static("/a", game.obj("Holder", items=game.array([10, 20])))
        self.assertEqual(game.exec("return StaticFindObject('/a').items:GetArrayNum()"), 2)
        self.assertEqual(game.exec("return StaticFindObject('/a').items[1]"), 10)
        with self.assertRaisesRegex(LuaError, "out of range"):
            game.exec("return StaticFindObject('/a').items[0]")
        with self.assertRaisesRegex(LuaError, "nil key"):
            game.exec("return StaticFindObject('/a').items[nil]")

    def test_wrapper_mode_needs_get(self):
        game = self.make_game(array_wrap=True)
        game.static("/a", game.obj("Holder", items=game.array([10, 20])))
        self.assertEqual(game.exec("return StaticFindObject('/a').items[2]:get()"), 20)
        with self.assertRaisesRegex(LuaError, "call :get"):
            game.exec("return StaticFindObject('/a').items[2].size")

    def test_array_can_fill_over_time(self):
        game = self.make_game()
        visible = {"count": 1}
        game.static("/a", game.obj("Holder", items=game.array([1, 2, 3], visible=lambda: visible["count"])))
        self.assertEqual(game.exec("return StaticFindObject('/a').items:GetArrayNum()"), 1)
        visible["count"] = 3
        self.assertEqual(game.exec("return StaticFindObject('/a').items:GetArrayNum()"), 3)

    def test_text_modes(self):
        fstring = self.make_game()
        self.assertEqual(fstring.exec("return nil"), None)
        self.assertEqual(fstring.lua.eval("function(t) return t:ToString() end")(fstring.text("hi")), "hi")
        plain = self.make_game(fstring_mode=False)
        self.assertEqual(plain.text("hi"), "hi")


class TimeAndLoopTests(KitCase):
    def test_fake_time_moves_only_when_the_test_moves_it(self):
        game = self.make_game()
        first = game.exec("return os.time()")
        self.assertEqual(game.exec("return os.time()"), first)
        game.advance(5)
        self.assertEqual(game.exec("return os.time()"), first + 5)
        self.assertEqual(game.exec("return os.clock()"), 5)

    def test_loop_runs_each_interval_and_stops_on_true(self):
        game = self.make_game()
        game.exec("count = 0; LoopAsync(1000, function() count = count + 1; return count >= 3 end)")
        game.advance(2)
        self.assertEqual(game.exec("return count"), 2)
        game.advance(10)
        self.assertEqual(game.exec("return count"), 3)
        self.assertEqual(game.fg.live_loops(), 0)

    def test_game_thread_work_waits_for_the_next_step(self):
        game = self.make_game()
        game.exec("ran = false; ExecuteInGameThread(function() ran = true end)")
        self.assertFalse(game.exec("return ran"))
        game.tick()
        self.assertTrue(game.exec("return ran"))

    def test_strict_threads_catch_object_access_in_a_loop(self):
        game = self.make_game(strict_threads=True)
        game.obj("Thing")
        game.exec("LoopAsync(100, function() FindFirstOf('Thing') end)")
        with self.assertRaisesRegex(LuaError, "outside the game thread"):
            game.tick()

    def test_run_until_idle_fails_loudly_at_the_limit(self):
        game = self.make_game()
        game.exec("LoopAsync(500, function() return false end)")
        with self.assertRaises(TimeoutError):
            game.run_until_idle(limit_seconds=5)


class KeyHookAndSpawnTests(KitCase):
    def test_key_binds_match_key_and_modifiers(self):
        game = self.make_game()
        game.exec("""hits = 0
            RegisterKeyBind(Key.F1, function() hits = hits + 1 end)
            RegisterKeyBind(Key.R, {ModifierKey.CONTROL}, function() hits = hits + 10 end)""")
        self.assertEqual(game.press("F1"), 1)
        self.assertEqual(game.press("R"), 0)
        self.assertEqual(game.press("R", "CONTROL"), 1)
        self.assertEqual(game.exec("return hits"), 11)

    def test_unknown_key_name_fails(self):
        game = self.make_game()
        with self.assertRaisesRegex(LuaError, "unknown Key.F99"):
            game.exec("RegisterKeyBind(Key.F99, function() end)")

    def test_hook_arguments_are_wrappers(self):
        game = self.make_game()
        game.exec("seen = nil; RegisterHook('/Script/X:Y', function(self, n) seen = n:get() end)")
        game.fire_hook("/Script/X:Y", game.obj("Thing"), 42)
        self.assertEqual(game.exec("return seen"), 42)

    def test_new_object_callback(self):
        game = self.make_game()
        game.exec("names = 0; NotifyOnNewObject('Thing', function(o) names = names + 1 end)")
        game.spawn(game.obj("Thing"))
        self.assertEqual(game.exec("return names"), 1)


class EnvironmentTests(unittest.TestCase):
    def test_environment_is_restored_and_run_dir_removed(self):
        os.environ["KIT_TEST_VAR"] = "before"
        with FakeGame(env={"KIT_TEST_VAR": "inside", "KIT_TEST_NEW": "1"}) as game:
            self.assertEqual(game.exec("return os.getenv('KIT_TEST_VAR')"), "inside")
            self.assertEqual(game.exec("return os.getenv('HARNESS_RUN_DIR')"), str(game.run_dir))
            run_dir = game.run_dir
        self.assertEqual(os.environ["KIT_TEST_VAR"], "before")
        self.assertNotIn("KIT_TEST_NEW", os.environ)
        self.assertFalse(run_dir.exists())
        del os.environ["KIT_TEST_VAR"]


class ClockTests(KitCase):
    def make_clock_game(self, **clock_options):
        game = self.make_game()
        state = build_manor_lords_state(game, clock=FakeGameClock(**clock_options))
        state.loaded_at = game.now()  # as if LoadGame was called
        state.clock.start_load()
        return game, state

    def test_clock_is_held_at_zero_then_starts(self):
        game, state = self.make_clock_game(hold_seconds=4, late_revert_after=None)
        game.advance(3)
        self.assertEqual(state.clock.time, 0)
        game.advance(3)
        self.assertGreater(state.clock.time, 0)

    def test_pause_stops_the_clock_and_a_start_undoes_an_early_pause(self):
        game, state = self.make_clock_game(hold_seconds=4, late_revert_after=None)
        game.exec("FindFirstOf('PawnCPP'):pauseGame()")
        game.advance(6)
        self.assertGreater(state.clock.time, 0)  # the game start undid the pause
        game.exec("FindFirstOf('PawnCPP'):pauseGame()")
        frozen = state.clock.time
        game.advance(5)
        self.assertEqual(state.clock.time, frozen)
        self.assertEqual(game.exec("return FindFirstOf('RTSMultiEngineCPP').gameSpeed"), 0)

    def test_late_revert_restarts_the_clock_once(self):
        game, state = self.make_clock_game(hold_seconds=2, late_revert_after=6)
        game.advance(3)
        game.exec("FindFirstOf('PawnCPP'):pauseGame()")
        game.advance(2)
        frozen = state.clock.time
        game.advance(5)
        self.assertGreater(state.clock.time, frozen)

    def test_pause_flag_is_stuck_until_a_call_and_set_speed_zero_is_not_a_pause(self):
        game, state = self.make_clock_game(hold_seconds=1, late_revert_after=None)
        game.advance(2)
        self.assertTrue(game.exec("return FindFirstOf('PawnCPP').bIsPlayerPaused"))
        game.exec("FindFirstOf('PawnCPP'):setGameSpeed(0)")
        before = state.clock.time
        game.advance(3)
        self.assertGreater(state.clock.time, before)
        self.assertLess(state.clock.time - before, 3)


class BootWithWrapperModesTests(unittest.TestCase):
    """HarnessBoot must also work when arrays give wrappers and text gives FStrings."""

    def test_happy_path_in_each_wrapper_mode(self):
        for wrap in (False, True):
            for fstring in (False, True):
                boot, marker, _, _, clocks = boot_state_machine.run_mode(
                    "happy", array_wrap=wrap, fstring_mode=fstring)
                self.assertEqual(boot["state"], "READY", (wrap, fstring, boot["reason"]))
                self.assertEqual(clocks[0], clocks[1])


if __name__ == "__main__":
    unittest.main()
