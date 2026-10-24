"""Mock tests for HarnessBattlefield (spec 10, issue #99): move all battlefield actors to an anchor, challenge, restore later.

The fake world copies the technique, not proven game behavior: initChallenge stores the position of the FIRST battlefield
actor as Challenge.Center. The real game picks one actor inside initChallenge. The A/B in the real game decides.
"""

import json
import unittest

import fakegame_path  # noqa: F401
from fakegame import FakeGame
from test_fakegame_harnesslords import BUILD_WORLD

ADD_BATTLEFIELDS = """
function(fg, world)
    local engine = FindFirstOf("RTSMultiEngineCPP")
    local home = world.player.currentRegion
    local manor = fg.object("SMBuildingMaster", {})
    fg.set_method(manor, "K2_GetActorLocation", function() return { X = 5000.0, Y = 6000.0, Z = 70.0 } end)
    home.manor = manor
    world.fields = {}
    for i, at in ipairs({ { 100.0, 200.0 }, { 900.0, 800.0 } }) do
        local field = fg.object("battlefield_BP_C", {})
        local place = { X = at[1], Y = at[2], Z = 10.0 }
        fg.set_method(field, "K2_GetActorLocation", function() return { X = place.X, Y = place.Y, Z = place.Z } end)
        fg.set_method(field, "K2_SetActorLocation", function(self, to) place = { X = to.X, Y = to.Y, Z = to.Z }; return true end)
        world.fields[#world.fields + 1] = field
    end
    fg.set_method(engine, "initChallenge", function(self, target, by, region)
        local first = world.fields[1]
        local at = first:K2_GetActorLocation()
        fg.array_add(engine.challenges, { ID = 0, challengedPawn = target, challengedBy = by, DaysLeft = 90, status = 0,
                                          contested = false, inRegardsTo = fg.array({ region }, { wrap = false }),
                                          Center = at, Battlefield = first })
    end)
end
"""


class BattlefieldTestCase(unittest.TestCase):
    def setUp(self):
        self.game = FakeGame()
        self.game.start()
        self.addCleanup(self.game.close)
        self.game.exec("FName = function(text) return { fname = text } end")
        world = self.game.lua.eval(BUILD_WORLD)(self.game.fg)
        self.game.lua.eval(ADD_BATTLEFIELDS)(self.game.fg, world)
        self.game.load_mod("HarnessActions")
        self.game.advance(1)
        self.number = 0

    def send(self, command, **fields):
        self.number += 1
        folder = self.game.run_dir / "commands"
        folder.mkdir(exist_ok=True)
        (folder / f"{self.number:04d}.json").write_text(json.dumps({"id": f"{self.number:04d}", "command": command, **fields}), encoding="utf-8")
        self.game.advance(1)
        return json.loads((folder / f"{self.number:04d}.result.json").read_text(encoding="utf-8"))


