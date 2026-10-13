"""Mock tests for the mod RefugeeWaves (spec 15, issue #51): trigger, wave start, end, and the bad outcome.

The fake world follows the facts of implementation-notes/refugee-followups.md:
  - settleRegion adds 5 families; the free home slots take families first, the rest is homeless (a tent);
  - the homeless count and approval are set by the test (the game rules for approval are not modelled);
  - sack_people (just_die on every member) removes a family from the count.
It tests the Lua logic of the mod. It does NOT prove how the real game decides.
"""

import unittest

import fakegame_path  # noqa: F401
from fakegame import FakeGame
from modstate_support import call, dispatch

PREFIX = "RefugeeWaves."

BUILD_WORLD = """
function(fg)
    local world = { settle_calls = {}, messages = {}, raids = 0, free_slots = 2 }
    local player = fg.object("PawnCPP", { isMainPlayer = true, isBandit = false, commandedSquads = fg.array({}, { wrap = false }) }, "/Game/Fake/Player")
    fg.set_method(player, "GetAddress", function() return 1 end)
    fg.set_method(player, "K2_GetActorLocation", function() return { X = 0.0, Y = 0.0, Z = 0.0 } end)
    fg.set_method(player, "playEventMessage", function(self, kind, text, subtext) world.messages[#world.messages + 1] = text end)
    local bandit = fg.object("PawnCPP", { isMainPlayer = false, isBandit = true, commandedSquads = fg.array({}, { wrap = false }) }, "/Game/Fake/Bandit")

    local families = {}
    local function add_family()
        local members = {}
        for _ = 1, 2 do
            local unit = fg.object("SMUnit", { dead = false })
            fg.set_method(unit, "just_die", function(self) self.dead = true end)
            members[#members + 1] = unit
        end
        families[#families + 1] = { familyMembers = fg.array(members, { wrap = false }), list = members }
    end
    for _ = 1, 10 do add_family() end
    world.homeless = 0
    local region = fg.object("Region", { ownerPawn = player, regionName = "Riesenbuckel", Approval = 71, workerFamilies = fg.array(families, { wrap = false }),
                                         isSettled = true, settlementType = 1, settlementLevel = 0 }, "/Game/Fake/Nusslohe")
    fg.set_method(region, "getTotalNumFamilies", function()
        local count = 0
        for _, family in ipairs(families) do
            local alive = false
            for _, unit in ipairs(family.list) do if not unit.dead then alive = true end end
            if alive then count = count + 1 end
        end
        return count
    end)
    fg.set_method(region, "getNumHomelessFamilies", function() return world.homeless end)
    fg.set_method(region, "getNumHumanResidents", function() return 20 end)
    fg.set_method(region, "getAvailableLivingSpace", function() return { constructed = 0, unconstructed = 0 } end)
    fg.set_method(region, "GetBuildings", function() return fg.array({}, { wrap = false }) end)
    fg.set_method(region, "getSettledRegionCenter", function() return { X = 5.0, Y = 6.0, Z = 7.0 } end)
    fg.set_method(player, "settleRegion", function(self, target, camp, supply, kind)
        world.settle_calls[#world.settle_calls + 1] = { x = camp.Translation.X, y = camp.Translation.Y }
        for _ = 1, 5 do add_family() end
        local housed = math.min(world.free_slots, 5)
        world.free_slots = world.free_slots - housed
        world.homeless = world.homeless + (5 - housed)
    end)

    local calendar = fg.object("TemporalComponent", { daysTotal = 100, day = 10, month = 3, Year = 1 })
    local engine = fg.object("RTSMultiEngineCPP", { playerRef = player, regions = fg.array({ region }, { wrap = false }), TemporalComponent = calendar })
    fg.set_method(engine, "spawnRaiders", function(self, squads, center)
        world.raids = world.raids + 1
        world.raid_target = { x = center.X, y = center.Y }
    end)
    world.calendar = calendar
    world.region = region
    world.groves = function(centres)
        for _, c in ipairs(centres) do
            local mesh = fg.object("StaticMesh", {})
            fg.set_method(mesh, "GetFName", function() return fg.fstring("stc_oak_test") end)
            local component = fg.object("FoliageInstancedStaticMeshComponent", { StaticMesh = mesh })
            fg.set_method(component, "GetOuter", function() return region end)
            fg.set_method(component, "GetInstanceCount", function() return 12 end)
            fg.set_method(component, "GetInstanceTransform", function(self, index, out)
                out.Translation = { X = c[1] + (index % 4) * 100, Y = c[2] + (index // 4) * 100, Z = 50 }
                return true
            end)
        end
    end
    return world
end
"""


