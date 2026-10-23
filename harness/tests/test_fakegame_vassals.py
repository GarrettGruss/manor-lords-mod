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
    SAVED_TAGS = ()  # tags that the pawn holds when the mod loads (an old save)

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
        add_tag = self.game.lua.eval("function(pawn, text) pawn.Tags[#pawn.Tags + 1] = FName(text) end")
        for text in self.SAVED_TAGS:
            add_tag(self.pawn, text)
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

    def test_a_claim_registers_slot_one(self):
        answer = self.claim("Eichenhau")
        self.assertTrue(answer["ok"], answer)
        result = answer["result"]
        self.assertEqual((result["count"], result["claimed_slot"]), (1, 1))
        row = result["vassals"][0]
        self.assertEqual((row["region"], row["since_day"]), ("Eichenhau", 61))
        self.assertNotIn("loyalty", row)
        self.assertEqual(self.game.exec("return CLAIMS[1]"), "Eichenhau")

    def test_the_registry_is_kept_in_the_pawn_tags(self):
        self.claim("Eichenhau")
        tags = self.tags()
        self.assertIn("invasion:vassal1_region=Eichenhau", tags)
        self.assertIn("invasion:vassal1_since_day=61", tags)
        self.assertFalse(any("loyalty" in tag or "submitted" in tag for tag in tags))

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


class OldSaveTests(VassalsTestCase):
    """Saves from before the removal of loyalty hold vassal1_loyalty and vassal1_submitted (change remove-vassal-loyalty)."""
    SAVED_TAGS = ("invasion:vassal1_region=Eichenhau", "invasion:vassal1_lord=Aldric", "invasion:vassal1_loyalty=7",
                  "invasion:vassal1_submitted=true", "invasion:vassals_submissions=1", "invasion:vassals_last_season=2")

    def test_the_old_fields_are_ignored_and_a_submitted_vassal_is_a_normal_vassal(self):
        state = self.state()
        self.assertEqual(state["count"], 1)
        row = state["vassals"][0]
        self.assertEqual((row["region"], row["lord"]), ("Eichenhau", "Aldric"))
        self.assertNotIn("loyalty", row)
        self.assertNotIn("submitted", row)
        self.assertIn(row["region"], self.game.exec("return table.concat(require('features.vassals.init').slot_regions(), ',')"))


