"""Mock tests for HarnessLords (spec 10, spike S11): read and steer the AI lords through HarnessActions commands.

The fake world copies what the real game showed (implementation-notes/baron-model.md):
  - lords are PawnCPP_AI objects; the relations, challenges and AI logs live on RTSMultiEngineCPP;
  - declareWar adds the tag at_war and the target to `enemies`; initChallenge adds a challenge of 90 days;
  - spawnArmy with a lord as owner adds squads to the lord; spawnNewAILord makes a new PawnCPP_AI;
  - property arrays hand out their elements directly (no :get()), and units move in `realPos`.
It tests the Lua module logic. It does NOT prove how the real AI decides.
"""

import json
import unittest

import fakegame_path  # noqa: F401
from fakegame import FakeGame

BUILD_WORLD = """
function(fg)
    local world = { nextSquad = 20, challengeCalls = 0 }
    local dataTable = fg.object("DataTable", {}, "/Game/NotStronghold/Data/DT_UnitTemplates.DT_UnitTemplates")
    local rows = { spearMilitia = fg.object("UnitTemplateRow", { maxSize = 3 }) }
    fg.set_method(dataTable, "GetRowNames", function() return { "spearMilitia" } end)
    fg.set_method(dataTable, "GetRowStruct", function() return fg.object("ScriptStruct", {}, "/Script/ManorLords.UnitTemplate") end)
    fg.set_method(dataTable, "FindRow", function(self, name) return rows[name] end)

    local home = fg.object("BP_Region_C", { regionName = "Wilde Wand", isSettled = true, settlementType = 1, settlementLevel = 0 },
                           "/Game/Fake/Eichenhau")
    local empty = fg.object("BP_Region_C", { regionName = "Hochweg", isSettled = false, settlementType = 0, settlementLevel = 0 },
                            "/Game/Fake/Goldhof")
    for _, region in ipairs({ home, empty }) do
        fg.set_method(region, "GetBuildings", function() return fg.array({}, { wrap = false }) end)
        fg.set_method(region, "getTotalNumFamilies", function() return 0 end)
    end
    world.empty = empty
    -- Like the real game (S13 part 2): finalizeClaim sets the owner and makes a planning component only for a region without an owner.
    local function claimMethods(pawn)
        fg.set_method(pawn, "layClaim", function(self, region) fg.array_add(self.claims, { Region = region, DaysLeft = 14 }) end)
        fg.set_method(pawn, "finalizeClaim", function(self, region)
            if region.ownerPawn == nil then
                region.ownerPawn = self
                region.CityPlanningComponent = fg.object("CityPlanningComponent", {})
                world.planningMade = world.planningMade + 1
            end
        end)
        fg.set_method(pawn, "settleRegion", function(self, region, camp, supply, kind, outpost)
            world.settled = { camp = camp, supply = supply, kind = kind }
            region.isSettled = true
            region.settlementType = kind
        end)
    end
    world.planningMade = 0
    for _, region in ipairs({ home, empty }) do
        fg.set_method(region, "getSettledRegionCenter", function() return { X = 10.0, Y = 20.0, Z = 30.0 } end)
    end
    local player = fg.object("MyPawnCPP_BP3_C", { isMainPlayer = true, currentRegion = home, enemies = fg.array({}, { wrap = false }),
                                                   claims = fg.array({}, { wrap = false }) })
    fg.set_method(player, "K2_GetActorLocation", function() return { X = 0.0, Y = 0.0, Z = 0.0 } end)
    claimMethods(player)

    local withPlayer
    local lord
    function lord(name, traits, bandit)
        local pawn = fg.object("PawnCPP_AI", { lordsName = name, isBandit = bandit or false, influence = 0, silver = 0,
                                               traits = fg.array(traits, { wrap = false }), enemies = fg.array({}, { wrap = false }),
                                               commandedSquads = fg.array({}, { wrap = false }), claims = fg.array({}, { wrap = false }) })
        fg.set_method(pawn, "declareWar", function(self, target)
            fg.array_add(withPlayer.Tags, "at_war")
            fg.array_add(self.enemies, target)
        end)
        fg.set_method(pawn, "declarePeace", function(self, target) withPlayer.Tags = fg.array({}, { wrap = false }) end)
        fg.set_method(pawn, "startAI", function(self, speed, canBuild) world.startedAt = speed end)
        claimMethods(pawn)
        return pawn
    end
    local baron = lord("Hildebolt von Berenreute", { "off_map_lord", "villain" })
    local outlaws = lord("Outlaws", { "bandit" }, true)
    world.baron, world.player = baron, player

    local relations = fg.array({}, { wrap = false })
    local function relation(a, b, tags)
        local entry = { pawnA = a, pawnB = b, Tags = fg.array(tags, { wrap = false }), friendship = 0.0, status = 0 }
        fg.array_add(relations, entry)
        return entry
    end
    withPlayer = relation(player, baron, {})
    relation(player, outlaws, { "at_war" })
    world.relationWithPlayer = withPlayer

    local challenges = fg.array({}, { wrap = false })
    local engine = fg.object("RTSMultiEngineCPP", {
        playerRef = player, relations = relations, challenges = challenges, openClaims = fg.array({}, { wrap = false }),
        regions = fg.array({ home, empty }, { wrap = false }),
        spawnAIPlayers = false, declareWarInstant = false, AI_canBuild = true,
        debugLog_AI_general = fg.array({ "Hildebolt von Berenreute (2) claimRegions: not enough influence" }, { wrap = false }),
        debugLog_AI_tactics = fg.array({ "Outlaws (1) Tactics_AI: Num commanded armies = 1" }, { wrap = false }),
        debugLog_AI_construction = fg.array({}, { wrap = false }),
    })

    fg.set_method(engine, "initChallenge", function(self, target, by, region)
        world.challengeCalls = world.challengeCalls + 1
        fg.array_add(challenges, { ID = 0, challengedPawn = target, challengedBy = by, DaysLeft = 90, status = 0, contested = false,
                                   inRegardsTo = fg.array({ region }, { wrap = false }) })
    end)
    fg.set_method(engine, "spawnArmy", function(self, position, names, owner)
        local ids = {}
        for _, name in ipairs(names) do
            local id = world.nextSquad
            world.nextSquad = id + 1
            fg.array_add(owner.commandedSquads, { Value = id })
            for i = 1, rows[name.fname].maxSize do
                local unit = fg.object("SMUnit", { dead = false, assignedSquadID = { Value = id }, currentRegion = home,
                                                   realPos = { X = position.X + i, Y = position.Y, Z = 0.0 } })
                fg.set_method(unit, "getTargetPos", function() return { X = 100.0, Y = 200.0, Z = 0.0 } end)
            end
            ids[#ids + 1] = fg.param({ Value = id })
        end
        return ids
    end)
    fg.set_method(engine, "spawnNewAILord", function(self, name, female, portrait, canBuild)
        world.lastCanBuild = canBuild
        return lord(name, {})
    end)
    fg.set_method(engine, "addPawnRelations", function(self, pawn)
        relation(player, pawn, {})
    end)
    return world
end
"""


