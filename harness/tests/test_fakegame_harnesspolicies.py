"""Mock tests for HarnessPolicies (spec 16): policy state, enact and sign, in the fake game kit.

The fake world follows the jmap (names and types only; the real behavior is in implementation-notes/policies.md):
`Region.policies` is an array of Policy structs (one per slot), `Region.policiesSigned` an int array,
`Region:getAllAvailablePolicies()` and `getMaxPolicies()` are Region calls, and `PawnCPP:enactPolicy(region, slot, id)` returns a bool.
"""

import json
import unittest

import fakegame_path  # noqa: F401
import runlib_path  # noqa: F401
from fakegame import FakeGame
from modstate_support import sleep_in
from runlib.actions import Actions, ActionError
from runlib.commands import CommandChannel, CommandRefused
from runlib.expectations import Expectations

WORLD = """
function(fg)
    local world = { slots = 2, enact_calls = 0 }
    local player = fg.object("PawnCPP", { silver = 500, influence = 40, availablePolicies = fg.array({ 3, 12 }, { wrap = false }) },
                             "/Game/Fake/Player")
    fg.set_method(player, "GetAddress", function() return 1 end)
    local factor = { Type = 21, day = 3, expirationDay = 9, count = 1, past = false, effectByPopulation = -2.5 }
    local region = fg.object("Region", { ownerPawn = player, Approval = 62, settlementLevel = 1, regionalWealth = 120,
                                          summedApprovalFactors = fg.array({ factor }, { wrap = false }) })
    world.region = region
    region.policies = fg.array({ { ID = 0, tier = 0, Name = fg.fstring("") }, { ID = 0, tier = 0, Name = fg.fstring("") } }, { wrap = false })
    region.policiesSigned = fg.array({}, { wrap = false })
    fg.set_method(region, "getMaxPolicies", function() return world.slots end)
    fg.set_method(region, "getAllAvailablePolicies", function() return fg.array({ 3, 12 }, { wrap = false }) end)
    fg.set_method(region, "getPredictedApprovalLossFromTaxes", function() return 2 end)
    fg.set_method(region, "getNumDevPointsSpent", function() return 0 end)
    fg.set_method(region, "getNumTotalPopulation", function() return 30 end)
    local function sign(id, signed)
        local items = {}
        for i = 1, #region.policiesSigned do items[#items + 1] = region.policiesSigned[i] end
        if signed then
            items[#items + 1] = id
        else
            for i = #items, 1, -1 do if items[i] == id then table.remove(items, i) end end
        end
        region.policiesSigned = fg.array(items, { wrap = false })
    end
    fg.set_method(region, "setPolicySigned", function(self, id, signed) sign(id, signed) end)
    fg.set_method(player, "enactPolicy", function(self, target, slot, id)
        world.enact_calls = world.enact_calls + 1
        if slot < 0 or slot >= world.slots then return false end
        sign(id, true)
        target.policies[slot + 1].ID = id
        target.policies[slot + 1].Name = fg.fstring("Policy " .. id)
        target.Approval = target.Approval - 5
        return true
    end)
    fg.object("RTSMultiEngineCPP", { playerRef = player, regions = fg.array({ region }, { wrap = false }) })
    return world
end
"""


def start():
    game = FakeGame()
    game.start()
    world = game.lua.eval(WORLD)(game.fg)
    game.load_mod("HarnessActions")
    game.advance(1)
    return game, world


def run_command(game, command, **fields):
    folder = game.run_dir / "commands"
    folder.mkdir(exist_ok=True)
    number = len(list(folder.glob("*.json"))) // 2 + 1
    (folder / f"{number:04d}.json").write_text(json.dumps({"id": f"{number:04d}", "command": command, **fields}), encoding="utf-8")
    game.advance(1)
    return json.loads((folder / f"{number:04d}.result.json").read_text(encoding="utf-8"))


class PolicyTestCase(unittest.TestCase):
    def setUp(self):
        self.game, self.world = start()
        self.addCleanup(self.game.close)

    def send(self, command, **fields):
        return run_command(self.game, command, **fields)


class StateTests(PolicyTestCase):
    def test_state_reads_slots_available_ids_approval_and_resources(self):
        answer = self.send("policy_state")
        self.assertTrue(answer["ok"], answer)
        self.assertEqual((answer["max_policies"], answer["available"], answer["pawn_available"]), (2, [3, 12], [3, 12]))
        self.assertEqual((answer["approval"], answer["silver"], answer["influence"]), (62, 500, 40))
        self.assertEqual([row["slot"] for row in answer["policies"]], [0, 1])
        self.assertEqual(answer["signed"], [])
        factor = answer["approval_factors"][0]
        self.assertEqual((factor["name"], factor["expiration_day"], factor["effect_by_population"]), ("hardship", 9, -2.5))

    def test_state_does_not_change_the_game(self):
        self.send("policy_state")
        self.assertEqual(self.world.enact_calls, 0)


