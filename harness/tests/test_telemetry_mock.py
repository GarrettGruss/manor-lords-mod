# Tests for mod/shared/HarnessJson and mod/shared/HarnessTelemetry against a fake game API (no game needed).
# Run from the repo root:
#   uv run python -m unittest harness/tests/test_telemetry_mock.py -v
# These tests do not prove that the real UE4SS API behaves like the fake one. The real game test is in spec 04.
import json
import os
import pathlib
import tempfile
import unittest

from lupa import LuaRuntime

REPO = pathlib.Path(__file__).resolve().parents[2]

FAKE_GAME = r"""
local function valid() return true end

local function region(name, extra)
    local r = { IsValid = valid, regionName = name, isSettled = true, Approval = 50, publicOrder = 90,
        regionalWealth = 50, supplies_food = 2,
        getNumTotalPopulation = function(self) return 10 end,
        getNumHomelessFamilies = function(self) return 5 end }
    for k, v in pairs(extra or {}) do r[k] = v end
    return r
end

CLOCK = 100.0
IN_GAME = true
REGION_EXTRA = REGION_EXTRA or {}

local regions = { GetArrayNum = function() return 2 end, region("Hochweg"), region("Wilde Wand", REGION_EXTRA) }
local engine = { IsValid = valid,
    playerRef = { IsValid = valid, silver = 0, influence = 0, kingsFavour = 0 },
    TemporalComponent = { IsValid = valid, day = 61, month = 3, Year = 1, Season = 1 },
    regions = regions,
    getGameTimeAdjusted = function(self) return CLOCK end }

function FindFirstOf(name)
    if name == "RTSMultiEngineCPP" and IN_GAME then return engine end
    return nil
end
function ExecuteInGameThread(fn) fn() end
LOOPS = {}
function LoopAsync(ms, fn) LOOPS[#LOOPS + 1] = { ms = ms, fn = fn } end
"""


class Game:
    """One fresh Lua runtime with the fake game and the harness modules loaded."""

    def __init__(self, interval=None, region_extra_lua="{}"):
        self.dir = tempfile.mkdtemp(prefix="telemetry-test-")
        os.environ["HARNESS_RUN_DIR"] = self.dir
        if interval is None:
            os.environ.pop("HARNESS_TELEMETRY_INTERVAL_S", None)
        else:
            os.environ["HARNESS_TELEMETRY_INTERVAL_S"] = str(interval)
        self.lua = LuaRuntime(unpack_returned_tuples=True)
        self.lua.execute(f'package.path = "{REPO.as_posix()}/mod/shared/?/?.lua;" .. package.path')
        self.lua.execute(f"REGION_EXTRA = {region_extra_lua}")
        self.lua.execute(FAKE_GAME)
        self.telemetry = self.lua.eval('(require("HarnessTelemetry"))')
        self.json = self.lua.eval('(require("HarnessJson"))')

    def samples(self):
        path = pathlib.Path(self.dir, "telemetry.jsonl")
        if not path.exists():
            return []
        return [json.loads(line) for line in path.read_text().splitlines()]

    def tick(self):
        """Run the sampler loop body once, like the game would."""
        self.lua.execute("LOOPS[1].fn()")


class JsonEncoderTests(unittest.TestCase):
    def setUp(self):
        self.json = Game().json

    def encode(self, lua_source):
        return json.loads(self.json.encode(Game().lua.eval(lua_source)))

    def test_scalars_and_nil(self):
        game = Game()
        encode = game.json.encode
        self.assertEqual(encode(None), "null")
        self.assertEqual(encode(True), "true")
        self.assertEqual(encode(3), "3")
        self.assertEqual(json.loads(encode(0.5)), 0.5)

    def test_string_escapes(self):
        game = Game()
        text = 'a "quote" \\ back\nnew\tline'
        self.assertEqual(json.loads(game.json.encode(text)), text)

    def test_nan_and_infinity_become_null(self):
        game = Game()
        self.assertEqual(game.lua.eval("require('HarnessJson').encode(0/0)"), "null")
        self.assertEqual(game.lua.eval("require('HarnessJson').encode(math.huge)"), "null")

    def test_array_and_object(self):
        game = Game()
        self.assertEqual(json.loads(game.lua.eval("require('HarnessJson').encode({1,2,3})")), [1, 2, 3])
        self.assertEqual(json.loads(game.lua.eval("require('HarnessJson').encode({b=1,a=2})")), {"a": 2, "b": 1})

    def test_object_marker_keeps_an_empty_object(self):
        game = Game()
        self.assertEqual(game.lua.eval("require('HarnessJson').encode(require('HarnessJson').object({}))"), "{}")

    def test_object_keys_are_sorted_for_stable_output(self):
        game = Game()
        self.assertEqual(game.lua.eval("require('HarnessJson').encode({b=1,a=2,c=3})"), '{"a":2,"b":1,"c":3}')

    def test_function_value_fails_loudly(self):
        game = Game()
        with self.assertRaises(Exception):
            game.lua.eval("require('HarnessJson').encode({f=function() end})")


