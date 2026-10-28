"""Tests for the feature bandits of the pack mod (mod feature M04) in the fake game.

They run the real Lua files. HarnessBandits (the buy-back letter) is replaced by a stub. The fake village has families with homes,
home inventories and members, a fake spawnBanditCamp and a fake squad spawn (HarnessBattle.spawn_at).
They do not prove how the real game behaves (see the real-game test scenarios of the change update-banditry-rebellion-raid).
"""

import json
import unittest

import fakegame_path  # noqa: F401
from fakegame import FakeGame
from test_fakegame_modstate import FNAME, HELPERS, find_pack_mod

STUB = """
package.loaded["HarnessBandits"] = {
    bandit_tag = function(request)
        TAGS = (TAGS or 0) + 1
        return { ok = true }
    end,
    bandit_letter = function(_, raw)
        if LETTER_OK ~= false then LETTERS = (LETTERS or 0) + 1 end
        LAST_LETTER = raw
        return { ok = LETTER_OK ~= false }
    end,
}
TELEMETRY = {}
package.loaded["HarnessTelemetry"] = { register = function(name, fn) TELEMETRY[name] = fn end }
package.loaded["HarnessUnits"] = {
    counts = function() return { by_side = { bandit = BANDIT_UNITS or 0 } } end,
    unitsOfSide = function(side, limit) return PY_BANDIT_UNITS() end,
}
package.loaded["HarnessBattle"] = {
    spawn_at = function(side, template, count, point)
        if SPAWN_FAIL then return nil, "spawn refused by the test" end
        SPAWN_CALLS = (SPAWN_CALLS or 0) + 1
        LAST_SPAWN = { side = side, template = template, count = count, x = point.x, y = point.y }
        return PY_SPAWN(side, template, count, point)
    end,
}
"""

# The weapon ids of the default config: 133 spears, 271 large shields.
SPEAR, SHIELD, BREAD = 133, 271, 15