class EnactTests(PolicyTestCase):
    def test_enact_calls_the_game_and_reports_before_and_after(self):
        answer = self.send("policy_enact", policy=12, slot=0)
        self.assertTrue(answer["ok"], answer)
        self.assertEqual((answer["returned"], answer["before"]["approval"], answer["after"]["approval"]), (True, 62, 57))
        self.assertEqual(answer["after"]["policies"][0]["id"], 12)
        self.assertEqual(answer["after"]["signed"], [12])

    def test_a_policy_that_is_not_available_is_refused_without_a_call(self):
        self.assertIn("not in the available list", self.send("policy_enact", policy=7, slot=0)["error"])
        self.assertEqual(self.world.enact_calls, 0)

    def test_a_slot_outside_the_count_is_refused_without_a_call(self):
        self.assertIn("slot must be", self.send("policy_enact", policy=12, slot=2)["error"])
        self.assertEqual(self.world.enact_calls, 0)

    def test_bad_inputs_are_refused(self):
        self.assertIn("policy must be", self.send("policy_enact", slot=0)["error"])
        self.assertIn("policy must be", self.send("policy_enact", policy=99, slot=0)["error"])
        self.assertIn("slot must be", self.send("policy_enact", policy=12)["error"])


class SignTests(PolicyTestCase):
    def test_sign_and_unsign_follow_the_request(self):
        self.send("policy_enact", policy=12, slot=0)
        removed = self.send("policy_sign", policy=12, signed=False)
        self.assertTrue(removed["ok"], removed)
        self.assertEqual((removed["before"]["signed"], removed["after"]["signed"]), ([12], []))
        self.assertEqual(self.send("policy_sign", policy=3, signed=True)["after"]["signed"], [3])

    def test_signed_must_be_a_boolean(self):
        self.assertIn("signed must be", self.send("policy_sign", policy=12)["error"])


class StubBridge:
    def engine_path(self):
        return "engine"


class SweepTests(unittest.TestCase):
    def test_the_sweep_is_refused_without_the_unsafe_variable(self):
        game, world = start()
        self.addCleanup(game.close)
        answer = run_command(game, "policy_enact_sweep")
        self.assertIn("HARNESS_ALLOW_UNSAFE=1", answer["error"])
        self.assertEqual(world["enact_calls"], 0)

    def test_the_sweep_stops_at_the_first_true(self):
        game = FakeGame(env={"HARNESS_ALLOW_UNSAFE": "1"})
        game.start()
        self.addCleanup(game.close)
        world = game.lua.eval(WORLD)(game.fg)
        game.load_mod("HarnessActions")
        game.advance(1)
        answer = run_command(game, "policy_enact_sweep")
        self.assertTrue(answer["ok"], answer)
        self.assertEqual(answer["calls"], 2)
        self.assertEqual(answer["first_true"], {"id": 0, "slot": 0})


class PolicyActionTests(unittest.TestCase):
    def setUp(self):
        self.game, self.world = start()
        self.addCleanup(self.game.close)
        sleep = sleep_in(self.game)
        channel = CommandChannel(self.game.run_dir / "commands", sleep=sleep, monotonic=self.game.now)
        self.actions = Actions(StubBridge(), Expectations(sleep=sleep, monotonic=self.game.now), [], commands=channel)

    def test_the_wrappers_read_enact_and_unsign(self):
        self.assertEqual(self.actions.policy_state()["max_policies"], 2)
        self.assertEqual(self.actions.policy_enact(12, 1)["after"]["policies"][1]["id"], 12)
        self.assertEqual(self.actions.policy_sign(12, False)["after"]["signed"], [])

    def test_the_wrappers_check_their_inputs(self):
        with self.assertRaises(ActionError):
            self.actions.policy_enact(0)
        with self.assertRaises(ActionError):
            self.actions.policy_enact(12, slot=-1)
        with self.assertRaises(ActionError):
            self.actions.policy_sign(12, "no")

    def test_a_refused_command_raises(self):
        with self.assertRaises(CommandRefused):
            self.actions.policy_enact(7, 0)


if __name__ == "__main__":
    unittest.main()