class WaveTestCase(unittest.TestCase):
    def setUp(self):
        self.game = FakeGame(separate_states=True)
        self.game.start()
        self.addCleanup(self.game.close)
        self.game.exec("FName = function(text) return { fname = text } end")
        self.world = self.game.lua.eval(BUILD_WORLD)(self.game.fg)
        self.game.load_mod("RefugeeWaves")
        self.game.advance(1)

    def mod(self, name, **args):
        return call(self.game, PREFIX + name, **args)

    def refused(self, name, **args):
        answer = dispatch(self.game, PREFIX + name, args)
        self.assertFalse(answer["ok"], answer)
        return answer["error"]

    def set_day(self, day, month=None):
        self.world.calendar.daysTotal = day
        if month is not None:
            self.world.calendar.month = month

    def add_grove(self):
        self.world.groves(self.game.lua.table_from([[-26000, -26000]], recursive=True))


class RegistrationTests(WaveTestCase):
    def test_commands_and_metrics_are_registered(self):
        names = {c["name"] for c in call(self.game, "harness.list_commands", mod="RefugeeWaves")["commands"]}
        self.assertEqual({n for n in names if n.startswith(PREFIX)}, {PREFIX + n for n in
                         ("configure", "start_wave", "check", "status", "forget_wave")})

    def test_bad_settings_are_refused(self):
        self.assertIn("chance_percent", self.refused("configure", chance_percent=101))
        self.assertIn("calls", self.refused("start_wave", calls=9))


class StartWaveTests(WaveTestCase):
    def test_a_wave_adds_families_and_homeless_and_shows_a_banner(self):
        self.mod("check")
        wave = self.mod("start_wave", calls=2)["wave"]
        self.assertEqual(wave["calls"], 2)
        self.assertEqual((wave["families_before"], wave["families_after"]), (10, 20))
        self.assertEqual((wave["homeless_before"], wave["homeless_after"]), (0, 8))
        self.assertEqual(len(self.world.settle_calls), 2)
        self.assertEqual(list(self.world.messages.values()), ["Refugees have arrived"])
        status = self.mod("status")
        self.assertTrue(status["active"])
        self.assertEqual(self.mod("check")["wave"]["state"], "active")

    def test_camp_is_the_settled_centre_when_no_woods_and_no_village_spot_exist(self):
        self.mod("start_wave", calls=1)
        self.assertEqual(self.mod("status")["wave"]["place"], "centre")

    def test_camp_is_near_the_woods_when_a_grove_exists(self):
        self.add_grove()
        self.mod("start_wave", calls=1)
        self.assertEqual(self.mod("status")["wave"]["place"], "woods")
        self.assertLess(abs(self.world.settle_calls[1]["x"] - -26000), 1000)

    def test_a_second_wave_is_refused_while_one_is_active(self):
        self.mod("start_wave", calls=1)
        answer = dispatch(self.game, PREFIX + "start_wave", {"calls": 1})
        self.assertFalse(answer["ok"])
        self.assertIn("already active", answer["error"])
        self.assertEqual(len(self.world.settle_calls), 1)


class EndTests(WaveTestCase):
    def test_the_wave_ends_housed_when_the_homeless_are_gone(self):
        self.mod("check")
        self.mod("start_wave", calls=1)
        self.world.homeless = 0
        status = self.mod("check")
        self.assertFalse(status["active"])
        self.assertEqual((status["last_outcome"], status["waves_ended"], status["rebellions"]), ("housed", 1, 0))

    def test_partly_housed_keeps_the_wave_active(self):
        self.mod("check")
        self.mod("start_wave", calls=2)
        self.world.homeless = 3
        self.assertTrue(self.mod("check")["active"])


