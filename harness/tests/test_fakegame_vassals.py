"""Tests for the feature vassals of the pack mod (mod feature M07) in the fake game.

They run the real Lua files. HarnessGameSetup, HarnessLords and the region list are stubs.
They do not prove how the real game behaves (see the real-game runs in the iteration files).
"""

import json
import unittest

import fakegame_path  # noqa: F401
from fakegame import FakeGame
from test_fakegame_modstate import FNAME, HELPERS, find_pack_mod

STUB = """
GOAL = 3
GOAL_WRITES = 0
package.loaded["HarnessGameSetup"] = {
    game_setup_state = function() return { ok = true, goals = GOAL, victory_status = 0 } end,
    game_setup_set_goal = function(request)
        local before = GOAL
        GOAL = request.goal
        GOAL_WRITES = GOAL_WRITES + 1
        return { ok = true, before = { goals = before }, after = { goals = GOAL } }
    end,
}
REGIONS = {
    { region = "Home", owner = "Player", settled = true },
    { region = "Eichenhau", owner = nil, settled = false },
    { region = "Goldhof", owner = nil, settled = false },
    { region = "Taken", owner = "Baron", settled = true },
}
CLAIMS = {}
package.loaded["HarnessLords"] = {
    claim_region = function(request)
        if request.target ~= 0 or request.finalize ~= 1 then return { ok = false, error = "bad claim request" } end
        CLAIMS[#CLAIMS + 1] = request.region
        for _, row in ipairs(REGIONS) do
            if row.region == request.region then row.owner = "Player" end
        end
        return { ok = true }
    end,
}
local core = require("ManorCore")
core.regions_state = function() return { ok = true, regions = REGIONS } end
"""


class VassalsTestCase(unittest.TestCase):
    def setUp(self):
        self.game = FakeGame()
        self.game.start()
        self.addCleanup(self.game.close)
        pack = find_pack_mod()
        self.mod_name = pack.name
        self.game.exec(f'package.path = "{(pack / "Scripts").as_posix()}/?.lua;" .. package.path')
        self.game.exec(FNAME + HELPERS + STUB)
        self.pawn = self.game.obj("PawnCPP", Tags=self.game.array([]))
        self.calendar = self.game.obj("TemporalComponent", daysTotal=61, daysUntilNextRaid=730, Season=1)
        self.engine = self.game.obj("RTSMultiEngineCPP", playerRef=self.pawn, TemporalComponent=self.calendar,
                                    regions=self.game.array([]), debugLog_AI_general=self.game.array([]))
        self.game.load_mod(self.mod_name)
        self.game.advance(3)
        self.counter = 0

    def ask(self, name, **args):
        self.counter += 1
        folder = self.game.run_dir / "modcmd" / self.mod_name
        folder.mkdir(parents=True, exist_ok=True)
        body = {"id": f"{self.counter:04d}", "command": f"{self.mod_name}.{name}", "args": args}
        (folder / f"{self.counter:04d}.json").write_text(json.dumps(body), encoding="utf-8")
        self.game.advance(1)
        return json.loads((folder / f"{self.counter:04d}.result.json").read_text(encoding="utf-8"))

    def state(self):
        answer = self.ask("vassals_state")
        self.assertTrue(answer["ok"], answer)
        return answer["result"]

    def goal(self):
        return self.game.exec("return GOAL")

    def tags(self):
        return list(self.game.lua.eval("tag_names")(self.pawn).values())


class GoalTests(VassalsTestCase):
    def test_the_poll_writes_endless_once(self):
        self.assertEqual(self.goal(), 2)
        self.assertEqual(self.game.exec("return GOAL_WRITES"), 1)
        self.game.advance(10)
        self.assertEqual(self.game.exec("return GOAL_WRITES"), 1)
        self.assertEqual(self.state()["goal"], 2)

    def test_the_mod_writes_the_goal_back_when_the_game_changes_it(self):
        self.game.exec("GOAL = 3")
        self.game.advance(5)
        self.assertEqual(self.goal(), 2)
        self.assertEqual(self.state()["goal_writes"], 2)

    def test_the_set_goal_command_is_undone_by_the_poll(self):
        self.assertTrue(self.ask("vassals_set_goal", goal=3)["ok"])
        self.game.advance(5)
        self.assertEqual(self.goal(), 2)