class LordsTestCase(unittest.TestCase):
    def setUp(self):
        self.game = FakeGame()
        self.game.start()
        self.addCleanup(self.game.close)
        self.game.exec("FName = function(text) return { fname = text } end")
        self.world = self.game.lua.eval(BUILD_WORLD)(self.game.fg)
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


class StateTests(LordsTestCase):
    def test_state_lists_the_lords_their_traits_and_the_ai_logs(self):
        state = self.send("lords_state", log=5)
        self.assertTrue(state["ok"], state)
        names = [lord["name"] for lord in state["lords"]]
        self.assertEqual(names, ["Hildebolt von Berenreute", "Outlaws"])
        self.assertEqual(state["lords"][0]["traits"], ["off_map_lord", "villain"])
        self.assertEqual(state["lords"][1]["with_player"]["tags"], ["at_war"])
        self.assertIn("not enough influence", state["logs"]["debugLog_AI_general"][0])
        self.assertEqual(state["player_region"], "BP_Region_C_" + state["player_region"].split("_")[-1])

    def test_log_zero_leaves_the_logs_out(self):
        self.assertFalse(self.send("lords_state", log=0)["logs"])  # an empty Lua table becomes [] in JSON


class SteeringTests(LordsTestCase):
    def test_war_adds_the_tag_and_the_enemy(self):
        answer = self.send("lord_declare_war", lord=1, target=0)
        self.assertTrue(answer["ok"], answer)
        self.assertEqual(answer["before"]["tags"], [])
        self.assertEqual(answer["after"]["tags"], ["at_war"])
        self.assertEqual(len(answer["enemies"]), 1)

    def test_influence_is_written_and_bounded(self):
        answer = self.send("lord_set_influence", lord=1, value=2000)
        self.assertEqual((answer["before"], answer["after"]), (0, 2000))
        self.assertFalse(self.send("lord_set_influence", lord=1, value=99999)["ok"])

    def test_a_challenge_names_the_target_region(self):
        answer = self.send("lord_challenge", lord=1, target=0)
        self.assertTrue(answer["ok"], answer)
        self.assertEqual(answer["challenges_before"], 0)
        self.assertEqual(answer["challenges"][0]["days_left"], 90)
        self.assertEqual(len(answer["challenges"][0]["regions"]), 1)

    def test_an_army_belongs_to_the_lord_and_shows_its_position_and_target(self):
        answer = self.send("lord_spawn_army", lord=1, template="spearMilitia", count=2, dx=500, dy=0)
        self.assertTrue(answer["ok"], answer)
        self.assertEqual(answer["squads"], [20, 21])
        squads = self.send("lords_state", log=0)["lords"][0]["squads"]
        self.assertEqual([squad["alive"] for squad in squads], [3, 3])
        self.assertEqual((squads[0]["target_x"], squads[0]["target_y"]), (100, 200))
        self.assertEqual(squads[0]["distance_to_player"], 502)

    def test_a_new_lord_can_be_made_and_started(self):
        answer = self.send("spawn_ai_lord", name="Norse Warlord")
        self.assertEqual((answer["lords_before"], answer["lords_after"], answer["lord"]), (2, 3, 3))
        self.assertTrue(self.send("lord_start_ai", lord=3, value=1)["ok"])
        self.assertEqual(self.world.startedAt, 1)

    def test_bad_input_is_refused(self):
        self.assertIn("no AI lord number 9", self.send("lord_declare_war", lord=9, target=0)["error"])
        self.assertIn("lord must be", self.send("lord_declare_war", target=0)["error"])
        self.assertIn("no pawn for target", self.send("lord_declare_war", lord=1, target=7)["error"])
        self.assertIn("no unit template", self.send("lord_spawn_army", lord=1, template="dragon")["error"])
        self.assertIn("count must be", self.send("lord_spawn_army", lord=1, template="spearMilitia", count=9)["error"])
        self.assertIn("name must be", self.send("spawn_ai_lord")["error"])
        self.assertEqual(self.world.challengeCalls, 0)



