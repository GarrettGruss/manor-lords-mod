"""Tests for the feature liege_contracts of the pack mod in the fake game.

They run the real Lua files. They do not prove how the real game behaves (see the test scenarios of the feature).
"""

import json
import unittest

import fakegame_path  # noqa: F401
from test_fakegame_modstate import find_pack_mod
from test_fakegame_tech_tree import TechTreeTestCase
from test_fakegame_vassals import VassalsTestCase

STOREHOUSE = """
function(fg, region)
    local world = { stock = {}, buildings = {} }
    local function add_stock(kind, amount) world.stock[kind] = (world.stock[kind] or 0) + amount end
    local function make(btype, constructed, number)
        local b = fg.object("SMBuildingMaster", { Data = { bType = btype, constructed = constructed }, Inventory = fg.array({}, { wrap = false }) },
                            "/Game/Fake/Map.Map:PersistentLevel.SMBuildingMaster_" .. number)
        fg.set_method(b, "IsRubble", function() return false end)
        fg.set_method(b, "addToInventory", function(self, good)
            local found
            for i = 1, #self.Inventory do if self.Inventory[i].Type == good.Type then found = self.Inventory[i] end end
            if found then found.amt = found.amt + good.amt else fg.array_add(self.Inventory, { Type = good.Type, amt = good.amt }) end
            add_stock(good.Type, good.amt)
        end)
        fg.set_method(b, "consumeGoodNoCheck", function(self, kind)
            for i = 1, #self.Inventory do
                local entry = self.Inventory[i]
                if entry.Type == kind and entry.amt > 0 then entry.amt = entry.amt - 1; add_stock(kind, -1); return end
            end
            error("nothing to consume")
        end)
        return b
    end
    world.store = make(72, true, 72)
    world.buildings[1] = world.store
    fg.set_method(region, "GetBuildings", function() return world.buildings end)
    fg.set_method(region, "getStockOfGood", function(self, kind) return world.stock[kind] or 0 end)
    world.add_building = function(btype, constructed) world.buildings[#world.buildings + 1] = make(btype, constructed, 100 + #world.buildings) end
    world.remove_store = function() world.buildings = {} end
    world.hide_goods = function(kind, amount)
        for i = 1, #world.store.Inventory do
            local entry = world.store.Inventory[i]
            if entry.Type == kind then entry.amt = entry.amt - amount end
        end
    end
    return world
end
"""

WINTER, SPRING, SUMMER, AUTUMN = 0, 1, 2, 3
TIMBER = 16
FEATURE = 'require("features.liege_contracts.init")'
THREE = "{}.clear_the_roads.keep_the_peace"


def with_two(first):
    return THREE.format(first) if first != "clear_the_roads" else "clear_the_roads.keep_the_peace.feed_the_city"


class ContractsTestCase(TechTreeTestCase):
    def setUp(self):
        super().setUp()
        self.world = self.game.lua.eval(STOREHOUSE)(self.game.fg, self.region)
        self.pawn.silver = 1000

    def contracts(self):
        answer = self.ask("liege_contracts_state")
        self.assertTrue(answer["ok"], answer)
        return answer["result"]

    def offer_now(self, ids=None):
        answer = self.ask("liege_contracts_offer_now", **({"ids": ids} if ids else {}))
        self.assertTrue(answer["ok"], answer)
        return answer["result"]

    def pick(self, contract_id):
        return self.ask("liege_contract_pick", id=contract_id)

    def complete(self):
        return self.ask("liege_contract_complete")

    def start(self, contract_id):
        self.offer_now(with_two(contract_id))
        answer = self.pick(contract_id)
        self.assertTrue(answer["ok"], answer)

    def set_stock(self, good, amount):
        self.game.lua.eval("function(world, good, amount) world.store:addToInventory({ Type = good, amt = amount }) end")(self.world, good, amount)

    def stock(self, good):
        return self.world.stock[good] or 0

    def season(self, value, days=91):
        """Move the calendar to a season so that invasion counts one season change."""
        self.calendar.daysTotal = self.calendar.daysTotal + days
        self.calendar.Season = value
        self.game.advance(6)

    def influence(self):
        return self.ask("liege_state")["result"]["influence"]

    def set_influence(self, value):
        self.game.exec(f"{FEATURE}; require('features.liege_influence.init').state:set('liege_influence', {value})")