LORD_STUB = """
SPAWNED = {}
RECEIVED = {}
local old = package.loaded["HarnessLords"]
old.spawn_ai_lord = function(request)
    SPAWNED[#SPAWNED + 1] = request.name
    return { ok = true, lord = #SPAWNED }
end
old.lord_relations = function() return { ok = true } end
old.lord_take_region = function(request)
    TAKEN = (TAKEN or {})
    TAKEN[#TAKEN + 1] = request.lord .. ":" .. request.region
    return { ok = true }
end
WARS = {}
old.lord_declare_war = function(request) WARS[#WARS + 1] = "war:" .. request.lord; return { ok = true } end
old.lord_declare_peace = function(request) WARS[#WARS + 1] = "peace:" .. request.lord; return { ok = true } end
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
        self.ruins = {}        # region name -> set of building indexes that are rubble
        self.deposits = []     # (region, building index, good id, amount)
        self.old_types = {}    # (region name, building index) -> typeBeforeChange of a ruin (default 3)
        self.setups = []       # (region, building index, bType, constructed, hp) at each SetupBuilding call
        self.sites = set()     # (region, building index) of construction sites made by SetupBuilding
        self.game.exec("package.loaded['HarnessSack'] = { MAX_GOODS_REMOVED = 5000, remove_goods = function(region, kind, amount) WOOD_REMOVED = (WOOD_REMOVED or {}); WOOD_REMOVED[#WOOD_REMOVED + 1] = kind; return 7 end }")
        self.families = {}     # region name -> list of families (each a list of member objects)
        self.region_by_name = {}
        self.game.exec(LORD_STUB)
        self.game.method(self.pawn, "GetAddress", lambda _self: 1)
        self.home = self.make_region("Home", True, 12)
        self.regions = [self.home]
        self.engine.regions = self.game.array(self.regions)
        self.game.advance(8)

    def make_building(self, name, index):
        building = self.game.obj("Building")
        self.game.method(building, "IsRubble", lambda _self: index in self.ruins[name])
        self.game.method(building, "collapseBuilding", lambda _self: self.ruins[name].add(index))
        self.game.method(building, "addToInventory", lambda _self, item: self.deposits.append((name, index, item.Type, item.amt)))
        building.typeBeforeChange = self.old_types.get((name, index), 3) if index in self.ruins[name] else 0
        building.Data = self.game.obj("BuildingData", bType=75 if index in self.ruins[name] else 3, constructed=(name, index) not in self.sites, hp=100, other=5)

        def set_up(own):
            data = own.Data
            self.setups.append((name, index, data.bType, data.constructed, data.hp))
            self.ruins[name].discard(index)
            self.sites.add((name, index))
        self.game.method(building, "SetupBuilding", set_up)
        return building

    def make_region(self, name, settled, buildings):
        region = self.game.obj("Region", ownerPawn=self.pawn, isSettled=settled)
        self.game.method(region, "GetFName", lambda _self, name=name: self.game.text(name))
        self.counts[name] = buildings
        self.ruins[name] = set()
        self.families[name] = []
        self.region_by_name[name] = region
        self.game.method(region, "GetBuildings", lambda _self, name=name: self.game.array([self.make_building(name, i) for i in range(self.counts[name])]))
        self.game.method(region, "getTotalNumFamilies", lambda _self, name=name: sum(1 for family in self.families[name] if any(not member.dead for member in family)))
        return region

    def add_families(self, name, count, members=2):
        """Give a region `count` families of `members` living people. just_die marks a member dead."""
        for _ in range(count):
            people = []
            for _ in range(members):
                person = self.game.obj("SMUnit", dead=False)
                self.game.method(person, "just_die", lambda unit: setattr(unit, "dead", True))
                people.append(person)
            self.families[name].append(people)
        family_objects = [self.game.obj("Family", familyMembers=self.game.array(people, wrap=False)) for people in self.families[name]]
        self.region_by_name[name].workerFamilies = self.game.array(family_objects, wrap=False)

    def lord_owns(self, name):
        """The real handover gives the region to the lord pawn. The fake handover does not, so the test does it."""
        lord = self.game.obj("PawnCPP_AI", lordsName="Aldric", enemies=self.game.array([]))
        self.game.method(lord, "GetFName", lambda _self: self.game.text("LordObj"))
        self.game.method(lord, "GetAddress", lambda _self: 2)
        self.region_by_name[name].ownerPawn = lord
        self.game.exec("package.loaded['features.vassals.world'].lord_status = function() return { number = 1, object = 'LordObj', enemy_of_player = false, tags = {} } end")
        return lord

    def living(self, name):
        return sum(1 for family in self.families[name] for member in family if not member.dead)

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


class PolicyTests(HandoverBase):
    def setUp(self):
        super().setUp()
        self.hand_over_and_wait()
        self.pawn.silver = 200

    def row(self):
        return self.state()["vassals"][0]

    def test_the_default_policy_is_fair(self):
        self.assertEqual(self.row()["policy"], "fair")

    def test_a_policy_change_does_not_change_the_row_apart_from_the_policy(self):
        before = dict(self.row())
        self.assertTrue(self.ask("vassals_set_policy", slot=1, policy="heavy")["ok"])
        before["policy"] = "heavy"
        self.assertEqual(self.row(), before)

    def test_unknown_policy_and_empty_slot_are_refused(self):
        self.assertFalse(self.ask("vassals_set_policy", slot=1, policy="harsh")["ok"])
        self.assertFalse(self.ask("vassals_set_policy", slot=2, policy="heavy")["ok"])

    def test_the_policy_is_kept_in_the_pawn_tags(self):
        self.ask("vassals_set_policy", slot=1, policy="light")
        self.assertIn("invasion:vassal1_policy=light", self.tags())

class LossTests(HandoverBase):
    def setUp(self):
        super().setUp()
        self.taker = self.game.obj("PawnCPP_AI", lordsName="Hussite", enemies=self.game.array([]))
        self.game.method(self.taker, "GetFullName", lambda _self: "PawnCPP_AI /Game/Taker")
        self.hand_over_and_wait()
        self.game.exec("package.loaded['HarnessLords'].lord_declare_peace = function() return { ok = true } end")

    def row(self):
        return self.state()["vassals"][0]

    def test_the_lose_command_frees_the_slot_and_leaves_the_land_to_its_lord(self):
        answer = self.ask("vassals_lose", slot=1)
        self.assertTrue(answer["ok"], answer)
        result = answer["result"]
        self.assertEqual((result["count"], result["lost"]), (0, 1))
        self.assertEqual((result["event"]["reason"], result["event"]["slot"], result["event"]["region"]), ("command", 1, "Eichenhau"))
        self.assertEqual(self.game.exec("return TAKEN and #TAKEN or 0"), 0)  # no other lord is given the land

    def test_the_removed_loss_commands_are_gone(self):
        self.assertFalse(self.ask("vassals_set_loss_region", mode="forget")["ok"])
        self.assertFalse(self.ask("fallback_state")["ok"])
        self.assertFalse(self.ask("fallback_move", slot=1)["ok"])

    def test_an_empty_slot_cannot_be_lost(self):
        self.assertFalse(self.ask("vassals_lose", slot=2)["ok"])

    def test_the_freed_slot_is_used_again(self):
        self.regions[1].ownerPawn = None
        self.ask("vassals_lose", slot=1)
        self.add_region("Goldhof", True, 4)
        self.game.advance(10)
        self.assertEqual(self.row()["region"], "Goldhof")

    def test_a_region_that_another_pawn_owns_is_detected_as_taken(self):
        lord = self.game.obj("PawnCPP_AI", lordsName="Aldric", enemies=self.game.array([]))
        self.game.method(lord, "GetFName", lambda _self: self.game.text("LordObj"))
        self.game.method(lord, "GetFullName", lambda _self: "PawnCPP_AI /Game/LordObj")
        self.engine.relations = self.game.array([])
        self.game.method(self.engine, "FindAllOf", lambda _self: None)
        taker = self.game.obj("PawnCPP_AI", lordsName="Hussite", enemies=self.game.array([]))
        self.game.method(taker, "GetFName", lambda _self: self.game.text("Taker"))
        self.regions[1].ownerPawn = taker
        self.game.advance(10)
        state = self.state()
        self.assertEqual(state["lost"], 1)
        self.assertEqual(state["lost_events"][0]["reason"], "taken")


NO_COLLAPSE = "package.loaded['features.vassals.world'].collapse_buildings = function() return 0 end"


class SackWipeTests(HandoverBase):
    """The sack of a vassal region (change add-vassal-sack-wipe): 80 percent ruins, then the wipe."""
    BUILDINGS = 20

    def setUp(self):
        super().setUp()
        self.hand_over_and_wait("Eichenhau", self.BUILDINGS)
        self.lord_owns("Eichenhau")
        self.add_families("Eichenhau", 5)
        self.game.exec("package.loaded['HarnessLords'].lord_declare_peace = function() return { ok = true } end")

    def sack(self, wait=40):
        answer = self.ask("vassals_sack", slot=1)
        if answer["ok"]:
            self.game.advance(wait)  # the wipe takes three polls after the collapses
            answer["result"] = self.state()
        return answer

    def test_a_sack_of_20_buildings_collapses_16_and_wipes_the_region(self):
        answer = self.sack()
        self.assertTrue(answer["ok"], answer)
        self.assertEqual(len(self.ruins["Eichenhau"]), 16)
        result = answer["result"]
        self.assertEqual((result["count"], result["lost"]), (0, 1))
        self.assertEqual(result["lost_events"][0]["reason"], "wiped")
        self.assertEqual(result["lost_events"][0]["families"], 5)
        self.assertEqual(self.living("Eichenhau"), 0)
        self.assertEqual([row["region"] for row in result["wiped"]], ["Eichenhau"])
        self.assertEqual(result["wiped"][0]["buildings"], 20)

    def test_the_slot_is_free_and_the_wiped_record_is_not_a_slot(self):
        self.sack()
        tags = self.tags()
        self.assertFalse(any(tag.startswith("invasion:vassal1_region=Eichenhau") for tag in tags))
        self.assertIn("invasion:wiped1_region=Eichenhau", tags)

    def test_the_sack_is_not_complete_at_15_ruins(self):
        self.game.exec(NO_COLLAPSE)
        for index in range(15):
            self.ruins["Eichenhau"].add(index)
        answer = self.sack(10)
        self.assertTrue(answer["ok"], answer)
        result = answer["result"]
        self.assertEqual(result["lost"], 0)
        self.assertEqual(self.living("Eichenhau"), 10)
        self.assertEqual(result["wiped"], [])
        self.assertIn("1", result["sacks"])

    def test_the_sack_goes_on_each_poll_until_the_ruins_are_enough(self):
        self.game.exec(NO_COLLAPSE)
        for index in range(15):
            self.ruins["Eichenhau"].add(index)
        self.sack(10)
        self.ruins["Eichenhau"].add(15)
        self.game.advance(40)
        self.assertEqual(self.state()["lost_events"][0]["reason"], "wiped")

    def test_a_sack_that_makes_no_progress_gives_up_and_reports(self):
        self.game.exec(NO_COLLAPSE)
        self.sack()
        self.game.advance(80)
        state = self.state()
        self.assertEqual(state["lost"], 0)
        self.assertFalse(state["sacks"])
        self.assertIn("gave up", state["sack_errors"]["1"])

    def test_the_sack_changes_no_owner_and_gives_no_other_order(self):

        self.sack()
        self.assertEqual(self.regions[1].ownerPawn.lordsName, "Aldric")
        self.assertEqual(self.game.exec("return TAKEN and #TAKEN or 0"), 0)

    def test_the_sack_of_an_empty_slot_or_twice_is_refused(self):
        self.assertFalse(self.ask("vassals_sack", slot=2)["ok"])
        self.game.exec(NO_COLLAPSE)
        self.assertTrue(self.sack(10)["ok"])
        self.assertFalse(self.sack(10)["ok"])

    def test_only_the_standing_buildings_are_collapsed(self):
        for index in range(4):
            self.ruins["Eichenhau"].add(index)
        self.sack()
        self.assertEqual(len(self.ruins["Eichenhau"]), 16)

    def test_a_region_without_buildings_is_wiped_at_once(self):
        self.game.exec("package.loaded['features.vassals.world'].census = function() return { total = 0, standing = 0, rubble = 0 } end")
        answer = self.sack()
        self.assertTrue(answer["ok"], answer)
        self.assertEqual(answer["result"]["lost_events"][0]["reason"], "wiped")

    def test_adopt_registers_a_region_that_an_ai_lord_owns(self):
        self.add_region("Goldhof", True, 6)
        self.game.exec("package.loaded['features.vassals.world'].region_lord_name = function(name) return name == 'Goldhof' and 'Endlein' or nil end")
        answer = self.ask("vassals_adopt", region="Goldhof")
        self.assertTrue(answer["ok"], answer)
        rows = {row["region"]: row for row in answer["result"]["vassals"]}
        self.assertEqual(rows["Goldhof"]["lord"], "Endlein")
        self.assertFalse(self.ask("vassals_adopt", region="Goldhof")["ok"])
        self.assertFalse(self.ask("vassals_adopt", region="Home")["ok"])

    def test_the_share_counts_against_the_buildings_that_are_still_there(self):
        self.game.exec(NO_COLLAPSE)
        for index in range(15):
            self.ruins["Eichenhau"].add(index)
        self.counts["Eichenhau"] = 19   # the AI demolished one ruin: 15 of 19 is 79 percent, so 16 are still needed
        self.sack(10)
        self.assertEqual(self.state()["lost"], 0)
        self.ruins["Eichenhau"].add(15)
        self.counts["Eichenhau"] = 19   # 16 ruins; 16 of 19 is complete
        self.game.advance(40)
        self.assertEqual(self.state()["lost_events"][0]["reason"], "wiped")

    def test_the_sack_start_removes_the_logs_and_planks(self):
        self.game.exec(NO_COLLAPSE)
        self.sack()
        self.assertEqual(self.game.exec("return table.concat(WOOD_REMOVED, ',')"), "16,17")

    def test_a_sack_that_gives_up_gives_wood_and_orders_the_rebuild_of_each_ruin(self):
        self.game.exec(NO_COLLAPSE)
        for index in (0, 1, 2):
            self.ruins["Eichenhau"].add(index)
        self.old_types[("Eichenhau", 1)] = 75   # skipped
        self.old_types[("Eichenhau", 2)] = 0    # skipped
        self.sack()
        self.game.advance(80)
        goods = {(good, amount) for _, _, good, amount in self.deposits}
        self.assertEqual(goods, {(16, 50), (17, 100)})
        self.assertIn(("Eichenhau", 0, 3, False, 0), self.setups)
        self.assertEqual(len(self.setups), 1)
        self.assertEqual(self.state()["lost"], 0)

    def test_the_wipe_takes_three_polls_and_keeps_one_family_in_the_first(self):
        self.game.exec(NO_COLLAPSE)
        self.game.exec("""local w = package.loaded['features.vassals.world']; local old = w.delete_villagers; DELETES = {}
            w.delete_villagers = function(name, keep) DELETES[#DELETES + 1] = tostring(keep) .. ':' .. tostring(w.region_families(name)); return old(name, keep) end""")
        for index in range(16):
            self.ruins["Eichenhau"].add(index)
        self.ask("vassals_sack", slot=1)
        self.game.advance(60)
        state = self.state()
        self.assertEqual(self.game.exec("return table.concat(DELETES, ',')"), "1:5,nil:1")   # 4 families first, the last one a poll later
        self.assertEqual((self.living("Eichenhau"), state["lost"]), (0, 1))
        self.assertEqual(state["lost_events"][0]["people_deleted"], 10)

    def test_the_raid_end_ends_a_sack_that_is_not_in_its_wipe(self):
        self.game.exec(NO_COLLAPSE)
        for index in range(3):
            self.ruins["Eichenhau"].add(index)
        self.sack(10)
        self.game.exec("require('features.tribute.init').on_raid_end({ id = 1, target = 'Eichenhau' })")
        self.assertEqual({(good, amount) for _, _, good, amount in self.deposits}, {(16, 50), (17, 100)})
        self.assertEqual(len(self.setups), 3)
        self.assertFalse(self.state()["sacks"])
        self.game.exec("require('features.tribute.init').on_raid_end({ id = 2, target = 'Eichenhau' })")   # no running sack: no second order
        self.assertEqual(len(self.setups), 3)

    def test_the_raid_end_does_not_stop_a_wipe_that_has_started(self):
        for index in range(16):
            self.ruins["Eichenhau"].add(index)
        self.game.exec(NO_COLLAPSE)
        self.ask("vassals_sack", slot=1)
        self.game.advance(1)
        self.game.exec("require('features.tribute.init').on_raid_end({ id = 1, target = 'Eichenhau' })")
        self.assertEqual(self.deposits, [])
        self.game.advance(60)
        self.assertEqual(self.state()["lost_events"][0]["reason"], "wiped")

    def test_the_end_sack_command_gives_wood_and_orders_the_rebuild(self):
        self.game.exec(NO_COLLAPSE)
        for index in range(3):
            self.ruins["Eichenhau"].add(index)
        self.sack(10)
        answer = self.ask("vassals_end_sack", slot=1)
        self.assertTrue(answer["ok"], answer)
        self.assertEqual(answer["result"]["ended"]["rebuild"], {"ordered": 3, "skipped": 0, "failed": 0})
        self.assertFalse(self.ask("vassals_end_sack", slot=1)["ok"])

    def test_the_rebuild_command_skips_type_0_and_75(self):
        for index in range(4):
            self.ruins["Eichenhau"].add(index)
        self.old_types[("Eichenhau", 0)] = 0
        self.old_types[("Eichenhau", 3)] = 75
        answer = self.ask("vassals_rebuild_ruins", region="Eichenhau")
        self.assertEqual(answer["result"], {"ordered": 2, "skipped": 2, "failed": 0})
        self.assertEqual({index for _, index, *_ in self.setups}, {1, 2})

    def test_the_ruin_rules(self):
        values = self.game.exec(
            "local r = require('features.vassals.rules'); return r.ruins_needed(20, 0.8), r.ruins_needed(5, 0.8), r.ruins_needed(0, 0.8), "
            "r.sack_complete(20, 16, 0.8) and 1 or 0, r.sack_complete(20, 15, 0.8) and 1 or 0, r.houses_to_collapse(16, 4), r.houses_to_collapse(16, 20), r.rebuilt_target(20, 0.5), r.rebuilt_target(0, 0.5)")
        self.assertEqual(tuple(values.values()) if hasattr(values, "values") else tuple(values), (16, 4, 0, 1, 0, 12, 0, 10, 1))


RESTORE_STUB = """
SETTLES = {}
local core = require("ManorCore")
core.settle_region = function(request, pawn)
    SETTLES[#SETTLES + 1] = request.region .. ":" .. tostring(pawn ~= nil)
    if SETTLE_FAILS then return { ok = false, error = "settle failed" } end
    return { ok = true, after = { families = 5 } }
end
"""


class RestoreTests(HandoverBase):
    def setUp(self):
        super().setUp()
        self.game.exec(RESTORE_STUB)
        self.hand_over_and_wait("Eichenhau", 10)
        self.lord_owns("Eichenhau")
        self.add_families("Eichenhau", 4)
        self.game.exec("package.loaded['HarnessLords'].lord_declare_peace = function() return { ok = true } end")
        self.ask("vassals_sack", slot=1)
        self.game.advance(40)
        self.pawn.silver = 500
        self.game.exec("SETTLES = {}")  # the refugee wave of the wipe settled the home region

    def restore(self, **args):
        return self.ask("vassals_restore", **args)

    def test_a_restore_takes_100_silver_raises_the_villagers_and_spawns_the_goods(self):
        answer = self.restore(region="Eichenhau")
        self.assertTrue(answer["ok"], answer)
        result = answer["result"]
        self.assertEqual(self.pawn.silver, 400)
        self.assertEqual(self.game.exec("return SETTLES[1]"), "Eichenhau:true")
        self.assertEqual(result["restored"]["goods"], {"logs": 100, "planks": 200, "rubble_stone": 100})
        goods = {(good, amount) for _, _, good, amount in self.deposits}
        self.assertEqual(goods, {(16, 100), (17, 200), (15, 100)})
        self.assertEqual(result["wiped"], [])

    def test_a_restore_gives_the_region_to_the_lord_and_orders_the_rebuild(self):
        for index in range(8):
            self.ruins["Eichenhau"].add(index)
        self.game.exec("RECEIVED = {}")
        result = self.restore()["result"]
        self.assertEqual(self.game.exec("return RECEIVED[1]"), "1:Eichenhau")
        self.assertEqual(result["restored"]["rebuild"]["ordered"], 8)
        self.assertEqual(len(self.setups), 8)
        self.assertEqual(self.game.exec("return SETTLES[1]"), "Eichenhau:true")

    def test_the_restored_vassal_gets_a_slot_again_and_the_tribute_waits_for_the_rebuild(self):
        result = self.restore()["result"]
        row = result["vassals"][0]
        self.assertEqual((result["count"], row["region"], row["lord"], row["rebuilding"]), (1, "Eichenhau", "Aldric", True))
        self.assertIn("invasion:vassal1_rebuilding=true", self.tags())

    def test_the_rebuilding_flag_ends_when_enough_buildings_stand(self):
        self.restore()
        self.assertTrue(self.state()["vassals"][0]["rebuilding"])
        self.game.advance(10)
        self.assertTrue(self.state()["vassals"][0]["rebuilding"])   # the ordered ruins are sites, not built
        self.sites.clear()
        self.game.advance(10)
        self.assertFalse(self.state()["vassals"][0]["rebuilding"])

    def test_a_construction_site_does_not_end_the_rebuilding_flag(self):
        self.restore()
        self.game.exec("package.loaded['features.vassals.world'].census = function() return { total = 10, standing = 10, built = 1, rubble = 0 } end")
        self.game.advance(10)
        self.assertTrue(self.state()["vassals"][0]["rebuilding"])

    def test_a_restore_with_too_little_silver_is_refused_and_takes_nothing(self):
        self.pawn.silver = 99
        answer = self.restore()
        self.assertFalse(answer["ok"])
        self.assertIn("silver", answer["error"])
        self.assertEqual(self.pawn.silver, 99)
        self.assertEqual(len(self.state()["wiped"]), 1)
        self.assertEqual(self.game.exec("return #SETTLES"), 0)
        self.assertEqual(self.deposits, [])

    def test_a_region_that_is_not_wiped_is_refused(self):
        answer = self.restore(region="Goldhof")
        self.assertFalse(answer["ok"])
        self.assertIn("no wiped region", answer["error"])
        self.assertEqual(self.pawn.silver, 500)

    def test_a_second_restore_finds_no_wiped_region(self):
        self.restore()
        answer = self.restore()
        self.assertFalse(answer["ok"])
        self.assertEqual(self.pawn.silver, 400)

    def test_a_failed_raise_of_the_villagers_takes_no_silver(self):
        self.game.exec("SETTLE_FAILS = true")
        answer = self.restore()
        self.assertFalse(answer["ok"])
        self.assertEqual(self.pawn.silver, 500)
        self.assertEqual(self.deposits, [])
        self.assertEqual(len(self.state()["wiped"]), 1)

    def test_the_restore_rules(self):
        values = self.game.exec(
            "local r = require('features.vassals.rules'); return r.restore_refusal(nil, 1, 500, 100), r.restore_refusal(1, nil, 500, 100), r.restore_refusal(1, 1, 99, 100), r.restore_refusal(1, 1, 100, 100) or 'ok', "
            "r.find_wiped({ 'none', 'B' }, 2, nil), r.find_wiped({ 'A', 'B' }, 2, 'B'), r.find_wiped({ 'A' }, 2, 'C') or 0")
        self.assertEqual(tuple(values.values()) if hasattr(values, "values") else tuple(values), ("no wiped region to restore", "all vassal slots are used", "silver 99 is below the restore cost 100", "ok", 2, 2, 0))


if __name__ == "__main__":
    unittest.main()