class AnchorTests(BattlefieldTestCase):
    def test_without_an_anchor_the_challenge_uses_the_first_battlefield(self):
        self.send("lord_challenge", lord=1, target=0)
        challenge = self.send("lords_state", log=0)["challenges"][0]
        self.assertEqual(challenge["center"], {"x": 100, "y": 200})

    def test_the_manor_is_the_default_anchor_and_the_challenge_keeps_it(self):
        answer = self.send("battlefield_anchor", lord=1, target=0)
        self.assertTrue(answer["ok"], answer)
        self.assertEqual((answer["anchor_kind"], answer["anchor"]["x"], answer["anchor"]["y"]), ("manor", 5000, 6000))
        self.assertEqual((answer["found"], answer["moved"]), (2, 2))
        self.assertTrue(answer["challenge"]["ok"], answer["challenge"])
        self.game.advance(1)
        challenge = self.send("lords_state", log=0)["challenges"][0]
        self.assertEqual(challenge["center"], {"x": 5000, "y": 6000})

    def test_state_names_the_anchor_without_moving_anything(self):
        state = self.send("battlefield_state", target=0)
        self.assertEqual((state["would_anchor"]["x"], state["would_anchor"]["y"], state["would_anchor_kind"]), (5000, 6000, "manor"))
        self.assertEqual(state["positions"][0], {"x": 100, "y": 200, "z": 10})

    def test_the_actors_go_back_after_the_delay(self):
        self.send("battlefield_anchor", x=10, y=20, delay_ms=5000)
        self.assertEqual(self.send("battlefield_state")["positions"][0], {"x": 10, "y": 20, "z": 0})
        self.game.advance(6)
        state = self.send("battlefield_state")
        self.assertEqual(state["positions"], [{"x": 100, "y": 200, "z": 10}, {"x": 900, "y": 800, "z": 10}])
        self.assertFalse(state["anchor_active"])
        self.assertEqual(state["last_restore"], {"restored": 2, "failed": 0})

    def test_a_second_anchor_is_refused_while_one_is_active(self):
        self.send("battlefield_anchor", x=10, y=20, delay_ms=5000)
        answer = self.send("battlefield_anchor", x=30, y=40)
        self.assertFalse(answer["ok"])
        self.assertIn("still active", answer["error"])

    def test_bad_input_is_refused(self):
        self.assertFalse(self.send("battlefield_anchor", x=10)["ok"])
        self.assertFalse(self.send("battlefield_anchor", x=10, y=20, delay_ms=-1)["ok"])
        self.assertFalse(self.send("battlefield_anchor", x=10, y=20, delay_ms=999999)["ok"])
        self.assertFalse(self.send("battlefield_anchor", x=9e9, y=0)["ok"])
        self.assertFalse(self.send("battlefield_anchor", region="Nowhere")["ok"])
        self.assertEqual(self.send("battlefield_state")["positions"][0], {"x": 100, "y": 200, "z": 10})

SETUP_HOME_ANCHOR = """
function(fg, mode)
    local engine = FindFirstOf("RTSMultiEngineCPP")
    local home = engine.playerRef.currentRegion
    local other
    for _, region in ipairs(require("ManorCore").listOf(engine.regions)) do
        if region:GetFullName() ~= home:GetFullName() then other = region end
    end
    fg.set_method(engine.playerRef, "GetAddress", function() return 1 end)
    home.ownerPawn = engine.playerRef
    engine.playerRef.currentRegion = other
    if mode == "no_manor" then
        home.manor = nil
        local buildings = {}
        for _, at in ipairs({ { 1000.0, 2000.0 }, { 3000.0, 4000.0 } }) do
            local building = fg.object("SMBuildingMaster", {})
            fg.set_method(building, "K2_GetActorLocation", function() return { X = at[1], Y = at[2], Z = 0.0 } end)
            buildings[#buildings + 1] = building
        end
        fg.set_method(home, "GetBuildings", function() return fg.array(buildings, { wrap = false }) end)
    end
end
"""


class HomeAnchorTests(BattlefieldTestCase):
    def camera_elsewhere(self, mode):
        self.game.lua.eval(SETUP_HOME_ANCHOR)(self.game.fg, mode)

    def test_the_home_anchor_is_the_manor_with_the_camera_in_another_region(self):
        self.camera_elsewhere("manor")
        answer = self.send("battlefield_anchor", lord=1, home=True)
        self.assertTrue(answer["ok"], answer)
        self.assertEqual((answer["anchor_kind"], answer["anchor"]["x"], answer["anchor"]["y"]), ("manor", 5000, 6000))
        self.game.advance(1)
        self.assertEqual(self.send("lords_state", log=0)["challenges"][0]["center"], {"x": 5000, "y": 6000})

    def test_without_a_manor_the_anchor_is_the_average_of_the_buildings(self):
        self.camera_elsewhere("no_manor")
        answer = self.send("battlefield_anchor", home=True)
        self.assertTrue(answer["ok"], answer)
        self.assertEqual((answer["anchor_kind"], answer["anchor"]["x"], answer["anchor"]["y"]), ("buildings_average", 2000, 3000))

    def test_the_camera_region_does_not_change_the_home_anchor(self):
        self.camera_elsewhere("manor")
        state = self.send("battlefield_state", home=True)
        self.assertEqual((state["would_anchor"]["x"], state["would_anchor_kind"]), (5000, "manor"))
        self.assertEqual(self.send("battlefield_state", target=0)["would_anchor_kind"], "village_centre")


if __name__ == "__main__":
    unittest.main()