class SmokeTests(ContractsTestCase):
    def test_the_feature_loads_with_the_starter_table(self):
        state = self.contracts()
        self.assertGreaterEqual(state["contract_count"], 8)
        self.assertEqual(state["offer"], [])
        self.assertIsNone(state.get("active"))


class LoaderTests(ContractsTestCase):
    GOOD = ('{ id = "a", name = "A", weight = 1, duration = "winter_start", '
            'objectives = { { type = "kill_raiders", amount = 3 } }, rewards = { { type = "influence", amount = 5 } } }')

    def build(self, contracts_lua, extra="offer_size = 1"):
        return self.game.exec(f"""
            local loader = require("features.liege_contracts.loader")
            local ok, err = pcall(loader.build, {{ version = 1, {extra}, contracts = {{ {contracts_lua} }} }})
            return ok and "ok" or tostring(err)
        """)

    def test_the_starter_table_holds_8_contracts_with_known_types(self):
        loaded = self.game.exec(f"""
            local contracts = {FEATURE}.contracts
            local loader = require("features.liege_contracts.loader")
            local bad = 0
            for _, c in ipairs(contracts.contracts) do
                for _, o in ipairs(c.objectives) do if loader.OBJECTIVE_TYPES[o.type] == nil then bad = bad + 1 end end
                for _, r in ipairs(c.rewards) do if loader.REWARD_TYPES[r.type] == nil then bad = bad + 1 end end
            end
            return #contracts.contracts .. ":" .. bad .. ":" .. contracts.offer_size
        """)
        self.assertEqual(loaded, "8:0:3")

    def test_the_table_has_no_envoy_and_no_penalty_field(self):
        text = (find_pack_mod() / "data" / "liege_contracts" / "contracts.json").read_text(encoding="utf-8")
        data = json.loads(text)
        self.assertNotIn("envoy", text)
        for contract in data["contracts"]:
            self.assertNotIn("penalty", contract)
            self.assertNotIn("fail_penalty", contract)

    def test_at_least_one_starter_contract_pays_a_tech_pick(self):
        data = json.loads((find_pack_mod() / "data" / "liege_contracts" / "contracts.json").read_text(encoding="utf-8"))
        kinds = {reward["type"] for contract in data["contracts"] for reward in contract["rewards"]}
        self.assertIn("tech_pick", kinds)
        self.assertNotIn("retinue_squad", kinds)

    def test_a_good_table_loads(self):
        self.assertEqual(self.build(self.GOOD), "ok")

    def test_a_duplicate_id_names_the_contract(self):
        self.assertIn("duplicate contract id 'a'", self.build(self.GOOD + ", " + self.GOOD))

    def test_an_unknown_type_names_the_contract(self):
        answer = self.build(self.GOOD.replace("kill_raiders", "dance"))
        self.assertIn("contract 'a'", answer)
        self.assertIn("unknown type 'dance'", answer)

    def test_a_missing_field_names_the_contract_and_the_field(self):
        answer = self.build(self.GOOD.replace("amount = 3", ""))
        self.assertIn("contract 'a'", answer)
        self.assertIn("'amount'", answer)

    def test_fewer_contracts_than_the_offer_size_stop_the_load(self):
        self.assertIn("offer_size is 3", self.build(self.GOOD, "offer_size = 3"))

    def test_a_bad_duration_stops_the_load(self):
        self.assertIn("'duration'", self.build(self.GOOD.replace('"winter_start"', '"never"')))

    def test_an_id_with_a_dot_is_refused(self):
        self.assertIn("may hold only", self.build(self.GOOD.replace('id = "a"', 'id = "a.b"')))

    def test_three_objectives_are_refused(self):
        item = '{ type = "kill_raiders", amount = 3 }'
        three = self.GOOD.replace(item, ", ".join([item] * 3))
        self.assertIn("at most 2", self.build(three))


