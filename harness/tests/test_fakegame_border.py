"""Tests for the map border module of the invasion feature (change update-spawn-from-map-border) in the fake game.

They run the real Lua files. The map edge actor, the battlefield anchor and the lord calls are stand-ins. They do not prove that
the real game walks the armies in (see the test scenario `invasion-border-arrival` for that).
"""

import unittest

import fakegame_path  # noqa: F401
from test_fakegame_invasion import InvasionTestCase

# The playable square of Jagged_Cliffs (spike B, run 20261028-020728-5a13) and the player manor of the test save.
BOUNDS = "{ min_x = -89459, max_x = 84174, min_y = -89040, max_y = 84593 }"
MANOR = "{ x = -43956, y = -63097 }"

EDGE_ACTOR = """
local function spline(a, b)
    return {
        IsValid = function() return true end,
        GetNumberOfSplinePoints = function() return 2 end,
        GetLocationAtSplinePoint = function(_, index, space)
            assert(space == 1, "world space")
            local p = index == 0 and a or b
            return { X = p[1], Y = p[2], Z = 10000 }
        end,
    }
end
local edge = { IsValid = function() return true end }
edge.Spline1 = spline({ -89459, 84593 }, { 84174, -89040 })
edge.Spline2 = spline({ -89459, 84593 }, { -89459, -89040 })
edge.Spline3 = spline({ 84174, 84593 }, { 84174, -89040 })
local previous = FindFirstOf
FindFirstOf = function(name)
    if name == "Medium_Map_Bounds_C" then return edge end
    return previous(name)
end
"""

LORD_STUBS = """
STUB_LOG = { requests = {} }
package.loaded["HarnessLords"] = {
    spawn_ai_lord = function() return { ok = true, lord = 1 } end,
    lord_relations = function() return { ok = true } end,
    lord_start_ai = function() return { ok = true } end,
    lord_declare_war = function() return { ok = true } end,
    lord_declare_peace = function() return { ok = true } end,
    pawn_by_number = function() return nil end,
    lord_spawn_army = function(request)
        STUB_LOG.requests[#STUB_LOG.requests + 1] = string.format("%s,%s", tostring(request.x), tostring(request.y))
        return { ok = true, squads = { #STUB_LOG.requests } }
    end,
}
package.loaded["HarnessBattlefield"] = {
    battlefield_state = function() return { would_anchor = { x = -43956, y = -63097 } } end,
    battlefield_anchor = function() return { ok = true, anchor = { x = -43956, y = -63097 }, challenge = { ok = true } } end,
}
"""


class BorderTests(InvasionTestCase):
    PLAN_AT_START = False

    def lua(self, code):
        return self.game.exec(code, state=self.mod_name)

    def pick(self, target, extra=""):
        return self.lua(f"""
            local border = require("features.invasion.border")
            local p = border.pick({BOUNDS}, {target}, {{ margin = 3000, inset = 5000, min_distance = 30000 {extra} }})
            return string.format("%s %d %d", p.side, p.x, p.y)""")

    def test_the_nearest_side_far_enough_is_picked(self):
        # The south edge is 28943 units from the manor (less than 30000), so the west edge is the next one.
        self.assertEqual(self.pick(MANOR), "west -92459 -63097")

    def test_the_nearest_side_is_used_when_it_is_far_enough(self):
        self.assertEqual(self.pick("{ x = 20000, y = 40000 }"), "north 20000 87593")

    def test_the_point_is_outside_the_square_and_away_from_the_corners(self):
        self.assertEqual(self.pick("{ x = -89000, y = -88000 }"), "north -84459 87593")  # near the south-west corner: both near sides too close or at the corner
        self.assertEqual(self.lua(f"""
            local border = require("features.invasion.border")
            local p = border.pick({BOUNDS}, {MANOR}, {{ margin = 3000, inset = 5000, min_distance = 30000 }})
            return tostring(border.is_outside({BOUNDS}, p))"""), "true")

    def test_an_avoided_side_is_skipped(self):
        self.assertEqual(self.pick(MANOR, ", avoid = { x = -92459, y = -63097 }, avoid_distance = 1000").split()[0], "east")

    def test_the_direction_is_one_of_eight_words(self):
        words = self.lua("""
            local border = require("features.invasion.border")
            local out = {}
            for _, d in ipairs({ { 1, 0 }, { 1, 1 }, { 0, 1 }, { -1, 1 }, { -1, 0 }, { -1, -1 }, { 0, -1 }, { 1, -1 } }) do
                out[#out + 1] = border.direction({ x = 0, y = 0 }, { x = d[1] * 1000, y = d[2] * 1000 })
            end
            return table.concat(out, ",")""")
        self.assertEqual(words, "east,south-east,south,south-west,west,north-west,north,north-east")  # north is -y

    def test_the_other_north_axis_turns_the_words(self):
        word = self.lua("""
            local border = require("features.invasion.border")
            return border.direction({ x = 0, y = 0 }, { x = 0, y = 1000 }, "+y")""")
        self.assertEqual(word, "north")

    def test_bounds_come_from_the_map_edge_actor(self):
        self.lua(EDGE_ACTOR)
        text = self.lua("""
            local border = require("features.invasion.border")
            local b = border.read_bounds()
            return string.format("%d %d %d %d", b.min_x, b.max_x, b.min_y, b.max_y)""")
        self.assertEqual(text, "-89459 84174 -89040 84593")

    def test_no_edge_actor_gives_a_message(self):
        text = self.lua("""
            FindFirstOf = function() return nil end
            local border = require("features.invasion.border")
            local b, why = border.read_bounds()
            return tostring(b) .. " " .. why""")
        self.assertTrue(text.startswith("nil no map edge actor"), text)

    def test_a_lord_raid_spawns_at_the_border_point(self):
        self.lua(EDGE_ACTOR)
        self.lua(LORD_STUBS)
        text = self.lua("""
            local lord_raid = require("features.invasion.lord_raid")
            local config = require("config").invasion
            local point = lord_raid.plan_border(config.border)
            local ok, info = lord_raid.start({ "spearMilitia", "bowMilitia" }, config.roles.lord_army, point)
            return string.format("%s %s %s %s %s", tostring(ok), point.side, point.direction, STUB_LOG.requests[1], STUB_LOG.requests[2])""")
        self.assertEqual(text, "true west west -92459,-63097 -92459,-63097")

    def test_the_raid_shows_the_direction_and_arrives_later(self):
        self.lua(EDGE_ACTOR)
        self.lua(LORD_STUBS)
        self.assertTrue(self.ask("invasion_plan_now")["ok"])
        self.ask("invasion_set_size", size="small")
        self.ask("invasion_force_next")
        self.game.advance(2)
        self.assertIn("Raiders approach from the west", self.banners)
        self.assertNotIn("Raiders are here", self.banners)
        self.assertEqual(self.lua("return STUB_LOG.requests[1]"), "-92459,-63097")


if __name__ == "__main__":
    unittest.main()