class RegistryTests(VassalsTestCase):
    def claim(self, region):
        return self.ask("vassals_claim", region=region)

    def test_a_claim_registers_slot_one_with_the_start_loyalty(self):
        answer = self.claim("Eichenhau")
        self.assertTrue(answer["ok"], answer)
        result = answer["result"]
        self.assertEqual((result["count"], result["claimed_slot"]), (1, 1))
        row = result["vassals"][0]
        self.assertEqual((row["region"], row["loyalty"], row["since_day"]), ("Eichenhau", 50, 61))
        self.assertEqual(self.game.exec("return CLAIMS[1]"), "Eichenhau")

    def test_the_registry_is_kept_in_the_pawn_tags(self):
        self.claim("Eichenhau")
        tags = self.tags()
        self.assertIn("invasion:vassal1_region=Eichenhau", tags)
        self.assertIn("invasion:vassal1_since_day=61", tags)
        self.ask("vassals_set_loyalty", slot=1, value=70)
        self.assertIn("invasion:vassal1_loyalty=70", self.tags())

    def test_a_region_with_an_owner_cannot_be_claimed(self):
        answer = self.claim("Taken")
        self.assertFalse(answer["ok"])
        self.assertIn("owner", answer["error"])
        self.assertEqual(self.state()["count"], 0)

    def test_the_same_region_cannot_be_claimed_twice(self):
        self.claim("Eichenhau")
        self.game.exec('REGIONS[2].owner = nil')
        self.assertFalse(self.claim("Eichenhau")["ok"])

    def test_an_unknown_region_is_refused(self):
        self.assertFalse(self.claim("Nowhere")["ok"])

    def test_the_fourth_vassal_is_refused(self):
        self.game.exec('REGIONS[#REGIONS + 1] = { region = "R3" }; REGIONS[#REGIONS + 1] = { region = "R4" }')
        for name in ("Eichenhau", "Goldhof", "R3"):
            self.assertTrue(self.claim(name)["ok"])
        answer = self.claim("R4")
        self.assertFalse(answer["ok"])
        self.assertIn("slots", answer["error"])

    def test_loyalty_stays_between_0_and_100(self):
        self.claim("Eichenhau")
        self.assertEqual(self.ask("vassals_set_loyalty", slot=1, value=150)["result"]["vassals"][0]["loyalty"], 100)
        self.assertEqual(self.ask("vassals_set_loyalty", slot=1, value=-5)["result"]["vassals"][0]["loyalty"], 0)

    def test_loyalty_of_an_empty_slot_is_refused(self):
        self.assertFalse(self.ask("vassals_set_loyalty", slot=2, value=10)["ok"])


LORD_STUB = """
SPAWNED = {}
RECEIVED = {}
local old = package.loaded["HarnessLords"]
old.spawn_ai_lord = function(request)
    SPAWNED[#SPAWNED + 1] = request.name
    return { ok = true, lord = #SPAWNED }
end
old.lord_relations = function() return { ok = true } end
old.lord_start_ai = function() return { ok = true } end
old.lord_receive_region = function(request)
    RECEIVED[#RECEIVED + 1] = request.lord .. ":" .. request.region
    return { ok = true }
end
"""