class DrawTests(ContractsTestCase):
    LCG = """
        local seed = SEED
        local function rng() seed = (seed * 1103515245 + 12345) % 2147483648; return seed / 2147483648 end
    """

    def test_the_draw_gives_different_ids(self):
        bad = self.game.exec(self.LCG.replace("SEED", "7") + f"""
            local rules = require("features.liege_contracts.rules")
            local contracts = {FEATURE}.contracts
            local bad = 0
            for _ = 1, 200 do
                local ids = rules.draw(contracts.contracts, 3, rng)
                if #ids ~= 3 or ids[1] == ids[2] or ids[1] == ids[3] or ids[2] == ids[3] then bad = bad + 1 end
            end
            return bad
        """)
        self.assertEqual(bad, 0)

    def test_weights_set_the_chance_of_a_contract(self):
        counts = self.game.exec(self.LCG.replace("SEED", "11") + """
            local rules = require("features.liege_contracts.rules")
            local list = { { id = "ten", weight = 10 }, { id = "five", weight = 5 }, { id = "x", weight = 5 }, { id = "y", weight = 5 } }
            local ten, five = 0, 0
            for _ = 1, 2000 do
                local ids = rules.draw(list, 1, rng)
                if ids[1] == "ten" then ten = ten + 1 elseif ids[1] == "five" then five = five + 1 end
            end
            return ten .. ":" .. five
        """)
        ten, five = (int(part) for part in counts.split(":"))
        self.assertAlmostEqual(ten / five, 2.0, delta=0.3)

    def test_a_draw_of_more_than_the_pool_fails(self):
        self.assertEqual(self.game.exec("""
            local ids, why = require("features.liege_contracts.rules").draw({ { id = "a", weight = 1 } }, 3, math.random)
            return ids == nil and why or "drawn"
        """), "only 1 contracts, 3 wanted")


class SpringTests(ContractsTestCase):
    def go_to_spring(self):
        for value in (SUMMER, AUTUMN, WINTER, SPRING):
            self.season(value)

    def test_a_new_game_makes_no_offer_at_the_first_poll(self):
        self.game.advance(5)
        state = self.contracts()
        self.assertEqual(state["offer"], [])
        self.assertEqual(state["spring_no"], 0)  # the first look only takes the counter

    def test_the_next_spring_makes_an_offer_of_3_different_ids(self):
        self.go_to_spring()
        state = self.contracts()
        self.assertEqual(len(state["offer"]), 3)
        self.assertEqual(len(set(state["offer"])), 3)
        self.assertEqual(state["spring_no"], state["season_no"])

    def test_one_offer_for_each_spring_counter_value(self):
        self.go_to_spring()
        first = self.contracts()["offer"]
        self.game.advance(20)
        self.assertEqual(self.contracts()["offer"], first)

    def test_no_offer_in_the_other_seasons(self):
        for value in (SUMMER, AUTUMN, WINTER):
            self.season(value)
            self.assertEqual(self.contracts()["offer"], [])

    def test_an_unpicked_offer_is_replaced_next_spring_with_no_penalty(self):
        self.set_influence(300)
        self.go_to_spring()
        first = self.contracts()["offer"]
        for value in (SUMMER, AUTUMN, WINTER):
            self.season(value)
        self.assertEqual(self.contracts()["offer"], first)  # stays open until the next spring
        self.season(SPRING)
        second = self.contracts()
        self.assertEqual(len(second["offer"]), 3)
        self.assertEqual(self.influence(), 300)
        self.assertEqual(second["failed"], 0)

    def test_offer_now_names_the_offer_without_a_spring(self):
        state = self.offer_now("clear_the_roads.keep_the_peace")
        self.assertEqual(state["offer"], ["clear_the_roads", "keep_the_peace"])

    def test_offer_now_refuses_an_unknown_id(self):
        answer = self.ask("liege_contracts_offer_now", ids="nope")
        self.assertFalse(answer["ok"])
        self.assertIn("unknown contract id", answer["error"])


