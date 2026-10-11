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

    local home = fg.object("BP_Region_C", { regionName = "Wilde Wand" }, "/Game/Fake/Eichenhau")
    local player = fg.object("MyPawnCPP_BP3_C", { isMainPlayer = true, currentRegion = home, enemies = fg.array({}, { wrap = false }) })
    fg.set_method(player, "K2_GetActorLocation", function() return { X = 0.0, Y = 0.0, Z = 0.0 } end)

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
        fg.set_method(pawn, "layClaim", function(self, region) fg.array_add(self.claims, { Region = region, DaysLeft = 5 }) end)
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
    fg.set_method(engine, "spawnNewAILord", function(self, name) return lord(name, {}) end)
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


if __name__ == "__main__":
    unittest.main()
