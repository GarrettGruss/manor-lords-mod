"""Tests for ManorCore.remove_families (change fix-removed-families-bodies) in the fake game.

The fake units are hidden when SetActorHiddenInGame(true) is called, and a death adds the unit to Region.corpses, as the real game does
(spike-rebel-without-corpses). These tests do not prove how the real game behaves: the real-game test scenario is `removed-families-bodies`.
"""

import unittest

import fakegame_path  # noqa: F401
from fakegame import FakeGame

WORLD = """
function(fg, fail_hide_on)
    local world = { destroyed = 0, units = {} }
    local old_bodies = {}
    for i = 1, 2 do
        local body = fg.object("SMUnit", { dead = true, bHidden = false }, "/Game/Fake/OldBody" .. i)
        old_bodies[#old_bodies + 1] = body
    end
    local corpses = fg.array(old_bodies, { wrap = false })
    local families = {}
    local n = 0
    for _, members in ipairs({ 2, 3, 1 }) do
        local list = {}
        for _ = 1, members do
            n = n + 1
            local unit = fg.object("SMUnit", { dead = false, bHidden = false }, "/Game/Fake/Person" .. n)
            fg.set_method(unit, "just_die", function(self) self.dead = true fg.array_add(corpses, self) end)
            fg.set_method(unit, "SetActorHiddenInGame", function(self, hidden)
                if n and fail_hide_on and self == world.units[fail_hide_on] then error("hide failed") end
                self.bHidden = hidden
            end)
            fg.set_method(unit, "K2_DestroyActor", function() world.destroyed = world.destroyed + 1 end)
            list[#list + 1] = unit
            world.units[#world.units + 1] = unit
        end
        families[#families + 1] = { familyMembers = fg.array(list, { wrap = false }) }
    end
    world.region = fg.object("Region", { workerFamilies = fg.array(families, { wrap = false }), corpses = corpses })
    world.old_bodies = old_bodies
    return world
end
"""


class RemoveFamiliesBodiesTests(unittest.TestCase):
    def setUp(self):
        self.game = FakeGame()
        self.game.start()
        self.addCleanup(self.game.close)
        self.core = self.game.lua.eval("function() return (require('ManorCore')) end")()

    def build(self, fail_hide_on=None):
        builder = self.game.lua.eval(WORLD)
        return builder(self.game.fg, fail_hide_on)

    def count(self, region):
        return self.game.lua.eval("function(r) return r.corpses:GetArrayNum() end")(region)

    def test_the_dead_are_hidden_and_the_body_count_does_not_rise(self):
        world = self.build()
        families, people = self.core.remove_families(world.region, 2)
        self.assertEqual((families, people), (2, 5))
        for index in range(1, 6):
            self.assertTrue(world.units[index].dead)
            self.assertTrue(world.units[index].bHidden)
        self.assertFalse(world.units[6].dead)
        self.assertEqual(self.count(world.region), 2)
        self.assertEqual(world.destroyed, 0)

    def test_old_bodies_stay_in_the_count_and_stay_visible(self):
        world = self.build()
        self.core.remove_families(world.region, 3)
        self.assertEqual(self.count(world.region), 2)
        self.assertFalse(world.old_bodies[1].bHidden)
        self.assertFalse(world.old_bodies[2].bHidden)

    def test_a_failed_hide_does_not_stop_the_other_bodies(self):
        world = self.build(fail_hide_on=2)
        families, people = self.core.remove_families(world.region, 1)
        self.assertEqual((families, people), (1, 2))
        self.assertTrue(world.units[1].bHidden)
        self.assertFalse(world.units[2].bHidden)


if __name__ == "__main__":
    unittest.main()