class PickTests(ContractsTestCase):
    IDS = "timber_for_the_walls.clear_the_roads.keep_the_peace"

    def test_a_pick_activates_one_and_discards_the_others(self):
        self.offer_now(self.IDS)
        answer = self.pick("clear_the_roads")
        self.assertTrue(answer["ok"], answer)
        state = self.contracts()
        self.assertEqual(state["offer"], [])
        self.assertEqual(state["active"]["id"], "clear_the_roads")

    def test_a_pick_with_an_active_contract_is_refused(self):
        self.offer_now(self.IDS)
        self.pick("clear_the_roads")
        self.offer_now(self.IDS)
        answer = self.pick("keep_the_peace")
        self.assertFalse(answer["ok"])
        self.assertIn("already active", answer["error"])
        self.assertEqual(self.contracts()["active"]["id"], "clear_the_roads")

    def test_a_pick_outside_the_offer_is_refused(self):
        self.offer_now(self.IDS)
        answer = self.pick("feed_the_city")
        self.assertFalse(answer["ok"])
        self.assertIn("not in the offer", answer["error"])
        self.assertEqual(len(self.contracts()["offer"]), 3)

    def test_a_pick_with_no_offer_is_refused(self):
        answer = self.pick("clear_the_roads")
        self.assertFalse(answer["ok"])
        self.assertIn("no contracts", answer["error"])

    def test_the_tribute_command_is_gone(self):
        answer = self.ask("liege_send_tribute", amount=100)
        self.assertFalse(answer["ok"])
        self.assertIn("unknown", answer["error"].lower())


class CompleteTests(ContractsTestCase):
    def test_goods_are_taken_and_every_reward_is_paid(self):
        self.set_stock(TIMBER, 70)
        self.start("timber_for_the_walls")
        self.set_influence(10)
        silver = self.pawn.silver
        answer = self.complete()
        self.assertTrue(answer["ok"], answer)
        self.assertEqual(self.stock(TIMBER), 10)
        self.assertEqual(self.pawn.silver, silver + 100)
        self.assertEqual(self.influence(), 25)
        state = self.contracts()
        self.assertEqual((state["done"], state["failed"]), (1, 0))
        self.assertIsNone(state.get("active"))

    def test_an_incomplete_contract_is_refused_and_nothing_moves(self):
        self.set_stock(TIMBER, 59)
        self.start("timber_for_the_walls")
        silver = self.pawn.silver
        answer = self.complete()
        self.assertFalse(answer["ok"])
        self.assertIn("short by 1", answer["error"])
        self.assertEqual((self.stock(TIMBER), self.pawn.silver, self.influence()), (59, silver, 0))
        self.assertEqual(self.contracts()["active"]["id"], "timber_for_the_walls")

    def test_the_progress_follows_the_stock(self):
        self.set_stock(TIMBER, 20)
        self.start("timber_for_the_walls")
        self.assertEqual(self.contracts()["active"]["objectives"][0]["progress"], 20)
        self.set_stock(TIMBER, 45)
        self.assertEqual(self.contracts()["active"]["objectives"][0]["progress"], 65)
        self.assertTrue(self.contracts()["active"]["complete"])

    def test_a_shortage_at_the_take_refuses_and_changes_nothing_else(self):
        self.set_stock(TIMBER, 60)
        self.start("timber_for_the_walls")
        # The stock number says 60 but the store holds 40: the take finds 40 and puts them back.
        self.world.hide_goods(TIMBER, 20)
        answer = self.complete()
        self.assertFalse(answer["ok"])
        self.assertIn("could be taken", answer["error"])
        self.assertEqual(self.contracts()["active"]["id"], "timber_for_the_walls")
        self.assertEqual(self.contracts()["done"], 0)
        self.assertEqual(self.influence(), 0)

    def test_build_count_counts_finished_buildings_after_the_pick(self):
        self.start("build_a_storehouse")
        self.assertEqual(self.contracts()["active"]["objectives"][0]["progress"], 0)
        self.world.add_building(72, False)
        self.assertEqual(self.contracts()["active"]["objectives"][0]["progress"], 0)
        self.world.add_building(72, True)
        self.assertEqual(self.contracts()["active"]["objectives"][0]["progress"], 1)
        order = self.ask("bandits_state")["result"]["mod_order"]
        answer = self.complete()
        self.assertTrue(answer["ok"], answer)
        self.assertEqual(self.stock(17), 50)
        self.assertEqual(self.influence(), 10)
        self.assertEqual(self.ask("bandits_state")["result"]["mod_order"], min(100, order + 5))

    def test_a_goods_reward_without_a_storehouse_is_counted_and_the_others_are_paid(self):
        self.start("raise_the_levy")
        self.ask("liege_contracts_test_progress", index=1, value=2)
        self.world.remove_store()
        answer = self.complete()
        self.assertTrue(answer["ok"], answer)
        state = self.contracts()
        self.assertEqual(state["failed_rewards"], 1)
        self.assertEqual(self.influence(), 20)
        self.assertEqual(state["done"], 1)

    def test_a_tech_pick_reward_pays_or_is_counted(self):
        read = f"""
            local s = {FEATURE}.state
            local ok, value = pcall(function() return s:get("tech_picks_earned") end)
            return ok and value or -99
        """
        before = self.game.exec(read)
        self.start("keep_the_peace")
        self.ask("liege_contracts_test_progress", index=1, value=90)
        self.assertTrue(self.complete()["ok"])
        if before != -99:  # the tech tree has the pick state (change update-tech-tree-yearly-picks)
            self.assertEqual(self.game.exec(read), max(0, before) + 1)
            self.assertEqual(self.contracts()["failed_rewards"], 0)
        else:
            self.assertEqual(self.contracts()["failed_rewards"], 1)