class BanditsTestCase(unittest.TestCase):
    HAS_PAWN = True       # the fake game starts with an Outlaws pawn; a test sets False to play bandit camps 0

    def setUp(self):
        self.game = FakeGame()
        self.game.start()
        self.addCleanup(self.game.close)
        pack = find_pack_mod()
        self.mod_name = pack.name
        self.game.exec(f'package.path = "{(pack / "Scripts").as_posix()}/?.lua;" .. package.path')
        self.game.exec(FNAME + HELPERS + STUB)
        self.pawn = self.game.obj("PawnCPP", Tags=self.game.array([]))
        self.banners = []
        self.game.method(self.pawn, "playEventMessage", lambda _self, _kind, text, sub: self.banners.append((text, sub)))
        self.game.method(self.pawn, "K2_GetActorLocation", lambda _self: self.game.struct(X=0.0, Y=0.0, Z=0.0))
        self.game.method(self.pawn, "GetAddress", lambda _self: self.pawn_address)
        self.pawn_address = 1
        self.calendar = self.game.obj("TemporalComponent", daysTotal=61, daysUntilNextRaid=730, Season=1)
        self.region = self.game.obj("Region", ownerPawn=self.pawn, publicOrder=100, Approval=65, workerFamilies=self.game.array([]))
        self.families = 10          # the number the game reports; arm() raises it
        self.slots = 4
        self.homeless = 0
        self.pawn.silver = 83
        self.game.method(self.region, "getTotalNumFamilies", lambda _self: self.families)
        self.game.method(self.region, "getNumHomelessFamilies", lambda _self: self.homeless)
        self.game.method(self.region, "getAvailableLivingSpace", lambda _self: self.game.struct(constructed=self.slots, unconstructed=0))
        self.engine = self.game.obj("RTSMultiEngineCPP", playerRef=self.pawn, TemporalComponent=self.calendar,
                                    regions=self.game.array([self.region]), debugLog_AI_general=self.game.array([]))
        self.clock = 1000.0
        self.game.method(self.engine, "getGameTimeAdjusted", lambda _self: self.clock)
        self.family_rows, self.units, self.bandit_units, self.camps, self.bandit_pawns = [], [], [], [], []
        self.camp_calls, self.relation_calls, self.demolish_calls, self.next_squad, self.next_address = 0, [], [], 30, 5000
        self.camp_works = True
        self.home_adds = []
        self.install_camp_engine()
        if self.HAS_PAWN:
            self.bandit_pawns.append(self.game.obj("PawnCPP", isBandit=True))
        lua = self.game.lua
        lua.globals().PY_BANDIT_UNITS = lambda: lua.table_from([u for u in self.bandit_units if not u.dead])
        lua.globals().PY_SPAWN = self.spawn_squads
        self.game.load_mod(self.mod_name)
        self.game.advance(3)
        self.counter = 0

    # -- the fake game ---------------------------------------------------------------------

    def make_unit(self, squad, bandit=True, dead=False):
        self.next_address += 1
        address = self.next_address
        unit = self.game.obj("SMUnit", dead=dead, assignedSquadID=self.game.struct(Value=squad))
        self.game.method(unit, "GetAddress", lambda _self, address=address: address)
        self.game.method(unit, "just_die", lambda _self, unit=unit: setattr(unit, "dead", True))
        self.game.method(unit, "SetActorHiddenInGame", lambda _self, hidden, unit=unit: setattr(unit, "hidden", hidden))
        unit.hidden = False
        self.units.append(unit)
        if bandit:
            self.bandit_units.append(unit)
        return unit

    def spawn_squads(self, side, template, count, point):
        """HarnessBattle.spawn_at: `count` squads of 18 units."""
        lua = self.game.lua
        squads = []
        for _ in range(count):
            self.next_squad += 1
            for _ in range(18):
                self.make_unit(self.next_squad)
            squads.append(lua.table_from({"id": self.next_squad, "units": 18}))
        self.game.exec(f"BANDIT_UNITS = (BANDIT_UNITS or 0) + {18 * count}")
        return lua.table_from({"squads": lua.table_from(squads), "units": 18 * count})

    def install_camp_engine(self):
        """The fake engine plays spawnBanditCamp: it makes the bandit pawn when missing, 18 Brigands and a camp building."""
        def spawn(_self):
            self.camp_calls += 1
            if not self.camp_works:
                raise RuntimeError("boom")
            if not self.bandit_pawns:
                self.bandit_pawns.append(self.game.obj("PawnCPP", isBandit=True))
            self.next_squad += 1
            for _ in range(18):
                self.make_unit(self.next_squad)
            camp = self.game.obj("SMBuildingMaster", Data=self.game.struct(bType=100))
            self.next_address += 1
            address = self.next_address
            self.game.method(camp, "GetAddress", lambda _self, address=address: address)
            self.game.method(camp, "demolish", lambda _self, flag, camp=camp: self.demolish_calls.append(flag))
            self.camps.append(camp)
            self.game.exec("BANDIT_UNITS = (BANDIT_UNITS or 0) + 18")
        self.game.method(self.engine, "spawnBanditCamp", spawn)
        self.game.method(self.engine, "addPawnRelations", lambda _self, pawn: self.relation_calls.append(pawn))

    def add_family(self, goods=(), members=3):
        """A family with a home. goods: a list of (item id, amount) in the home inventory. Returns the row."""
        index = len(self.family_rows)
        row = {"goods": [list(g) for g in goods], "members": [], "index": index}
        home = self.game.obj("SMBuildingMaster", Data=self.game.struct(bType=3))
        row["home"] = home

        def refresh():
            home.Inventory = self.game.array([self.game.struct(Type=t, amt=a) for t, a in row["goods"]])

        def consume(_self, good):
            for entry in row["goods"]:
                if entry[0] == good and entry[1] > 0:
                    entry[1] -= 1
                    break
            refresh()

        def add(_self, good):
            for entry in row["goods"]:
                if entry[0] == good["Type"]:
                    entry[1] += good["amt"]
                    break
            else:
                row["goods"].append([good["Type"], good["amt"]])
            self.home_adds.append((index, good["Type"], good["amt"]))
            refresh()

        self.game.method(home, "consumeGoodNoCheck", consume)
        self.game.method(home, "addToInventory", add)
        self.game.method(home, "K2_GetActorLocation", lambda _self, index=index: self.game.struct(X=1000.0 * (index + 1), Y=500.0, Z=10.0))
        refresh()
        for _ in range(members):
            row["members"].append(self.make_unit(squad=900 + index, bandit=False))
        family = self.game.struct(familyHome=home, familyMembers=self.game.array(row["members"]))
        self.family_rows.append(row)
        self.region.workerFamilies = self.game.array([self.game.struct(familyHome=r["home"], familyMembers=self.game.array(r["members"])) for r in self.family_rows])
        self.families = max(self.families, len(self.family_rows))
        return row

    def arm(self, count, goods=((SPEAR, 1), (SHIELD, 1)), members=3):
        """`count` families that hold weapons at home."""
        return [self.add_family(goods, members) for _ in range(count)]

    def goods_of(self, row):
        return {t: a for t, a in row["goods"] if a > 0}

    def dead_members(self):
        return sum(1 for row in self.family_rows for m in row["members"] if m.dead)

    # -- the commands ----------------------------------------------------------------------

    def ask(self, name, **args):
        self.counter += 1
        folder = self.game.run_dir / "modcmd" / self.mod_name
        folder.mkdir(parents=True, exist_ok=True)
        body = {"id": f"{self.counter:04d}", "command": f"{self.mod_name}.{name}", "args": args}
        (folder / f"{self.counter:04d}.json").write_text(json.dumps(body), encoding="utf-8")
        self.game.advance(1)
        return json.loads((folder / f"{self.counter:04d}.result.json").read_text(encoding="utf-8"))

    def state(self):
        answer = self.ask("bandits_state")
        self.assertTrue(answer["ok"], answer)
        return answer["result"]

    def overrides(self):
        answer = self.ask("raid_behavior_override_state")
        self.assertTrue(answer["ok"], answer)
        return answer["result"]

    def spawn_calls(self):
        return self.game.exec("return SPAWN_CALLS or 0")