class HandoverBase(VassalsTestCase):
    def setUp(self):
        super().setUp()
        self.counts = {}
        self.game.exec(LORD_STUB)
        self.game.method(self.pawn, "GetAddress", lambda _self: 1)
        self.home = self.make_region("Home", True, 12)
        self.regions = [self.home]
        self.engine.regions = self.game.array(self.regions)
        self.game.advance(8)

    def make_region(self, name, settled, buildings):
        region = self.game.obj("Region", ownerPawn=self.pawn, isSettled=settled)
        self.game.method(region, "GetFName", lambda _self, name=name: self.game.text(name))
        self.counts[name] = buildings
        self.game.method(region, "GetBuildings", lambda _self, name=name: self.game.array([self.game.struct()] * self.counts[name]))
        return region

    def add_region(self, name, settled, buildings=0):
        region = self.make_region(name, settled, buildings)
        self.regions.append(region)
        self.engine.regions = self.game.array(self.regions)
        return region

    def hand_over_and_wait(self, name="Eichenhau", buildings=4):
        self.add_region(name, True, buildings)
        self.game.advance(10)
        return self.state()


class HandoverTests(HandoverBase):
    def test_the_first_scan_picks_the_region_with_most_buildings_as_home(self):
        self.assertEqual(self.state()["home_region"], "Home")

    def test_an_unsettled_claim_is_registered_but_not_handed_over(self):
        self.add_region("Eichenhau", False)
        self.game.advance(8)
        state = self.state()
        self.assertEqual(state["count"], 1)
        self.assertEqual(state["vassals"][0]["lord"], "none")
        self.assertEqual(self.game.exec("return #SPAWNED"), 0)

    def test_a_settled_claim_is_handed_to_a_new_lord(self):
        region = self.add_region("Eichenhau", False)
        self.game.advance(8)
        region.isSettled = True
        self.game.advance(8)
        self.assertEqual(self.state()["vassals"][0]["lord"], "Aldric")
        self.assertEqual(self.game.exec('return SPAWNED[1] .. " " .. RECEIVED[1]'), "Aldric 1:Eichenhau")

    def test_the_handover_runs_once(self):
        self.add_region("Eichenhau", True)
        self.game.advance(30)
        self.assertEqual(self.game.exec("return #RECEIVED"), 1)
        self.assertEqual(self.game.exec("return #SPAWNED"), 1)

    def test_two_regions_get_two_lords(self):
        self.add_region("Eichenhau", True)
        self.add_region("Goldhof", True)
        self.game.advance(30)
        self.assertEqual(self.game.exec("return SPAWNED[1] .. SPAWNED[2]"), "AldricBertram")

    def test_a_failed_handover_stops_after_the_attempt_limit(self):
        self.game.exec('package.loaded["HarnessLords"].lord_receive_region = function() RECEIVED[#RECEIVED + 1] = "x"; return { ok = false, error = "boom" } end')
        self.add_region("Eichenhau", True)
        self.game.advance(80)
        state = self.state()
        self.assertEqual(state["vassals"][0]["lord"], "none")
        self.assertIn("boom", state["handover_errors"]["1"])
        self.assertEqual(self.game.exec("return #RECEIVED"), 3)

    def hand_over_and_wait(self, name="Eichenhau", buildings=4):
        self.add_region(name, True, buildings)
        self.game.advance(10)
        return self.state()

    def test_a_lord_that_builds_nothing_is_flagged_after_ten_days(self):
        self.hand_over_and_wait()
        self.calendar.daysTotal = self.calendar.daysTotal + 11
        self.game.advance(10)
        row = self.state()["vassals"][0]
        self.assertTrue(row["stalled"])
        self.assertIn("invasion:vassal1_stalled=true", self.tags())

    def test_a_lord_that_builds_is_not_flagged(self):
        self.hand_over_and_wait()
        self.counts["Eichenhau"] = 14
        self.calendar.daysTotal = self.calendar.daysTotal + 11
        self.game.advance(10)
        self.assertFalse(self.state()["vassals"][0]["stalled"])

    def test_no_check_before_ten_days(self):
        self.hand_over_and_wait()
        self.calendar.daysTotal = self.calendar.daysTotal + 5
        self.game.advance(10)
        self.assertFalse(self.state()["vassals"][0]["stalled"])


if __name__ == "__main__":
    unittest.main()