class ProgressTests(ContractsTestCase):
    def test_hold_public_order_counts_days_and_resets(self):
        self.ask("bandits_set_order", value=80)
        self.start("keep_the_peace")
        self.calendar.daysTotal = self.calendar.daysTotal + 40
        self.game.advance(4)
        self.assertEqual(self.contracts()["active"]["objectives"][0]["progress"], 40)
        self.ask("bandits_set_order", value=30)
        self.calendar.daysTotal = self.calendar.daysTotal + 1
        self.game.advance(4)
        self.assertEqual(self.contracts()["active"]["objectives"][0]["progress"], 0)
        self.ask("bandits_set_order", value=80)
        self.calendar.daysTotal = self.calendar.daysTotal + 5
        self.game.advance(4)
        self.assertEqual(self.contracts()["active"]["objectives"][0]["progress"], 5)

    def test_kill_raiders_is_complete_at_the_target(self):
        self.start("clear_the_roads")
        self.ask("liege_contracts_test_progress", index=1, value=14)
        self.assertFalse(self.contracts()["active"]["complete"])
        self.ask("liege_contracts_test_progress", index=1, value=15)
        self.assertTrue(self.contracts()["active"]["complete"])

    def test_raiders_killed_counts_the_dead_of_tracked_raids(self):
        self.assertEqual(self.game.exec('return require("features.raid_behavior.init").raiders_killed()'), 0)

    def test_militia_squads_start_at_0(self):
        self.start("raise_the_levy")
        self.assertEqual(self.contracts()["active"]["objectives"][0]["progress"], 0)

    def test_the_test_progress_command_needs_an_active_contract(self):
        answer = self.ask("liege_contracts_test_progress", index=1, value=3)
        self.assertFalse(answer["ok"])
        self.assertIn("no contract is active", answer["error"])