class BadOutcomeTests(WaveTestCase):
    def test_homeless_for_the_day_limit_starts_a_raid_with_half_the_families(self):
        self.add_grove()
        self.mod("configure", homeless_days_limit=30)
        self.mod("check")
        self.mod("start_wave", calls=2)  # 8 homeless
        self.set_day(129)
        self.assertTrue(self.mod("check")["active"])
        self.set_day(130)
        status = self.mod("check")
        self.assertFalse(status["active"])
        self.assertEqual((status["last_outcome"], status["rebellions"]), ("rebelled", 1))
        self.assertEqual(self.world.raids, 1)
        self.assertEqual(self.world.region.getTotalNumFamilies(self.world.region), 20 - 4)

    def test_low_approval_starts_the_raid_before_the_day_limit(self):
        self.add_grove()
        self.mod("check")
        self.mod("start_wave", calls=1)  # 3 homeless
        self.world.region.Approval = 39
        status = self.mod("check")
        self.assertEqual(status["last_outcome"], "rebelled")
        self.assertEqual(self.world.region.getTotalNumFamilies(self.world.region), 15 - 2)  # ceil(3 / 2)

    def test_approval_at_the_floor_does_not_trigger(self):
        self.mod("check")
        self.mod("start_wave", calls=1)
        self.world.region.Approval = 40
        self.assertTrue(self.mod("check")["active"])

    def test_without_a_safe_raid_call_the_gap_is_recorded_and_no_family_is_removed(self):
        self.mod("check")
        self.mod("start_wave", calls=1)
        self.world.region.Approval = 10
        status = self.mod("check")
        self.assertEqual(status["last_outcome"], "rebellion_failed")
        self.assertEqual(self.world.raids, 0)
        self.assertEqual(self.world.region.getTotalNumFamilies(self.world.region), 15)

    def test_housing_wins_over_a_late_check(self):
        self.mod("check")
        self.mod("start_wave", calls=1)
        self.set_day(500)
        self.world.homeless = 0
        self.assertEqual(self.mod("check")["last_outcome"], "housed")
        self.assertEqual(self.world.raids, 0)


class TriggerTests(WaveTestCase):
    def new_month(self, month=4):
        self.set_day(130, month)
        return self.mod("check")

    def test_a_sure_chance_starts_a_wave_at_the_next_month_only(self):
        self.mod("configure", chance_percent=100, seed=1)
        self.assertFalse(self.mod("check")["active"])  # first check only reads the month
        self.assertFalse(self.mod("check")["active"])
        status = self.new_month()
        self.assertTrue(status["active"])
        self.assertEqual(status["waves_started"], 1)
        self.assertEqual(status["wave"]["calls"], 1)  # 10 families allow one call

    def test_zero_chance_never_starts_a_wave(self):
        self.mod("configure", chance_percent=0)
        self.mod("check")
        for month in range(4, 10):
            self.assertFalse(self.new_month(month)["active"])

    def test_a_small_village_gets_no_wave(self):
        self.mod("configure", chance_percent=100, min_families=11)
        self.mod("check")
        self.assertFalse(self.new_month()["active"])

    def test_a_big_village_can_get_more_calls_up_to_the_cap(self):
        self.mod("configure", chance_percent=100, families_per_extra_call=3, max_calls=3, seed=7)
        self.mod("check")
        self.assertIn(self.new_month()["wave"]["calls"], (1, 2, 3))

    def test_no_second_wave_while_one_is_active(self):
        self.mod("configure", chance_percent=100)
        self.mod("check")
        self.new_month(4)
        self.new_month(5)
        self.assertEqual(self.mod("status")["waves_started"], 1)


class LoadTests(WaveTestCase):
    def test_homeless_families_found_at_the_first_check_are_adopted_as_the_wave(self):
        self.world.homeless = 3
        status = self.mod("check")
        self.assertTrue(status["active"])
        self.assertEqual(status["wave"]["place"], "adopted")
        self.assertEqual(self.mod("status")["numbers"]["homeless"], 3)

    def test_nothing_is_adopted_when_the_setting_is_off(self):
        self.mod("configure", adopt_on_start=False)
        self.world.homeless = 3
        self.assertFalse(self.mod("check")["active"])

    def test_nothing_is_adopted_after_the_first_check(self):
        self.mod("check")
        self.world.homeless = 3
        self.assertFalse(self.mod("check")["active"])


if __name__ == "__main__":
    unittest.main()