class OrderTests(BanditsTestCase):
    def test_a_new_game_starts_at_100_and_the_mod_writes_it(self):
        self.region.publicOrder = 60  # the game's own value
        self.game.advance(3)
        self.assertEqual(self.region.publicOrder, 100)
        self.assertEqual(self.state()["mod_order"], 100)

    def test_the_game_value_is_overwritten_again(self):
        self.game.advance(3)
        self.region.publicOrder = 40  # the game recalculates
        self.game.advance(3)
        self.assertEqual(self.region.publicOrder, 100)
        self.assertGreaterEqual(self.state()["overwrites"], 1)

    def test_set_order_writes_the_game_value(self):
        self.ask("bandits_set_order", value=70)
        self.game.advance(3)
        self.assertEqual(self.region.publicOrder, 70)

    def test_a_reload_keeps_the_order_and_the_tick_day(self):
        self.ask("bandits_set_order", value=70)
        self.calendar.daysTotal = 80
        self.game.advance(3)
        before = self.state()
        self.game.load_mod(self.mod_name)  # ModState keeps the saved values
        self.game.advance(5)
        after = self.state()
        self.assertEqual((after["mod_order"], after["last_tick_day"]), (70, before["last_tick_day"]))


class TickTests(BanditsTestCase):
    def test_no_tick_before_30_days(self):
        self.ask("bandits_set_order", value=50)
        self.calendar.daysTotal = 61 + 29
        self.game.advance(5)
        state = self.state()
        self.assertEqual((state["ticks"], state["mod_order"]), (0, 50))

    def test_a_tick_every_30_days(self):
        self.ask("bandits_set_order", value=50)
        self.game.advance(3)
        self.calendar.daysTotal = 61 + 30
        self.game.advance(3)
        self.calendar.daysTotal = 61 + 59
        self.game.advance(3)
        self.assertEqual(self.state()["ticks"], 1)
        self.calendar.daysTotal = 61 + 61
        self.game.advance(3)
        state = self.state()
        self.assertEqual((state["ticks"], state["mod_order"]), (2, 70))

    def test_a_tick_with_homeless_villagers_is_recorded(self):
        self.homeless = 4
        self.ask("bandits_set_order", value=50)
        tick = self.ask("bandits_tick_now")["result"]["last_tick"]
        self.assertEqual(
            {key: tick[key] for key in ("order_before", "manor_term", "homeless_count", "homeless_term", "order_after")},
            {"order_before": 50, "manor_term": 10, "homeless_count": 4, "homeless_term": 20, "order_after": 40},
        )
        self.assertEqual(self.region.publicOrder, 40)

    def test_the_tick_is_logged(self):
        self.ask("bandits_tick_now")
        self.assertTrue(any("BANDITS tick day=" in line for line in self.game.log_lines()))

    def test_the_tech_tree_order_bonus_adds_to_the_manor_term(self):
        self.game.exec('require("features.bandits.init").set_modifiers({ order_bonus = 5 })')
        self.ask("bandits_set_order", value=50)
        self.assertEqual(self.ask("bandits_tick_now")["result"]["last_tick"]["manor_term"], 15)

    def test_the_telemetry_metric_holds_the_last_tick(self):
        self.ask("bandits_tick_now")
        self.assertEqual(self.game.exec("return TELEMETRY.bandits_order().last_tick.order_after"), 100)