class DeadlineTests(ContractsTestCase):
    def test_the_start_of_winter_fails_an_incomplete_contract(self):
        self.set_influence(700)
        self.start("raise_the_levy")
        for value in (SUMMER, AUTUMN):
            self.season(value)
            self.assertEqual(self.contracts()["active"]["id"], "raise_the_levy")
        self.season(WINTER)
        state = self.contracts()
        self.assertIsNone(state.get("active"))
        self.assertEqual((state["failed"], state["done"]), (1, 0))
        self.assertEqual(self.influence(), 200)

    def test_the_penalty_never_takes_the_influence_below_0(self):
        self.set_influence(100)
        self.start("raise_the_levy")
        for value in (SUMMER, AUTUMN, WINTER):
            self.season(value)
        self.assertEqual(self.influence(), 0)
        self.assertEqual(self.contracts()["failed"], 1)

    def test_a_changed_config_value_changes_the_penalty(self):
        self.game.exec('require("config").liege_contracts.fail_penalty = 120')
        self.set_influence(700)
        self.start("raise_the_levy")
        for value in (SUMMER, AUTUMN, WINTER):
            self.season(value)
        self.assertEqual(self.influence(), 580)

    def test_a_contract_with_met_objectives_at_the_deadline_pays(self):
        self.start("raise_the_levy")
        self.ask("liege_contracts_test_progress", index=1, value=2)
        for value in (SUMMER, AUTUMN, WINTER):
            self.season(value)
        state = self.contracts()
        self.assertEqual((state["done"], state["failed"]), (1, 0))
        self.assertEqual(self.influence(), 20)

    def test_a_contract_picked_in_winter_is_not_due_at_once(self):
        self.season(WINTER)
        self.start("raise_the_levy")
        self.game.advance(10)
        self.assertEqual(self.contracts()["active"]["id"], "raise_the_levy")

    def test_a_day_count_fails_at_the_day_not_at_winter(self):
        self.game.exec(f"""
            local contracts = {FEATURE}.contracts
            contracts.by_id.test_days = {{ id = "test_days", name = "Days", quote = "", weight = 1, duration = 120,
                objectives = {{ {{ type = "kill_raiders", amount = 99 }} }}, rewards = {{ {{ type = "influence", amount = 1 }} }} }}
        """)
        self.set_influence(900)
        self.offer_now("test_days")
        self.assertTrue(self.pick("test_days")["ok"])
        self.calendar.daysTotal = self.calendar.daysTotal + 119
        self.game.advance(4)
        self.assertEqual(self.contracts()["active"]["id"], "test_days")
        self.calendar.daysTotal = self.calendar.daysTotal + 1
        self.game.advance(4)
        state = self.contracts()
        self.assertIsNone(state.get("active"))
        self.assertEqual(state["failed"], 1)
        self.assertEqual(self.influence(), 400)


class StateTests(ContractsTestCase):
    def reload_state(self):
        self.game.exec(f"{FEATURE}.state:load()")

    def test_the_keys_are_written(self):
        self.start("raise_the_levy")
        keys = self.game.exec(f"""
            local state = {FEATURE}.state
            local out = {{}}
            for _, key in ipairs({{ "contracts_spring_no", "contracts_offer", "contracts_active", "contracts_start_day", "contracts_baseline",
                                   "contracts_progress", "contracts_done", "contracts_failed" }}) do out[#out + 1] = key .. "=" .. tostring(state:get(key)) end
            return table.concat(out, ";")
        """)
        self.assertIn("contracts_active=raise_the_levy", keys)
        self.assertIn("contracts_offer=;", keys)
        self.assertIn("contracts_baseline=o0-0.s-0", keys)
        self.assertIn("contracts_progress=o0-0", keys)

    def test_an_active_contract_survives_a_load(self):
        self.set_stock(TIMBER, 33)
        self.start("timber_for_the_walls")
        before = self.contracts()
        self.reload_state()
        self.game.advance(4)
        after = self.contracts()
        self.assertEqual(after["active"]["id"], "timber_for_the_walls")
        self.assertEqual(after["active"]["objectives"], before["active"]["objectives"])
        self.assertEqual(after["active"]["start_day"], before["active"]["start_day"])

    def test_an_offer_survives_a_load_and_is_not_drawn_again(self):
        for value in (SUMMER, AUTUMN, WINTER, SPRING):
            self.season(value)
        offer = self.contracts()["offer"]
        self.reload_state()
        self.game.advance(10)
        self.assertEqual(self.contracts()["offer"], offer)

    def test_a_removed_contract_id_is_dropped_with_no_penalty(self):
        self.set_influence(300)
        self.game.exec(f'{FEATURE}.state:set("contracts_active", "gone_id")')
        self.game.advance(5)
        state = self.contracts()
        self.assertIsNone(state.get("active"))
        self.assertEqual(self.influence(), 300)
        self.assertEqual(state["failed"], 0)

    def test_the_progress_text_uses_only_characters_that_modstate_allows(self):
        self.start("raise_the_levy")
        self.ask("liege_contracts_test_progress", index=1, value=2)
        self.assertEqual(self.game.exec(f'return {FEATURE}.state:get("contracts_progress")'), "o0-2")


