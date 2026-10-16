"""The four sack scenarios (sack-village, sack-ruins, sack-store-trip, loot-drop-recovery) against the REAL Lua files in the fake game kit.

The chain: scenario code -> Actions -> CommandChannel -> request files -> HarnessActions -> HarnessSack / HarnessLoot -> a fake village.
Only the game is fake. This checks the logic of the scenarios and of the Lua modules. It does NOT prove that the real game behaves the same:
the real runs are listed in docs/harness/10-invasion-testability/implementation-notes/spike-S6.md.
"""

import unittest

import fakegame_path  # noqa: F401
import runlib_path  # noqa: F401
from fakegame import FakeGame
from modstate_support import sleep_in
from runlib.actions import Actions
from runlib.commands import CommandChannel
from runlib.expectations import Expectations
from runlib.waiting import WaitTimeout
from scenarios import loot_drop_recovery, sack_ruins, sack_store_trip, sack_village
from test_fakegame_harnesssack import BUILD_VILLAGE, BURN_OUT

# What the scenarios need on top of the village of test_fakegame_harnesssack: stock and count reads, the cheat manager, raiders.
EXTEND_VILLAGE = """
function(fg, village, options)
    local region = village.region
    fg.set_method(region, "getStockOfGood", function(self, kind)
        local n = 0
        for _, b in ipairs(village.buildings) do
            for _, g in ipairs(b.items) do if g.Type == kind then n = n + g.amt end end
        end
        return n
    end)
    fg.set_method(region, "getBuildingCount", function(self, kind)
        local n = 0
        for _, b in ipairs(village.buildings) do if b.Data.bType == kind then n = n + 1 end end
        return n
    end)
    local cheat = fg.object("MLCheatManager", {})
    village.cheat = cheat
    -- GiveItemByID puts the goods into the first building of the village (seen in the real game).
    fg.set_method(cheat, "GiveItemByID", function(self, kind, amount)
        local first = village.buildings[1]
        for _, g in ipairs(first.items) do
            if g.Type == kind then g.amt = g.amt + amount; return end
        end
        first.items[#first.items + 1] = { Type = kind, amt = amount }
    end)
    fg.set_method(village.player, "K2_GetActorLocation", function() return { X = 0, Y = 0, Z = 0 } end)
    fg.object("PawnCPP", { isMainPlayer = false, isBandit = true, isAI = true, commandedSquads = fg.array({ { Value = 5 } }, { wrap = false }) })
    fg.set_method(village.engine, "spawnRaiders", function(self, squads, center)
        for i = 1, squads * 18 do
            local unit = fg.object("SMUnit", { dead = false, assignedSquadID = { Value = 5 }, currentUnitRole = 5, ItemsLooted = 0,
                                               morale = 1.0, combatExperience = 0.0, realPos = { X = 100.0 * i, Y = -50.0, Z = 0 } })
            fg.set_method(unit, "just_die", function(me) me.dead = true; me.ItemsLooted = 0 end)
        end
    end)
end
"""


class VillageBridge:
    """The bridge calls that the sack scenarios make, answered by the fake village."""

    def __init__(self, village):
        self.village = village

    def engine_path(self):
        return "engine"

    def player_region_path(self):
        return "region"

    def call_function(self, ref, function, args=None):
        target = self.village.cheat if ref == "first:MLCheatManager" else self.village.region
        return target[function](target, *(args or []))

    def read_property(self, ref, name):
        if name == "bAnyBuildingOnFire":
            return any(building["onFire"] for building in self.village.buildings.values())
        if name == "currentGameVictoryStatus":
            return 0
        raise KeyError(name)


class FakeSackTime:
    """`set_speed` is where game time passes: the fires burn out then."""

    def __init__(self, game, village, burns_out=True):
        self.game = game
        self.village = village
        self.burns_out = burns_out
        self.calls = []

    def set_speed(self, speed):
        self.calls.append(("set_speed", speed))
        if self.burns_out:
            self.game.lua.eval(BURN_OUT)(self.village)

    def pause(self):
        self.calls.append(("pause",))

    def run_game_days(self, days, speed=1):
        self.calls.append(("run_game_days", days, speed))


class SackContext:
    def __init__(self, game, village, burns_out=True):
        sleep = sleep_in(game)
        self.expect = Expectations(sleep=sleep, monotonic=game.now)
        self.notes = []
        self.bridge = VillageBridge(village)
        self.commands = CommandChannel(game.run_dir / "commands", sleep=sleep, monotonic=game.now)
        self.actions = Actions(self.bridge, self.expect, self.notes, commands=self.commands)
        self.time = FakeSackTime(game, village, burns_out)
        self.popups = lambda: None

    def run_until(self, predicate, timeout_s, **options):
        if not predicate():
            raise WaitTimeout(f"timeout: {options.get('what', 'the condition')} was not true")

    def result(self):
        result = self.expect.result()
        result["notes"] = list(self.notes)
        return result


def running_village(**options):
    game = FakeGame()
    game.start()
    village = game.lua.eval(BUILD_VILLAGE)(game.fg, game.lua.table_from(options))
    game.lua.eval(EXTEND_VILLAGE)(game.fg, village, game.lua.table_from(options))
    game.load_mod("HarnessActions")
    game.advance(1)
    return game, village


class SackScenarioTests(unittest.TestCase):
    def run_scenario(self, module, burns_out=True, **options):
        game, village = running_village(**options)
        self.addCleanup(game.close)
        ctx = SackContext(game, village, burns_out)
        result = module.run(ctx)
        return result, [a["name"] for a in result["asserts"] if not a["ok"]], ctx

    def test_sack_village_passes(self):
        result, failed, ctx = self.run_scenario(sack_village)
        self.assertEqual(failed, [])
        self.assertGreaterEqual(len(result["asserts"]), 20)
        self.assertIn(("run_game_days", 1, 3), ctx.time.calls)

    def test_sack_ruins_passes(self):
        result, failed, ctx = self.run_scenario(sack_ruins)
        self.assertEqual(failed, [])
        self.assertIn(("set_speed", sack_ruins.SPEED), ctx.time.calls)

    def test_sack_store_trip_passes(self):
        result, failed, ctx = self.run_scenario(sack_store_trip)
        self.assertEqual(failed, [])
        self.assertTrue(any("stores: barn" in note for note in ctx.notes))

    def test_loot_drop_recovery_passes(self):
        result, failed, _ = self.run_scenario(loot_drop_recovery)
        self.assertEqual(failed, [])
        self.assertGreaterEqual(len(result["asserts"]), 10)

    def test_a_game_that_does_not_remove_goods_fails_the_goods_checks(self):
        for module in (sack_village, sack_store_trip):
            result, failed, _ = self.run_scenario(module, refuse_consume=True)
            self.assertTrue(failed, module.NAME)
            self.assertFalse(result["passed"], module.NAME)

    def test_fires_that_never_go_out_time_out_the_ruins_scenario(self):
        game, village = running_village()
        self.addCleanup(game.close)
        with self.assertRaisesRegex(WaitTimeout, "fires to burn out"):
            sack_ruins.run(SackContext(game, village, burns_out=False))

    def test_scenarios_carry_the_metadata_the_coverage_tool_reads(self):
        for module, covers in ((sack_village, ["S1"]), (sack_ruins, []), (sack_store_trip, ["R7"]), (loot_drop_recovery, ["R3"])):
            self.assertEqual(module.COVERS, covers)
            self.assertIsInstance(module.LIMIT_S, int)
            self.assertTrue(module.NAME and module.DESCRIPTION)


if __name__ == "__main__":
    unittest.main()