class TimerTests(BanditsTestCase):
    def setUp(self):
        super().setUp()
        self.game.exec('require("config").bandits.tick_days = 100000')  # no tick moves the order in these tests

    def test_low_order_starts_the_timer_with_a_banner(self):
        self.ask("bandits_set_order", value=20)
        state = self.state()
        self.assertTrue(state["timer"]["active"])
        self.assertEqual(state["timer"]["days_left"], 60)
        self.assertEqual(len(self.banners), 1)
        self.assertIn("unrest", self.banners[0][0].lower())

    def test_the_timer_resets_when_order_reaches_25(self):
        self.arm(10)
        self.ask("bandits_set_order", value=20)
        self.ask("bandits_set_order", value=25)
        self.assertFalse(self.state()["timer"]["active"])
        self.calendar.daysTotal = 61 + 200
        self.game.advance(5)
        self.assertEqual(self.state()["converted_families"], 0)

    def test_the_warning_shows_once_30_days_before(self):
        self.ask("bandits_set_order", value=20)
        self.calendar.daysTotal = 61 + 29
        self.game.advance(3)
        self.assertEqual(len(self.banners), 1)
        self.calendar.daysTotal = 61 + 30
        self.game.advance(3)
        self.calendar.daysTotal = 61 + 40
        self.game.advance(3)
        self.assertEqual(len(self.banners), 2)
        self.assertIn("about to leave", self.banners[1][0])

    def test_the_rebellion_starts_when_the_timer_expires(self):
        self.arm(8)
        self.ask("bandits_set_order", value=20)
        self.calendar.daysTotal = 61 + 60
        self.game.advance(3)
        state = self.state()
        self.assertEqual(state["converted_families"], 6)
        self.assertEqual(state["mod_order"], 45)  # 20 + 25
        self.assertFalse(state["timer"]["active"])  # order 45 is not under 25
        self.assertEqual(self.banners[-1][0], "Families have turned to banditry")
        self.assertEqual(self.dead_members(), 18)  # 6 families, 3 members each

    def test_the_timer_restarts_after_a_rebellion_when_order_stays_under_25(self):
        self.arm(8)
        self.ask("bandits_set_order", value=0)
        self.game.exec('require("config").bandits.order_gain = 10')
        self.calendar.daysTotal = 61 + 60
        self.game.advance(3)
        state = self.state()
        self.assertEqual(state["mod_order"], 10)
        self.assertTrue(state["timer"]["active"])
        self.assertEqual(state["timer"]["days_left"], 60)

    def test_the_last_family_stays(self):
        self.families = 1
        self.ask("bandits_set_order", value=20)
        self.calendar.daysTotal = 61 + 60
        self.game.advance(3)
        self.assertEqual(self.state()["converted_families"], 0)
        self.assertEqual(self.dead_members(), 0)

    def test_fewer_families_than_6_all_but_one_leave(self):
        self.arm(4)
        self.families = 4
        self.ask("bandits_set_order", value=20)
        self.calendar.daysTotal = 61 + 60
        self.game.advance(3)
        self.assertEqual(self.state()["converted_families"], 3)  # the village keeps one family

    def test_a_blocked_rebellion_keeps_the_timer_expired(self):
        self.arm(5)
        self.families = 10
        self.ask("bandits_set_order", value=20)
        self.calendar.daysTotal = 61 + 60
        self.game.advance(3)
        state = self.state()
        self.assertEqual((state["converted_families"], state["blocks"]), (0, 1))
        self.assertEqual(state["mod_order"], 20)  # no order gain
        self.assertTrue(state["timer"]["active"])
        self.assertEqual(self.dead_members(), 0)
        self.game.advance(10)  # no new tick: no new try
        self.assertEqual(self.state()["blocks"], 1)

    def test_weapons_that_arrive_after_a_blocked_tick_start_the_rebellion_on_the_next_tick(self):
        self.arm(5)
        self.families = 10
        self.game.exec('require("config").bandits.tick_days = 30')
        self.game.exec('require("config").bandits.manor_term = 0')  # the tick keeps the order at 20
        self.ask("bandits_set_order", value=20)
        self.calendar.daysTotal = 61 + 31
        self.game.advance(3)
        self.assertEqual(self.state()["blocks"], 0)  # the tick at day 92 came first; the timer started at 61 + 0
        self.calendar.daysTotal = 61 + 61
        self.game.advance(3)
        self.assertEqual(self.state()["blocks"], 1)
        self.arm(2)  # now 7 valid families
        self.game.advance(3)
        self.assertEqual(self.state()["converted_families"], 0)  # still waiting for the next tick
        self.calendar.daysTotal = 61 + 92
        self.game.advance(3)
        state = self.state()
        self.assertEqual(state["converted_families"], 6)
        self.assertEqual(state["blocks"], 1)