class SampleTests(unittest.TestCase):
    def test_sample_has_all_fields(self):
        game = Game()
        game.telemetry.start()
        game.tick()
        (sample,) = game.samples()
        self.assertEqual(sample["n"], 1)
        self.assertEqual(sample["clock"], 100)
        self.assertEqual(sample["date"], {"day": 61, "month": 3, "year": 1, "season": 1})
        self.assertEqual(sample["player"], {"silver": 0, "influence": 0, "kingsFavour": 0})
        self.assertEqual(sample["errors"], [])
        self.assertEqual(len(sample["regions"]), 2)
        self.assertEqual(sample["regions"][0], {
            "name": "Hochweg", "settled": True, "approval": 50, "publicOrder": 90, "wealth": 50,
            "food": 2, "population": 10, "homeless": 5})
        self.assertEqual(sample["custom"], {})

    def test_first_sample_has_no_paused_value_and_later_ones_do(self):
        game = Game()
        game.telemetry.start()
        game.tick()
        game.tick()  # the clock did not move: paused
        game.lua.execute("CLOCK = 105.0")
        game.tick()  # the clock moved: running
        first, second, third = game.samples()
        self.assertIsNone(first["paused"])
        self.assertTrue(second["paused"])
        self.assertFalse(third["paused"])

    def test_menu_gives_no_sample(self):
        game = Game()
        game.lua.execute("IN_GAME = false")
        game.telemetry.start()
        game.tick()
        self.assertEqual(game.samples(), [])

    def test_unreadable_field_is_null_and_counted_and_others_survive(self):
        # Region 2 has no readable Approval: reading it raises an error.
        game = Game(region_extra_lua="{ Approval = nil, __missing = true }")
        game.lua.execute("""
            local regions = FindFirstOf('RTSMultiEngineCPP').regions
            local second = regions[2]
            second.Approval = nil
        """)
        game.telemetry.start()
        game.tick()
        (sample,) = game.samples()
        self.assertIsNone(sample["regions"][1]["approval"])
        self.assertIn("region2.approval", sample["errors"])
        self.assertEqual(sample["regions"][1]["wealth"], 50)
        self.assertEqual(sample["regions"][0]["approval"], 50)

    def test_custom_metric_and_a_failing_custom_metric(self):
        game = Game()
        game.lua.execute("""
            local t = require('HarnessTelemetry')
            t.register('farms', function() return 7 end)
            t.register('broken', function() error('boom') end)
        """)
        game.telemetry.start()
        game.tick()
        (sample,) = game.samples()
        self.assertEqual(sample["custom"]["farms"], 7)
        self.assertNotIn("broken", sample["custom"])
        self.assertIn("custom.broken", sample["errors"])

    def test_register_rejects_bad_arguments(self):
        game = Game()
        with self.assertRaises(Exception):
            game.lua.execute("require('HarnessTelemetry').register('', function() end)")
        with self.assertRaises(Exception):
            game.lua.execute("require('HarnessTelemetry').register('x', 5)")

    def test_every_line_is_valid_json_and_samples_are_numbered(self):
        game = Game()
        game.telemetry.start()
        for _ in range(4):
            game.tick()
        self.assertEqual([s["n"] for s in game.samples()], [1, 2, 3, 4])


class StartTests(unittest.TestCase):
    def test_default_interval_is_5_seconds(self):
        game = Game()
        game.telemetry.start()
        self.assertEqual(game.lua.eval("LOOPS[1].ms"), 5000)

    def test_interval_from_environment(self):
        game = Game(interval=2.5)
        game.telemetry.start()
        self.assertEqual(game.lua.eval("LOOPS[1].ms"), 2500)

    def test_interval_zero_turns_it_off(self):
        game = Game(interval=0)
        self.assertFalse(game.telemetry.start())
        self.assertEqual(game.lua.eval("#LOOPS"), 0)

    def test_bad_interval_falls_back_to_default(self):
        game = Game(interval="abc")
        game.telemetry.start()
        self.assertEqual(game.lua.eval("LOOPS[1].ms"), 5000)

    def test_second_start_does_nothing(self):
        game = Game()
        self.assertTrue(game.telemetry.start())
        self.assertFalse(game.telemetry.start())
        self.assertEqual(game.lua.eval("#LOOPS"), 1)


if __name__ == "__main__":
    unittest.main()
