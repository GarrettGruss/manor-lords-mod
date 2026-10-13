"""Mock tests for HarnessBandits (spec 15): negotiate with the bandit faction so that raiders settle.

The fake world copies what the real game showed (implementation-notes/bandit-settlement.md):
  - the letter paragraph `raider_suggestSettle+<silver>` is sent with PawnCPP:sendLetter(banditPawn, names);
  - it only works when the relation between the player and the bandit lord has the tag "attacking";
  - the silver is taken from the player, and the bandit units lose their squad (the real game then deletes them after some seconds);
  - the number of families of the player does not change.
It tests the Lua module logic. It does NOT prove how the real game decides.
"""

import json
import unittest

import fakegame_path  # noqa: F401
from fakegame import FakeGame

BUILD_WORLD = """
function(fg)
    local world = { letters = {}, cheat_calls = 0 }
    local region = fg.object("Region", { regionName = "Riesenbuckel" })
    fg.set_method(region, "getTotalNumFamilies", function() return 10 end)
    fg.set_method(region, "getNumHomelessFamilies", function() return 0 end)
    fg.set_method(region, "getAvailableLivingSpace", function() return { constructed = 4, unconstructed = 0 } end)

    local player = fg.object("MyPawnCPP_BP3_C", { isMainPlayer = true, silver = 100, influence = 660,
                                                   outbox = fg.array({}, { wrap = false }), quests = fg.array({}, { wrap = false }) })
    region.ownerPawn = player
    local bandit = fg.object("PawnCPP", { isBandit = true, isAI = true, silver = 0, commandedSquads = fg.array({ { Value = 5 } }, { wrap = false }),
                                          InBox = fg.array({}, { wrap = false }), quests = fg.array({}, { wrap = false }) })
    fg.finders["PawnCPP_AI"] = function() return bandit end

    local units = {}
    for index = 1, 4 do
        units[index] = fg.object("SMUnit", { dead = false, assignedSquadID = { Value = 5 }, currentUnitRole = 5, ItemsLooted = 0,
                                             morale = 1.0, combatExperience = 0.0, realPos = { X = 10.0 * index, Y = 2.0, Z = 3.0 } })
    end

    local entry = { pawnA = player, pawnB = bandit, Tags = fg.array({ "at_war" }, { wrap = false }), friendship = 0.0, status = 0 }
    local relations = fg.array({ entry }, { wrap = false })
    local engine = fg.object("RTSMultiEngineCPP", { playerRef = player, relations = relations })
    fg.set_method(engine, "addRelationTag", function(self, a, b, tag) fg.array_add(entry.Tags, tag.fname) return true end)
    fg.set_method(player, "changeRelationTags", function(self, other, add, remove)
        local kept = {}
        for i = 1, entry.Tags:GetArrayNum() do
            local keep = true
            for _, gone in ipairs(remove) do if entry.Tags[i] == gone.fname then keep = false end end
            if keep then kept[#kept + 1] = entry.Tags[i] end
        end
        entry.Tags = fg.array(kept, { wrap = false })
    end)

    local function has_tag(name)
        for i = 1, entry.Tags:GetArrayNum() do if entry.Tags[i] == name then return true end end
        return false
    end
    local function settle()
        for _, unit in ipairs(units) do unit.assignedSquadID = { Value = 0 } end
    end
    fg.set_method(player, "sendLetter", function(self, recipient, names)
        world.letters[#world.letters + 1] = names[1].fname
        local amount = tonumber(names[1].fname:match("^raider_suggestSettle%+(%d+)$"))
        if amount and has_tag("attacking") then
            self.silver = self.silver - math.min(amount, self.silver)
            settle()
        end
    end)
    local cheat = fg.object("MLCheatManager", {})
    fg.set_method(cheat, "SettleRaiders", function() world.cheat_calls = world.cheat_calls + 1 settle() end)
    world.player, world.units = player, units
    return world
end
"""


class BanditTestCase(unittest.TestCase):
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


class StateTests(BanditTestCase):
    def test_state_shows_families_units_silver_and_tags(self):
        state = self.send("bandit_state")
        self.assertTrue(state["ok"], state)
        self.assertEqual((state["families"], state["bandit_units"], state["silver"], state["influence"]), (10, 4, 100, 660))
        self.assertEqual(state["relation"]["tags"], ["at_war"])
        self.assertEqual(state["regions"][0]["vacant_slots"], 4)


class TagTests(BanditTestCase):
    def test_a_tag_is_added_and_removed(self):
        added = self.send("bandit_tag", tag="attacking")
        self.assertEqual((added["ok"], added["after"]["tags"]), (True, ["at_war", "attacking"]))
        removed = self.send("bandit_tag", tag="attacking", remove=1)
        self.assertEqual((removed["ok"], removed["after"]["tags"]), (True, ["at_war"]))

    def test_a_tag_outside_the_list_is_refused(self):
        self.assertIn("tag must be", self.send("bandit_tag", tag="peace_treaty")["error"])
        self.assertIn("tag must be", self.send("bandit_tag")["error"])


class LetterTests(BanditTestCase):
    def test_the_settle_letter_costs_silver_and_clears_the_bandit_units(self):
        self.send("bandit_tag", tag="attacking")
        answer = self.send("bandit_letter", paragraphs=["raider_suggestSettle+30"])
        self.assertTrue(answer["ok"], answer)
        self.assertEqual((answer["before"]["silver"], answer["after"]["silver"]), (100, 70))
        self.assertEqual((answer["before"]["bandit_units"], answer["after"]["bandit_units"]), (4, 0))
        self.assertEqual((answer["before"]["families"], answer["after"]["families"]), (10, 10))
        self.assertEqual(list(self.world.letters.values()), ["raider_suggestSettle+30"])

    def test_without_the_attacking_tag_nothing_changes(self):
        answer = self.send("bandit_letter", paragraphs=["raider_suggestSettle+30"])
        self.assertTrue(answer["ok"], answer)
        self.assertEqual((answer["after"]["silver"], answer["after"]["bandit_units"]), (100, 4))

    def test_bad_paragraphs_are_refused(self):
        for names in (["welcome_positive"], ["raider_suggestSettle+x"], ["raider_suggestSettle+1234567"], []):
            self.assertFalse(self.send("bandit_letter", paragraphs=names)["ok"], names)
        self.assertEqual(len(self.world.letters), 0)


class CheatTests(BanditTestCase):
    def test_settle_raiders_calls_the_cheat_and_reports_before_and_after(self):
        answer = self.send("settle_raiders")
        self.assertTrue(answer["ok"], answer)
        self.assertEqual((answer["before"]["bandit_units"], answer["after"]["bandit_units"], self.world.cheat_calls), (4, 0, 1))


class TrackTests(BanditTestCase):
    def test_marked_units_are_followed(self):
        self.assertEqual(self.send("bandit_mark")["marked"], 4)
        self.assertEqual(self.send("bandit_track")["counts"]["in_squad"], 4)
        self.send("settle_raiders")
        counts = self.send("bandit_track")["counts"]
        self.assertEqual((counts["no_squad"], counts["in_squad"]), (4, 0))


if __name__ == "__main__":
    unittest.main()