class RebellionTests(BanditsTestCase):
    """The leave event: selection, goods, bodies, the squad and the loot overrides."""

    def rebel(self, count=6):
        answer = self.ask("bandits_leave_now", count=count)
        self.assertTrue(answer["ok"], answer)
        return answer["result"]

    def test_six_of_nine_valid_families_leave_chosen_at_random(self):
        rows = self.arm(9)
        result = self.rebel()
        self.assertEqual(result["last_leave"]["removed"], 6)
        self.assertEqual(result["last_leave"]["valid"], 9)
        left = [row for row in rows if any(m.dead for m in row["members"])]
        self.assertEqual(len(left), 6)
        self.assertTrue(all(all(m.dead for m in row["members"]) for row in left))

    def test_the_pick_is_random_and_not_the_best_armed(self):
        seen = set()
        for seed in range(8):
            self.setUp()
            rows = self.arm(7, goods=((SPEAR, 1),))
            rows[0]["goods"] = [[SPEAR, 9], [SHIELD, 9]]  # the best armed home
            self.game.exec(f"math.randomseed({seed})")
            self.rebel()
            seen.add(tuple(i for i, row in enumerate(rows) if any(m.dead for m in row["members"])))
        self.assertGreater(len(seen), 1)  # not always the same families

    def test_bodies_of_the_families_are_hidden(self):
        self.arm(6)
        self.rebel()
        members = [m for row in self.family_rows for m in row["members"]]
        self.assertTrue(all(m.hidden for m in members if m.dead))
        self.assertEqual(sum(1 for m in members if m.dead), 18)

    def test_the_goods_of_the_chosen_homes_are_taken_and_the_others_keep_theirs(self):
        rows = self.arm(9, goods=((SPEAR, 2), (SHIELD, 1), (BREAD, 5)))
        self.rebel()
        left = [row for row in rows if any(m.dead for m in row["members"])]
        stay = [row for row in rows if not any(m.dead for m in row["members"])]
        self.assertTrue(all(self.goods_of(row) == {BREAD: 5} for row in left))
        self.assertEqual(len(stay), 3)
        self.assertTrue(all(self.goods_of(row) == {SPEAR: 2, SHIELD: 1, BREAD: 5} for row in stay))

    def test_a_home_with_only_bread_is_not_valid(self):
        self.arm(5)
        self.add_family(goods=((BREAD, 9),))
        result = self.rebel()
        self.assertEqual(result["last_leave"]["valid"], 5)
        self.assertEqual(result["last_leave"]["blocked"], "5 valid families found, 6 needed")

    def test_one_squad_of_18_spawns_at_the_first_removed_home(self):
        self.arm(6)
        result = self.rebel()
        self.assertEqual(self.spawn_calls(), 1)
        self.assertEqual(self.game.exec("return LAST_SPAWN.template .. ',' .. LAST_SPAWN.side .. ',' .. LAST_SPAWN.count"), "Brigands,bandit,1")
        x = self.game.exec("return LAST_SPAWN.x")
        self.assertIn(x, [1000.0 * (i + 1) for i in range(6)])  # the x of a home
        self.assertEqual((result["last_leave"]["squads"], result["last_leave"]["bandit_units"]), (1, 18))

    def test_the_squad_count_follows_the_config(self):
        self.arm(6)
        self.game.exec('require("config").bandits.rebellion_squads = 2')
        result = self.rebel()
        self.assertEqual(self.game.exec("return LAST_SPAWN.count"), 2)
        self.assertEqual(result["last_leave"]["bandit_units"], 36)

    def test_no_camp_call_when_the_pawn_exists(self):
        self.arm(6)
        self.rebel()
        self.assertEqual((self.camp_calls, self.relation_calls), (0, []))

    def test_all_goods_go_to_the_overrides_of_the_18_brigands_and_none_twice(self):
        self.arm(6, goods=((SPEAR, 3), (SHIELD, 2)))  # 30 goods
        result = self.rebel()
        self.assertEqual(result["last_leave"]["taken"], 30)
        entries = self.overrides()["entries"]
        total = [good for entry in entries for good in entry["goods"]]
        self.assertEqual(len(total), 30)
        self.assertEqual(sorted(total), sorted([SPEAR] * 18 + [SHIELD] * 12))
        self.assertEqual(len(entries), 18)  # 30 goods over 18 units: every unit has an entry
        self.assertEqual(len({(e["squad"], e["index"]) for e in entries}), 18)

    def test_fewer_goods_than_units_leave_some_units_without_entry(self):
        self.arm(6, goods=((SPEAR, 1),))
        self.rebel()
        self.assertEqual(self.overrides()["count"], 6)

    def test_the_overrides_are_saved_in_the_tags(self):
        self.arm(6, goods=((SPEAR, 1),))
        self.rebel()
        names = self.game.lua.eval("tag_names")(self.pawn)
        slots = [name for name in names.values() if name.startswith("invasion:loot_slot_") and not name.endswith("=")]
        self.assertEqual(len(slots), 6)
        self.assertTrue(all("=" in name and name.split("=")[1].count("_") == 2 for name in slots))

    def test_a_failed_spawn_returns_the_goods_and_logs_an_error(self):
        rows = self.arm(7, goods=((SPEAR, 2), (SHIELD, 1)))
        self.game.exec("SPAWN_FAIL = true")
        result = self.rebel()
        self.assertFalse(result["last_leave"]["spawned"])
        self.assertEqual(result["last_leave"]["taken"], 18)
        self.assertEqual(result["last_leave"]["returned"], 18)
        left = [row for row in rows if any(m.dead for m in row["members"])]
        self.assertEqual(len(left), 6)  # the families stay gone
        self.assertTrue(all(self.goods_of(row) == {SPEAR: 2, SHIELD: 1} for row in rows))
        self.assertTrue(any("rebellion spawn failed" in line for line in self.game.log_lines()))
        self.assertEqual(self.overrides()["count"], 0)

    def test_the_rebellion_is_logged_with_the_new_fields(self):
        self.arm(6)
        self.rebel()
        line = next(line for line in self.game.log_lines() if "BANDITS leave day=" in line)
        for part in ("valid=6", "families_left=6", "goods_taken=12", "goods_returned=0", "squads=1", "bandit_units=18", "overrides=12"):
            self.assertIn(part, line)