class DynamicLordTests(LordsTestCase):
    """Spike S13. The real game crashed on settleRegion for a region without an owner (3 of 3), so the command refuses that."""

    def test_regions_state_lists_owner_and_settled(self):
        rows = {row["region"]: row for row in self.send("regions_state")["regions"]}
        self.assertEqual(set(rows), {"BP_Region_C_" + key.split("_")[-1] for key in rows})
        settled = [row for row in rows.values() if row["settled"]]
        self.assertEqual([row["name"] for row in settled], ["Wilde Wand"])

    def test_a_building_lord_gets_relations_and_a_region(self):
        answer = self.send("spawn_ai_lord", name="Hochweg Lord", build=1)
        self.assertTrue(answer["can_build"])
        self.assertTrue(self.world.lastCanBuild)
        relations = self.send("lord_relations", lord=answer["lord"])
        self.assertEqual(relations["relations_after"], relations["relations_before"] + 1)
        empty = self.send("regions_state")["regions"][1]["region"]
        taken = self.send("lord_take_region", lord=answer["lord"], region=empty)
        self.assertTrue(taken["ok"], taken)
        self.assertEqual(taken["after"]["owner"], answer["object"])

    def test_a_lord_receives_a_region_of_the_player_and_gets_a_new_owner_claim(self):
        lord = self.send("spawn_ai_lord", name="Receiver", build=1)["lord"]
        self.assertTrue(self.send("claim_region", target=0, region=self.empty_name(), finalize=1)["ok"])
        self.assertEqual(self.world.planningMade, 1)
        answer = self.send("lord_receive_region", lord=lord, region=self.empty_name())
        self.assertTrue(answer["ok"], answer)
        self.assertEqual(answer["steps_done"], ["clear owner", "claim"])
        self.assertEqual(self.world.planningMade, 2)
        self.assertIsNotNone(answer["region"]["owner"])
        self.assertNotEqual(answer["region"]["owner"], self.send("regions_state")["regions"][0].get("owner"))

    def test_a_lord_founds_a_village_in_a_free_region_only(self):
        lord = self.send("spawn_ai_lord", name="Founder", build=1)["lord"]
        answer = self.send("lord_found_village", lord=lord, region=self.empty_name(), type=1, supply=2)
        self.assertTrue(answer["ok"], answer)
        self.assertEqual(answer["steps_done"], ["claim", "settle"])
        self.assertTrue(answer["region"]["settled"])
        self.assertEqual((self.world.settled.supply, self.world.settled.kind), (2, 1))
        self.assertEqual((self.world.settled.camp.Translation.X, self.world.settled.camp.Translation.Y), (10, 20))
        again = self.send("lord_found_village", lord=lord, region=self.empty_name())
        self.assertIn("already has an owner", again["error"])

    def test_settle_is_refused_for_a_region_the_pawn_does_not_own(self):
        answer = self.send("settle_region", target=0, region=self.empty_name())
        self.assertIn("does not own", answer["error"])
        self.assertIsNone(getattr(self.world, "settled", None))
        self.send("claim_region", target=0, region=self.empty_name(), finalize=1)
        self.assertIn("type must be", self.send("settle_region", target=0, region=self.empty_name(), type=9)["error"])

    def empty_name(self):
        return self.send("regions_state")["regions"][1]["region"]

    def test_an_unknown_region_is_refused(self):
        self.assertIn("no region named", self.send("lord_take_region", lord=1, region="Nowhere")["error"])


if __name__ == "__main__":
    unittest.main()