class OldSaveTests(VassalsTestCase):
    """A save from before the change has only liege_influence and arms_last_day."""

    SAVED_TAGS = ("invasion:v=1", "invasion:liege_influence=40", "invasion:arms_last_day=12")

    def test_an_old_save_keeps_its_values_and_waits_for_the_next_spring(self):
        answer = self.ask("liege_contracts_state")["result"]
        self.assertEqual((answer["influence"], answer["offer"]), (40, []))
        self.assertEqual(self.ask("liege_state")["result"]["arms_last_day"], 12)
        self.game.advance(5)
        self.assertEqual(self.ask("liege_contracts_state")["result"]["offer"], [])


class WindowViewTests(ContractsTestCase):
    def view(self):
        answer = self.ask("liege_menu_state")
        self.assertTrue(answer["ok"], answer)
        return answer["result"]

    def test_with_no_offer_the_window_says_the_liege_sends_contracts_at_spring(self):
        view = self.view()["view"]
        self.assertEqual(view["cards"], [])
        self.assertIn("start of spring", view["empty_text"])

    def test_the_cards_show_name_items_and_penalty(self):
        self.offer_now("timber_for_the_walls.clear_the_roads.keep_the_peace")
        cards = self.view()["view"]["cards"]
        self.assertEqual([card["id"] for card in cards], ["timber_for_the_walls", "clear_the_roads", "keep_the_peace"])
        first = cards[0]
        self.assertEqual(first["name"], "Timber for the Walls")
        self.assertEqual(first["objectives"][0]["text"], "60 Wood")
        self.assertEqual([row["text"] for row in first["rewards"]], ["+15 influence", "+100 silver"])
        self.assertEqual(first["penalty"], "Fail: -500 influence")
        self.assertIn("Wood", first["objectives"][0]["tooltip"])
        self.assertEqual(len(cards[2]["rewards"]), 3)

    def test_the_active_panel_shows_progress_and_replaces_the_cards(self):
        self.set_stock(TIMBER, 12)
        self.start("timber_for_the_walls")
        view = self.view()["view"]
        self.assertEqual(view["cards"], [])
        self.assertEqual(view["active"]["lines"], ["Deliver: 12 / 60"])
        self.assertFalse(view["active"]["complete"])
        self.assertEqual(view["active"]["days_text"], "Ends when winter begins")

    def test_the_arms_text_stays(self):
        self.assertIn("Arms shipment: 200 silver", self.view()["wanted_texts"]["ArmsInfoText"])

    def test_the_influence_and_silver_texts_follow_the_values(self):
        self.set_stock(TIMBER, 60)
        self.start("timber_for_the_walls")
        silver = self.pawn.silver
        self.complete()
        wanted = self.view()["wanted_texts"]
        self.assertEqual(wanted["InfluenceText"], "Influence: 15")
        self.assertEqual(wanted["SilverText"], f"Silver: {silver + 100}")

    def test_open_menu_without_the_pak_gives_a_clear_message(self):
        answer = self.ask("liege_menu_open")
        self.assertTrue(answer["ok"], answer)
        self.assertFalse(answer["result"]["ok"])
        self.assertTrue(answer["result"]["error"])

    def test_close_without_an_open_menu_is_fine(self):
        self.assertTrue(self.ask("liege_menu_close")["result"]["ok"])

    def test_the_window_tick_is_not_faster_than_100_ms(self):
        source = (find_pack_mod() / "Scripts" / "features" / "liege_contracts" / "init.lua").read_text(encoding="utf-8")
        self.assertIn("math.max(100, menu_config.poll_ms)", source)


if __name__ == "__main__":
    unittest.main()