class BlockedTests(BanditsTestCase):
    def blocked(self, count=6):
        answer = self.ask("bandits_leave_now", count=count)
        self.assertTrue(answer["ok"], answer)
        return answer["result"]

    def test_too_few_valid_families_remove_nothing(self):
        rows = self.arm(5, goods=((SPEAR, 2),))
        self.families = 20
        result = self.blocked()
        self.assertEqual(result["last_leave"]["blocked"], "5 valid families found, 6 needed")
        self.assertEqual(self.dead_members(), 0)
        self.assertTrue(all(self.goods_of(row) == {SPEAR: 2} for row in rows))
        self.assertEqual(self.spawn_calls(), 0)
        self.assertEqual(result["converted_families"], 0)
        self.assertEqual(result["mod_order"], 100)

    def test_the_event_is_logged_and_in_the_state_and_the_telemetry(self):
        self.arm(5)
        result = self.blocked()
        self.assertTrue(any("BANDITS rebellion_blocked" in line and "valid=5" in line and "needed=6" in line for line in self.game.log_lines()))
        self.assertEqual((result["blocked"]["valid"], result["blocked"]["needed"]), (5, 6))
        self.assertEqual(self.game.exec("return TELEMETRY.bandits_order().last_blocked.valid"), 5)
        self.assertEqual(result["blocks"], 1)

    def test_an_unarmed_village_is_blocked_on_every_try(self):
        self.add_family(goods=((BREAD, 3),))
        self.families = 20
        for _ in range(3):
            self.assertIsNotNone(self.blocked()["last_leave"]["blocked"])
        self.assertEqual(self.state()["blocks"], 3)
        self.assertEqual(self.dead_members(), 0)

    def test_weapons_that_arrive_later_let_the_next_try_pass(self):
        self.arm(5)
        self.assertIsNotNone(self.blocked()["last_leave"]["blocked"])
        self.arm(1)
        result = self.blocked()
        self.assertIsNone(result["last_leave"].get("blocked"))
        self.assertEqual(result["last_leave"]["removed"], 6)


class BuyBackTests(BanditsTestCase):
    """C1, C4 to C7 in the fake game. The stub plays the game: it records the letter, the test moves silver, units and families."""

    def convert(self):
        self.arm(3)
        self.ask("bandits_leave_now", count=2)
        self.game.exec("BANDIT_UNITS = 18")
        self.families -= 2

    def letter(self):
        return self.game.exec("return LAST_LETTER"), self.game.exec("return LETTERS or 0")

    def test_a_conversion_adds_outstanding_families(self):
        self.convert()
        self.assertEqual(self.state()["outstanding_families"], 2)

    def test_buy_back_sends_the_letter_with_the_price(self):
        self.convert()
        answer = self.ask("bandits_buy_back")["result"]
        self.assertTrue(answer["accepted"], answer)
        self.assertEqual((answer["price"], answer["expected_families"]), (20, 2))
        raw, count = self.letter()
        self.assertEqual(count, 1)
        self.assertIn("raider_suggestSettle+20", raw)
        self.assertEqual(self.game.exec("return TAGS"), 1)
        self.assertEqual(self.state()["outstanding_families"], 0)

    def test_the_result_is_recorded_when_the_bandits_are_gone(self):
        self.convert()
        self.ask("bandits_buy_back")
        self.game.exec("BANDIT_UNITS = 0")
        self.pawn.silver = 63
        self.families += 2
        self.game.advance(8)
        state = self.state()
        self.assertFalse(state["buy_back_pending"])
        self.assertEqual(state["returned_families"], 2)
        self.assertEqual((state["buy_backs"][0]["silver_paid"], state["buy_backs"][0]["family_gain"]), (20, 2))

    def test_a_failed_deal_gives_the_silver_back_and_keeps_the_families_outstanding(self):
        self.pawn.silver = 100
        self.convert()
        self.ask("bandits_buy_back")
        self.game.exec("BANDIT_UNITS = 0")
        self.pawn.silver = 80  # the game took the price, no family came
        self.clock += 130
        self.game.advance(8)
        state = self.state()
        self.assertFalse(state["buy_back_pending"])
        self.assertEqual(self.pawn.silver, 100)
        self.assertEqual(state["outstanding_families"], 2)
        self.assertEqual(state["returned_families"], 0)
        self.assertEqual((state["buy_backs"][0]["refunded"], state["buy_backs"][0]["family_gain"]), (20, 0))

    def test_the_mod_waits_in_game_time_for_a_late_family(self):
        self.convert()
        self.ask("bandits_buy_back")
        self.game.exec("BANDIT_UNITS = 0")
        self.game.advance(10)  # real time passes, the game clock stands still
        self.assertTrue(self.state()["buy_back_pending"])

    def test_the_price_follows_the_free_slots(self):
        self.convert()
        self.slots = 1
        answer = self.ask("bandits_buy_back")["result"]
        self.assertEqual((answer["price"], answer["expected_families"]), (10, 1))
        self.assertEqual(self.state()["outstanding_families"], 1)

    def refused(self, reason_part):
        before = self.state()["outstanding_families"], self.letter()[1]
        answer = self.ask("bandits_buy_back")["result"]
        self.assertFalse(answer["accepted"], answer)
        self.assertIn(reason_part, answer["reason"])
        self.assertEqual((self.state()["outstanding_families"], self.letter()[1]), before)

    def test_refused_when_silver_is_short(self):
        self.convert()
        self.pawn.silver = 19
        self.refused("silver")

    def test_refused_without_free_homes(self):
        self.convert()
        self.slots = 0
        self.refused("free home")

    def test_refused_when_nothing_is_outstanding(self):
        self.game.exec("BANDIT_UNITS = 18")
        self.refused("no families")

    def test_refused_without_bandit_units(self):
        self.convert()
        self.game.exec("BANDIT_UNITS = 0")
        self.refused("no bandit units")

    def test_a_failed_letter_changes_nothing(self):
        self.convert()
        self.game.exec("LETTER_OK = false")
        self.refused("letter failed")

    def test_a_second_buy_back_waits_for_the_first(self):
        self.convert()
        self.ask("bandits_buy_back")
        self.refused("still running")


if __name__ == "__main__":
    unittest.main()
