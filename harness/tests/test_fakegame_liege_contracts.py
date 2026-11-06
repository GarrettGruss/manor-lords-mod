"""Tests for the feature liege_contracts of the pack mod in the fake game (changes update-liege-contracts-tiers, #533, and update-liege-contracts-tier-goods, #569).

They run the real Lua files. They do not prove how the real game behaves (see the test scenarios of the feature).
"""

import json
import pathlib
import unittest

import fakegame_path  # noqa: F401
from test_fakegame_modstate import find_pack_mod
from test_fakegame_tech_tree import TechTreeTestCase
from test_fakegame_vassals import VassalsTestCase

# Two storehouses (types 72 and 6) and a manor module (type 98). Goods are counted for the whole region, as getStockOfGood does.
WORLD = """
function(fg, region)
    local world = { stock = {}, buildings = {}, wealth = 0 }
    local function add_stock(kind, amount) world.stock[kind] = (world.stock[kind] or 0) + amount end
    local function make(btype, constructed, number)
        local b = fg.object("SMBuildingMaster", { Data = { bType = btype, constructed = constructed }, Inventory = fg.array({}, { wrap = false }) },
                            "/Game/Fake/Map.Map:PersistentLevel.SMBuildingMaster_" .. number)
        fg.set_method(b, "IsRubble", function() return false end)
        fg.set_method(b, "IsConstructed", function(self) return self.Data.constructed end)
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
    world.store2 = make(6, true, 6)
    world.manor = make(98, true, 98)
    world.buildings = { world.store, world.store2, world.manor }
    region.regionalWealth = 100
    fg.set_method(region, "GetBuildings", function() return world.buildings end)
    fg.set_method(region, "getStockOfGood", function(self, kind) return world.stock[kind] or 0 end)
    fg.set_method(region, "addRegionalWealth", function(self, amount) self.regionalWealth = self.regionalWealth + amount end)
    world.remove_store = function() world.buildings = { world.manor } end
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
# Goods of the tests (item ids of notes/item-ids.md of change update-liege-contracts-tiers)
PLANKS, BERRIES, CLAY, SALT, EEL, STONE = 17, 171, 146, 145, 32, 27
MUSHROOMS, HIDES, PELTS = 279, 3, 9
SAUSAGES, SMOKED_FISH, BREAD, TOOLS, ALE, CLOTHES = 320, 323, 172, 6, 28, 149
SWORDS, PLATE = 177, 293
FEATURE = 'require("features.liege_contracts.init")'
SMALL, MEDIUM, LARGE = "small", "medium", "large"
LETTER = {"small": "s", "medium": "m", "large": "l"}
# The cost codes of the saved text (rules.COST_CODE): the code stands in the place of the good id of a Large contract.
LOAN, FAMILIES, TRIBUTE = 1, 2, 3


def contract(tier, good, amount, kind, reward_good, reward_amount, done=0):
    """One contract in the saved text form: s-17-50-g-146-30-0. For a Large contract `good` is the cost code."""
    return f"{LETTER[tier]}-{good}-{amount}-{kind}-{reward_good}-{reward_amount}-{done}"


def offer_of(*contracts):
    return ".".join(contracts)


# Nine contracts: three for each tier. Rewards: g = goods, w = weapons, a = armor, l = law, k = King's Favour, s = law slot, p = relief promise.
NINE = offer_of(
    contract(SMALL, PLANKS, 50, "g", CLAY, 30), contract(SMALL, BERRIES, 70, "g", SALT, 25), contract(SMALL, EEL, 30, "g", STONE, 20),
    contract(MEDIUM, SAUSAGES, 24, "g", TOOLS, 15), contract(MEDIUM, SMOKED_FISH, 20, "g", ALE, 20), contract(MEDIUM, BREAD, 36, "g", CLOTHES, 10),
    contract(LARGE, FAMILIES, 3, "k", 0, 10), contract(LARGE, LOAN, 1, "l", 0, 1), contract(LARGE, TRIBUTE, 3, "p", 0, 5),
)
FAMILIES_ID, LOAN_ID, TRIBUTE_ID = "large-1", "large-2", "large-3"


def load_data():
    return json.loads((find_pack_mod() / "data" / "liege_contracts" / "contracts.json").read_text(encoding="utf-8"))


# Six families of three villagers, a King's Favour value, and two squads of the player (5: 32 men, 6: 36 men).
EXTRAS = """
function(fg, region, pawn)
    local extras = { families = {}, removed_squads = {} }
    local function rebuild()
        local live = {}
        for _, family in ipairs(extras.families) do
            if not family.gone then live[#live + 1] = family end
        end
        region.workerFamilies = fg.array(live, { wrap = false })
    end
    for number = 1, 6 do
        local family = { gone = false, dead_count = 0 }
        local members = {}
        for index = 1, 3 do
            local member = fg.object("VAMP_Villager", { dead = false }, "/Game/Fake/Map.Map:PersistentLevel.Member_" .. number .. "_" .. index)
            fg.set_method(member, "just_die", function(self)
                self.dead = true
                family.dead_count = family.dead_count + 1
                if family.dead_count == 3 then family.gone = true; rebuild() end
            end)
            members[index] = member
        end
        family.familyMembers = fg.array(members, { wrap = false })
        extras.families[number] = family
    end
    rebuild()
    pawn.kingsFavour = 0
    fg.set_method(pawn, "changeKingsFavour", function(self, amount) self.kingsFavour = self.kingsFavour + amount end)
    pawn.commandedSquads = fg.array({}, { wrap = false })
    extras.units = {}
    extras.add_squad = function(id, men, xp)
        fg.array_add(pawn.commandedSquads, { Value = id })
        for index = 1, men do
            extras.units[#extras.units + 1] = fg.object("SMUnit", { dead = false, assignedSquadID = { Value = id }, combatExperience = xp },
                "/Game/Fake/Map.Map:PersistentLevel.Unit_" .. id .. "_" .. index)
        end
    end
    fg.set_method(pawn, "addRemoveSquadRequest", function(self, handle)
        extras.removed_squads[#extras.removed_squads + 1] = handle.Value
        for _, unit in ipairs(extras.units) do
            if unit.assignedSquadID.Value == handle.Value then unit.dead = true end
        end
        local keep = {}
        for i = 1, #pawn.commandedSquads do
            local entry = pawn.commandedSquads[i]
            if entry.Value ~= handle.Value then keep[#keep + 1] = entry end
        end
        pawn.commandedSquads = fg.array(keep, { wrap = false })
    end)
    extras.add_squad(5, 32, 2)
    extras.add_squad(6, 36, 4)
    return extras
end
"""


class ContractsTestCase(TechTreeTestCase):
    STUB_BUILT_MANOR = False

    START_SEASON = SUMMER  # a game that starts in summer makes no offer until spring
    def setUp(self):
        super().setUp()
        self.world = self.game.lua.eval(WORLD)(self.game.fg, self.region)
        self.extras = self.game.lua.eval(EXTRAS)(self.game.fg, self.region, self.pawn)
        self.pawn.silver = 1000
        self.calendar.day = 100
        self.ask("invasion_set_level", kind="yearly", value=2)  # difficulty 1.0 (the base class sets level 1)

    def contracts(self):
        answer = self.ask("liege_contracts_state")
        self.assertTrue(answer["ok"], answer)
        return answer["result"]

    def offer_now(self, ids=None):
        answer = self.ask("liege_contracts_offer_now", **({"ids": ids} if ids else {}))
        self.assertTrue(answer["ok"], answer)
        return answer["result"]

    def fulfil(self, contract_id):
        return self.ask("liege_contract_fulfil", id=contract_id)

    def card(self, contract_id):
        return next(card for card in self.contracts()["contracts"] if card["id"] == contract_id)

    def set_stock(self, good, amount, store=None):
        self.game.lua.eval("function(store, good, amount) store:addToInventory({ Type = good, amt = amount }) end")(store or self.world.store, good, amount)

    def stock(self, good):
        return self.world.stock[good] or 0

    def season(self, value, days=91):
        """Move the calendar to a season so that invasion counts one season change."""
        self.calendar.daysTotal = self.calendar.daysTotal + days
        self.calendar.Season = value
        self.game.advance(6)

    def go_to_spring(self):
        for value in (SUMMER, AUTUMN, WINTER, SPRING):
            self.season(value)

    def influence(self):
        return self.ask("liege_state")["result"]["influence"]

    def set_influence(self, value):
        self.game.exec(f"{FEATURE}; require('features.liege_influence.init').state:set('liege_influence', {value})")

    def family_count(self):
        return self.game.exec('return require("features.liege_contracts.world").family_count()')

    def fill_slots(self):
        for _ in range(4):
            self.game.exec('require("features.laws_menu.init").laws_add_slot()')

    def vassals_pay(self, count=2):
        """The fake world has no vassal: the tribute feature says that `count` vassals pay."""
        self.game.exec(f'require("features.tribute.init").paying_vassals = function() return {count} end')

    def slots(self):
        return self.contracts()["law_slots"]


class SmokeTests(ContractsTestCase):
    def test_the_feature_loads_with_the_starter_table(self):
        state = self.contracts()
        self.assertEqual(state["offer"], [])
        self.assertEqual(state["contracts"], [])
        self.assertEqual(state["tiers"], {"small": {"used": 0, "limit": 1}, "medium": {"used": 0, "limit": 1}, "large": {"used": 0, "limit": 1}})


class LoaderTests(ContractsTestCase):
    GOOD_TIER = '{ requests = { { good = 1, weight = 1 } }, rewards = { { kind = "kings_favour", min = 5, max = 6 } } }'
    LARGE_TIER = '{ requests = { { cost = "send_families", min = 3, max = 3, weight = 1 } }, rewards = { { kind = "kings_favour", min = 5, max = 6 } } }'

    def build(self, small=None, extra="offer_per_tier = 1", version="3", large=None):
        tier = small or self.GOOD_TIER
        return self.game.exec(f"""
            local loader = require("features.liege_contracts.loader")
            local tier = {tier}
            local large = {large or self.LARGE_TIER}
            local ok, err = pcall(loader.build, {{ version = {version}, {extra}, tiers = {{ small = tier, medium = tier, large = large }} }})
            return ok and "ok" or tostring(err)
        """)

    def data(self):
        return load_data()

    def test_the_table_fields(self):
        data = self.data()
        self.assertEqual((data["version"], data["offer_per_tier"]), (3, 3))
        self.assertEqual(sorted(data["tiers"]), ["large", "medium", "small"])
        text = json.dumps(data)
        for word in ("duration", "penalty", "objectives", "envoy"):
            self.assertNotIn(word, text)
        for request in data["tiers"]["large"]["requests"]:
            self.assertEqual(sorted(request), ["cost", "max", "min", "weight"])
        for tier in ("small", "medium"):
            for request in data["tiers"][tier]["requests"]:
                self.assertEqual(sorted(request), ["good", "weight"])

    def test_the_starter_table_loads_with_the_pools_of_the_design(self):
        sizes = self.game.exec(f"""
            local c = {FEATURE}.contracts
            return #c.tiers.small.requests .. ":" .. #c.tiers.medium.requests .. ":" .. #c.tiers.large.requests .. ":" .. c.offer_per_tier
        """)
        self.assertEqual(sizes, "11:9:3:3")

    def test_small_and_medium_requests_are_the_goods_of_table_1(self):
        data = self.data()
        small = {r["good"] for r in data["tiers"]["small"]["requests"]}
        medium = {r["good"] for r in data["tiers"]["medium"]["requests"]}
        # 279 (mushrooms) is in the group of berries; pelts (9) are in the group of hides
        self.assertEqual(small, {171, 30, 32, 330, 16, 13, 216, 3, 220, 15, 17})
        self.assertEqual(medium, {320, 323, 35, 172, 170, 7, 4, 12, 148})

    def test_every_good_of_the_starter_table_has_a_name_and_is_an_item_row(self):
        data = self.data()
        goods = set()
        for tier in data["tiers"].values():
            goods.update(request["good"] for request in tier["requests"] if "good" in request)
            for reward in tier["rewards"]:
                goods.update(data["good_lists"].get(reward.get("goods"), []))
        self.assertEqual(sorted(goods - {int(key) for key in data["names"]}), [])
        for tier in data["tiers"].values():
            for request in tier["requests"]:
                self.assertGreater(request["weight"], 0)

    def test_the_reward_pools_follow_table_2(self):
        data = self.data()
        kinds = {name: {reward["kind"] for reward in tier["rewards"]} for name, tier in data["tiers"].items()}
        self.assertEqual(kinds, {"small": {"goods"}, "medium": {"goods"},
                                 "large": {"law", "kings_favour", "weapons", "armor", "law_slot", "relief_promise"}})
        lists = data["good_lists"]
        small = data["tiers"]["small"]["rewards"][0]
        self.assertEqual(sorted(lists[small["goods"]]), sorted([145, 14, 146, 11, 27]))
        medium = {tuple(sorted(lists[r["goods"]])) for r in data["tiers"]["medium"]["rewards"]}
        self.assertEqual(medium, {(6,), (28, 325, 327), (149,)})
        large = {r["kind"]: r for r in data["tiers"]["large"]["rewards"]}
        self.assertEqual(sorted(lists[large["weapons"]["goods"]]), sorted([177, 178, 133, 270, 271, 205, 206]))
        self.assertEqual(sorted(lists[large["armor"]["goods"]]), sorted([163, 164, 273, 293]))
        self.assertEqual((large["kings_favour"]["min"], large["kings_favour"]["max"]), (10, 10))
        self.assertEqual((large["relief_promise"]["min"], large["relief_promise"]["max"]), (5, 5))
        self.assertEqual((large["law_slot"]["min"], large["law_slot"]["max"]), (1, 1))
        for gone in ("regional_wealth", "silver", "tech_point", "influence"):
            self.assertNotIn(gone, json.dumps(data))

    def test_the_large_costs_are_the_owner_amounts(self):
        data = self.data()
        costs = {r["cost"]: (r["min"], r["max"]) for r in data["tiers"]["large"]["requests"]}
        # 1 squad, 3 families, 3 months of tribute (one season). No peasant loan and no herd (design decisions 9 and 10).
        self.assertEqual(costs, {"loan_units": (1, 1), "send_families": (3, 3), "tribute_season": (3, 3)})

    def groups(self, groups, requests="{ good = 1, weight = 1 }, { good = 2, weight = 1 }"):
        tier = "{ requests = { " + requests + " }, rewards = { { kind = \"kings_favour\", min = 5, max = 6 } } }"
        return self.build(small=tier, extra="offer_per_tier = 1, groups = " + groups)

    def test_a_group_table_loads(self):
        self.assertEqual(self.groups('{ { goods = { 1, 3 }, label = "a or b" } }'), "ok")

    def test_a_group_needs_two_goods(self):
        self.assertIn("group 1 needs the field 'goods' with at least 2 good ids", self.groups("{ { goods = { 1 } } }"))

    def test_a_good_in_two_groups_stops_the_load(self):
        self.assertIn("good 1 is in two groups", self.groups("{ { goods = { 1, 3 } }, { goods = { 1, 4 } } }"))

    def test_two_requests_of_one_group_in_a_tier_stop_the_load(self):
        self.assertIn("tier 'small' lists two requests of the same group", self.groups("{ { goods = { 1, 2 } } }"))

    def test_a_label_must_be_text(self):
        self.assertIn("field 'label' must be text", self.groups("{ { goods = { 1, 3 }, label = 5 } }"))

    def test_a_good_table_loads(self):
        self.assertEqual(self.build(), "ok")

    def test_an_unknown_kind_names_the_tier_and_the_kind(self):
        answer = self.build(self.GOOD_TIER.replace("kings_favour", "dance"))
        self.assertIn("tier 'small' reward 1", answer)
        self.assertIn("unknown kind 'dance'", answer)

    def test_the_removed_reward_kinds_are_unknown(self):
        for kind in ("regional_wealth", "silver", "tech_point", "influence"):
            self.assertIn(f"unknown kind '{kind}'", self.build(self.GOOD_TIER.replace("kings_favour", kind)))

    def test_an_unknown_cost_names_the_tier_and_the_cost(self):
        answer = self.build(large=self.LARGE_TIER.replace("send_families", "herd"))
        self.assertIn("tier 'large' request 1", answer)
        self.assertIn("unknown cost 'herd'", answer)

    def test_the_peasant_loan_is_not_a_cost(self):
        self.assertIn("unknown cost 'loan_peasants'", self.build(large=self.LARGE_TIER.replace("send_families", "loan_peasants")))

    def test_a_large_request_needs_a_cost_and_an_amount_range(self):
        self.assertIn("missing the field 'cost'", self.build(large=self.LARGE_TIER.replace('cost = "send_families", ', "")))
        self.assertIn("'min'", self.build(large=self.LARGE_TIER.replace("min = 3, ", "")))

    def test_a_missing_field_names_the_tier_and_the_field(self):
        answer = self.build(self.GOOD_TIER.replace("min = 5, ", ""))
        self.assertIn("tier 'small'", answer)
        self.assertIn("'min'", answer)

    def test_a_weight_of_0_stops_the_load(self):
        answer = self.build(self.GOOD_TIER.replace("weight = 1", "weight = 0"))
        self.assertIn("tier 'small'", answer)
        self.assertIn("'weight'", answer)

    def test_fewer_requests_than_the_offer_per_tier_stop_the_load(self):
        self.assertIn("tier 'small' has 1 requests, but offer_per_tier is 3", self.build(extra="offer_per_tier = 3"))

    def test_a_goods_reward_without_goods_stops_the_load(self):
        answer = self.build(self.GOOD_TIER.replace('"kings_favour"', '"goods"'))
        self.assertIn("needs the field 'goods'", answer)

    def test_an_armor_reward_needs_a_list_too(self):
        self.assertIn("needs the field 'goods'", self.build(self.GOOD_TIER.replace('"kings_favour"', '"armor"')))

    def test_the_old_version_is_refused(self):
        self.assertIn("'version' must be 3", self.build(version="2"))


class FormulaTests(ContractsTestCase):
    def amount(self, base, weight, difficulty):
        return self.game.exec(f'return require("features.liege_contracts.rules").request_amount({base}, {weight}, {difficulty})')

    def test_plate_armor_at_two_difficulties(self):
        self.assertEqual(self.amount(15, 0.35, 1.25), 7)  # 6.56
        self.assertEqual(self.amount(15, 0.35, 1.0), 5)   # 5.25

    def test_the_amount_is_at_least_1(self):
        self.assertEqual(self.amount(1, 0.1, 0.75), 1)

    def test_a_half_rounds_up(self):
        self.assertEqual(self.amount(10, 0.25, 1.0), 3)   # 2.5
        self.assertEqual(self.amount(50, 1.4, 1.0), 70)

    def test_the_difficulty_comes_from_the_yearly_raid_level(self):
        for level, wanted in ((0, 1.0), (1, 0.75), (2, 1.0), (3, 1.25)):
            self.ask("invasion_set_level", kind="yearly", value=level)
            self.assertEqual(self.contracts()["difficulty"], wanted, level)

    def test_a_drawn_amount_follows_base_weight_and_difficulty(self):
        self.ask("invasion_set_level", kind="yearly", value=3)
        self.go_to_spring()
        for card in self.contracts()["contracts"]:
            self.assertEqual(card["amount"], self.expected(card), card)

    def expected(self, card):
        data = load_data()
        if card["tier"] == LARGE:
            return max(1, int(next(r["min"] for r in data["tiers"]["large"]["requests"] if r["cost"] == card["cost"]) * 1.25 + 0.5 + 1e-9))
        weight = next(r["weight"] for r in data["tiers"][card["tier"]]["requests"] if r["good"] == card["good"])
        base = {"small": 50, "medium": 30}[card["tier"]]
        return max(1, int(base * weight * 1.25 + 0.5 + 1e-9))

    def cost_amount(self, amount, difficulty):
        return self.game.exec(f'return require("features.liege_contracts.rules").cost_amount({amount}, {difficulty})')

    def test_a_large_cost_scales_with_the_difficulty_factors(self):
        # easy 0.75, medium 1.0, hard 1.25, rounded half up (owner decision 2026-11-05)
        self.assertEqual([self.cost_amount(3, d) for d in (0.75, 1.0, 1.25)], [2, 3, 4])   # 2.25, 3, 3.75
        self.assertEqual([self.cost_amount(1, d) for d in (0.75, 1.0, 1.25)], [1, 1, 1])   # a squad and 1 stay 1
        self.assertEqual(self.cost_amount(0, 1.0), 1)

    def test_the_cost_of_a_drawn_large_contract_follows_the_level(self):
        for level, families in ((1, 2), (2, 3), (3, 4)):
            self.setUp()
            self.ask("invasion_set_level", kind="yearly", value=level)
            self.game.exec("math.randomseed(3)")
            self.go_to_spring()
            costs = {card["cost"]: card["amount"] for card in self.contracts()["contracts"] if card["tier"] == LARGE}
            self.assertEqual(costs["send_families"], families, level)
            self.assertEqual(costs["loan_units"], 1, level)

    def test_a_changed_config_value_changes_the_amount(self):
        self.game.exec('local c = require("config").liege_contracts; c.base.small = 100; c.base.medium = 1; c.weight[17] = 2')
        self.go_to_spring()
        for card in self.contracts()["contracts"]:
            if card["tier"] == SMALL and card["good"] == PLANKS:
                self.assertEqual(card["amount"], 200)
            if card["tier"] == MEDIUM:
                self.assertLessEqual(card["amount"], 2)


class DrawTests(ContractsTestCase):
    def draw(self, seed):
        self.game.exec(f"math.randomseed({seed})")
        self.go_to_spring()
        return self.contracts()["contracts"]

    def test_a_spring_draw_holds_three_different_contracts_in_each_tier(self):
        for seed in (1, 2, 3, 4, 5):
            self.setUp()
            cards = self.draw(seed)
            self.assertEqual(len(cards), 9)
            for tier in (SMALL, MEDIUM, LARGE):
                keys = [card.get("cost") or card.get("good") for card in cards if card["tier"] == tier]
                self.assertEqual(len(keys), 3)
                self.assertEqual(len(set(keys)), 3)

    def test_a_request_belongs_to_the_pool_of_its_tier(self):
        data = load_data()
        for card in self.draw(7):
            keys = [r.get("cost") or r["good"] for r in data["tiers"][card["tier"]]["requests"]]
            self.assertIn(card.get("cost") or card.get("good"), keys)
            self.assertEqual(card.get("cost") is not None, card["tier"] == LARGE)

    def test_rewards_follow_the_tier_and_never_repeat_the_request_good(self):
        allowed = {SMALL: {"goods"}, MEDIUM: {"goods"}, LARGE: {"law", "kings_favour", "weapons", "armor", "law_slot", "relief_promise"}}
        ranges = {"goods": {SMALL: (20, 40), MEDIUM: (10, 30)}, "weapons": {LARGE: (20, 40)}, "armor": {LARGE: (15, 30)}, "law": {LARGE: (1, 1)},
                  "kings_favour": {LARGE: (10, 10)}, "law_slot": {LARGE: (1, 1)}, "relief_promise": {LARGE: (5, 5)}}
        for seed in range(1, 25):
            self.setUp()
            for card in self.draw(seed):
                reward = card["reward"]
                self.assertIn(reward["kind"], allowed[card["tier"]])
                low, high = ranges[reward["kind"]][card["tier"]]
                self.assertTrue(low <= reward["amount"] <= high, card)
                if reward["kind"] in ("goods", "weapons", "armor"):
                    self.assertNotEqual(reward["good"], card.get("good"))

    def test_small_rewards_are_vassal_goods_and_medium_rewards_are_tools_drinks_or_clothes(self):
        data = load_data()
        lists = data["good_lists"]
        small = set(lists["vassal"])
        medium = set(lists["tools"]) | set(lists["drinks"]) | set(lists["clothes"])
        seen = set()
        for seed in range(1, 25):
            self.setUp()
            for card in self.draw(seed):
                if card["reward"]["kind"] == "goods":
                    seen.add(card["tier"])
                    self.assertIn(card["reward"]["good"], small if card["tier"] == SMALL else medium)
        self.assertEqual(seen, {SMALL, MEDIUM})

    def test_the_draw_gives_different_offers(self):
        first = [(card.get("cost") or card.get("good")) for card in self.draw(1)]
        self.setUp()
        second = [(card.get("cost") or card.get("good")) for card in self.draw(99)]
        self.assertNotEqual(first, second)

    ALL_LAWS = 'local out = {}; for _, l in ipairs(require("features.tech_tree.init").tree.laws) do out[#out + 1] = l.id end; return table.concat(out, ",")'

    def unlock_every_law(self):
        for law in self.game.exec(self.ALL_LAWS).split(","):
            self.game.exec(f'require("features.laws_menu.init").laws_unlock("{law}", "test")')

    def test_the_law_reward_is_not_drawn_when_every_law_is_unlocked(self):
        seen = set()
        for seed in range(1, 40):
            self.setUp()
            self.unlock_every_law()
            seen.update(card["reward"]["kind"] for card in self.draw(seed) if card["tier"] == LARGE)
        self.assertNotIn("law", seen)
        self.assertTrue(seen)

    def test_the_law_reward_is_drawn_when_laws_are_locked(self):
        seen = set()
        for seed in range(1, 40):
            self.setUp()
            seen.update(card["reward"]["kind"] for card in self.draw(seed) if card["tier"] == LARGE)
        self.assertIn("law", seen)

    def test_the_law_slot_reward_is_not_drawn_at_the_cap(self):
        seen = set()
        for seed in range(1, 40):
            self.setUp()
            self.fill_slots()
            self.assertEqual(self.slots(), 5)
            seen.update(card["reward"]["kind"] for card in self.draw(seed) if card["tier"] == LARGE)
        self.assertNotIn("law_slot", seen)

    def test_the_law_slot_reward_is_drawn_below_the_cap(self):
        seen = set()
        for seed in range(1, 40):
            self.setUp()
            seen.update(card["reward"]["kind"] for card in self.draw(seed) if card["tier"] == LARGE)
        self.assertIn("law_slot", seen)

    def test_a_loan_is_not_drawn_when_loaning_is_off(self):
        self.game.exec('require("config").liege_contracts.loan_enabled = false')
        self.game.exec("math.randomseed(1)")
        answer = self.game.exec(f"""
            local rules = require("features.liege_contracts.rules")
            local data = {FEATURE}.contracts
            local offer, why = rules.draw_offer({{ tiers = data.tiers, base = {{ small = 1, medium = 1 }}, difficulty = 1,
                cost_allowed = function(cost) return cost ~= "loan_units" end }}, 3, math.random)
            return offer == nil and why or "drawn"
        """)
        self.assertIn("tier large has fewer than 3", answer)

    def test_a_draw_of_more_than_the_pool_fails(self):
        self.assertIn("fewer than", self.game.exec(f"""
            local rules = require("features.liege_contracts.rules")
            local data = {FEATURE}.contracts
            local offer, why = rules.draw_offer({{ tiers = data.tiers, base = {{ small = 1, medium = 1 }}, difficulty = 1 }}, 20, math.random)
            return offer == nil and why or "drawn"
        """))


class SpringTests(ContractsTestCase):
    def test_a_new_game_makes_no_offer_at_the_first_poll(self):
        self.game.advance(5)
        state = self.contracts()
        self.assertEqual(state["offer"], [])
        self.assertEqual(state["spring_no"], 0)  # the first look only takes the counter

    def test_the_next_spring_makes_nine_contracts_and_resets_the_counts(self):
        self.go_to_spring()
        state = self.contracts()
        self.assertEqual(len(state["offer"]), 9)
        self.assertEqual(state["offer"], [f"{tier}-{n}" for tier in (SMALL, MEDIUM, LARGE) for n in (1, 2, 3)])
        self.assertEqual(state["spring_no"], state["season_no"])
        self.assertTrue(all(row["used"] == 0 for row in state["tiers"].values()))

    def test_one_offer_for_each_spring_counter_value(self):
        self.go_to_spring()
        first = self.contracts()["offer_text"]
        self.game.advance(20)
        self.assertEqual(self.contracts()["offer_text"], first)

    def test_no_offer_in_the_other_seasons(self):
        for value in (SUMMER, AUTUMN, WINTER):
            self.season(value)
            self.assertEqual(self.contracts()["offer"], [])

    def test_the_offer_is_made_with_or_without_a_manor(self):
        self.world.manor.Data.constructed = False
        self.go_to_spring()
        self.assertEqual(len(self.contracts()["offer"]), 9)

    def test_a_game_that_starts_in_summer_makes_no_offer_until_spring(self):
        self.season(SUMMER)
        self.game.advance(10)
        state = self.contracts()
        self.assertEqual(state["offer"], [])
        self.assertIn("start of spring", state["notice_text"])
        for value in (AUTUMN, WINTER):
            self.season(value)
            self.assertEqual(self.contracts()["offer"], [])
        self.season(SPRING)
        self.assertEqual(len(self.contracts()["offer"]), 9)

    def test_offer_now_names_the_offer_without_a_spring(self):
        state = self.offer_now(NINE)
        self.assertEqual(len(state["offer"]), 9)
        self.assertEqual(state["contracts"][0]["requirement"], "Deliver 50 planks")
        self.assertEqual(state["contracts"][6]["requirement"], "Cost: 3 families, for good")

    def test_offer_now_without_ids_draws(self):
        self.assertEqual(len(self.offer_now()["offer"]), 9)

    def test_offer_now_refuses_an_unknown_good(self):
        answer = self.ask("liege_contracts_offer_now", ids=contract(SMALL, 999, 5, "k", 0, 5))
        self.assertFalse(answer["ok"])
        self.assertIn("unknown contract", answer["error"])


class FirstSpringTests(ContractsTestCase):
    START_SEASON = SPRING  # a new game starts on day 61 in spring

    def test_a_new_game_in_spring_is_dealt_the_offer_at_the_first_poll(self):
        self.game.advance(5)
        state = self.contracts()
        self.assertEqual(len(state["offer"]), 9)
        self.assertEqual(state["spring_no"], state["season_no"])

    def test_a_load_in_the_same_spring_does_not_deal_again(self):
        self.game.advance(5)
        offer = self.contracts()["offer_text"]
        self.game.exec(f"{FEATURE}.state:load()")
        self.game.advance(10)
        self.assertEqual(self.contracts()["offer_text"], offer)

    def test_a_game_in_spring_with_no_state_is_dealt_once(self):
        self.game.advance(5)
        first = self.contracts()["offer_text"]
        self.game.advance(30)
        self.assertEqual(self.contracts()["offer_text"], first)


class FulfilTests(ContractsTestCase):
    def setUp(self):
        super().setUp()
        self.offer_now(NINE)

    def test_a_fulfilment_takes_the_goods_and_pays_the_reward(self):
        self.set_stock(PLANKS, 60)
        before = self.stock(CLAY)
        answer = self.fulfil("small-1")
        self.assertTrue(answer["ok"], answer)
        self.assertEqual(self.stock(PLANKS), 10)
        self.assertEqual(self.stock(CLAY) - before, 30)
        state = self.contracts()
        self.assertEqual((state["done"], state["tiers"]["small"]["used"], state["failed_rewards"]), (1, 1, 0))
        self.assertTrue(self.card("small-1")["done"])

    def test_a_medium_contract_pays_tools(self):
        self.set_stock(SAUSAGES, 24)
        self.assertTrue(self.fulfil("medium-1")["ok"])
        self.assertEqual((self.stock(SAUSAGES), self.stock(TOOLS)), (0, 15))

    def test_a_weapons_reward_adds_the_weapons(self):
        self.offer_now(offer_of(contract(LARGE, FAMILIES, 3, "w", SWORDS, 25)))
        self.assertTrue(self.fulfil("large-1")["ok"])
        self.assertEqual(self.stock(SWORDS), 25)
        self.assertEqual(self.family_count(), 3)

    def test_an_armor_reward_adds_the_armor(self):
        self.offer_now(offer_of(contract(LARGE, FAMILIES, 3, "a", PLATE, 16)))
        self.assertTrue(self.fulfil("large-1")["ok"])
        self.assertEqual(self.stock(PLATE), 16)

    def test_goods_are_taken_from_any_storehouse(self):
        self.set_stock(PLANKS, 20)
        self.set_stock(PLANKS, 40, self.world.store2)
        self.assertTrue(self.fulfil("small-1")["ok"])
        self.assertEqual(self.stock(PLANKS), 10)

    def test_not_enough_goods_is_refused_with_the_missing_amount_and_nothing_moves(self):
        self.set_stock(PLANKS, 45)
        answer = self.fulfil("small-1")
        self.assertFalse(answer["ok"])
        self.assertIn("5 more needed", answer["error"])
        self.assertEqual((self.stock(PLANKS), self.stock(CLAY)), (45, 0))
        self.assertEqual(self.contracts()["done"], 0)

    def test_the_tier_limit_stops_a_second_contract_of_the_tier(self):
        self.set_stock(PLANKS, 50)
        self.set_stock(EEL, 30)
        self.assertTrue(self.fulfil("small-1")["ok"])
        answer = self.fulfil("small-3")
        self.assertFalse(answer["ok"])
        self.assertIn("limit of 1", answer["error"])
        self.assertEqual(self.stock(EEL), 30)

    def test_the_other_tiers_are_not_affected_by_a_full_tier(self):
        self.set_stock(PLANKS, 50)
        self.set_stock(SMOKED_FISH, 20)
        self.assertTrue(self.fulfil("small-1")["ok"])
        self.assertTrue(self.fulfil("medium-2")["ok"])
        state = self.contracts()
        self.assertEqual((state["tiers"]["small"]["used"], state["tiers"]["medium"]["used"], state["tiers"]["large"]["used"]), (1, 1, 0))

    def test_a_changed_limit_in_the_config_allows_more(self):
        self.game.exec('require("config").liege_contracts.tier_limits.small = 2')
        self.set_stock(PLANKS, 50)
        self.set_stock(EEL, 30)
        self.assertTrue(self.fulfil("small-1")["ok"])
        self.assertTrue(self.fulfil("small-3")["ok"])
        self.assertEqual(self.contracts()["tiers"]["small"], {"used": 2, "limit": 2})

    def test_a_fulfilled_contract_cannot_be_fulfilled_again(self):
        self.set_stock(PLANKS, 120)
        self.game.exec('require("config").liege_contracts.tier_limits.small = 3')
        self.assertTrue(self.fulfil("small-1")["ok"])
        answer = self.fulfil("small-1")
        self.assertFalse(answer["ok"])
        self.assertIn("already fulfilled", answer["error"])

    def test_a_contract_that_is_not_in_the_offer_is_refused(self):
        answer = self.fulfil("small-9")
        self.assertFalse(answer["ok"])
        self.assertIn("not in the offer", answer["error"])

    def test_a_shortage_at_the_take_refuses_and_changes_nothing_else(self):
        self.set_stock(PLANKS, 50)
        # The stock number says 50 but the store holds 30: the take finds 30 and puts them back.
        self.world.hide_goods(PLANKS, 20)
        self.world.stock[PLANKS] = 50
        answer = self.fulfil("small-1")
        self.assertFalse(answer["ok"])
        self.assertIn("could be taken", answer["error"])
        self.assertEqual(self.contracts()["done"], 0)

    def test_a_goods_reward_without_a_storehouse_is_counted_and_the_contract_still_counts(self):
        self.set_stock(PLANKS, 50)
        self.game.exec('require("features.liege_contracts.world").add_goods = function() return nil, "no storehouse" end')
        answer = self.fulfil("small-1")
        self.assertTrue(answer["ok"], answer)
        state = self.contracts()
        self.assertEqual((state["failed_rewards"], state["done"]), (1, 1))

    def test_a_failed_reward_is_not_retried(self):
        self.set_stock(PLANKS, 50)
        self.game.exec('require("features.liege_contracts.world").add_goods = function() return nil, "no storehouse" end')
        self.fulfil("small-1")
        self.game.advance(10)
        self.assertEqual(self.contracts()["failed_rewards"], 1)


class InterchangeableGoodsTests(ContractsTestCase):
    """Change update-contract-interchangeable-goods (#589): hides and pelts, berries and mushrooms stand for each other."""

    def setUp(self):
        super().setUp()
        self.offer_now(offer_of(contract(SMALL, BERRIES, 40, "g", SALT, 25), contract(SMALL, HIDES, 20, "g", CLAY, 25), contract(SMALL, EEL, 30, "g", STONE, 20)))

    def test_the_card_names_both_goods_and_the_storage_adds_them(self):
        self.set_stock(BERRIES, 25)
        self.set_stock(MUSHROOMS, 20)
        card = self.card("small-1")
        self.assertEqual(card["requirement"], "Deliver 40 berries or mushrooms")
        self.assertEqual(card["have"], "In storage: 45 / 40")
        self.assertTrue(card["enabled"], card)
        self.assertEqual(self.card("small-2")["requirement"], "Deliver 20 hides or pelts")

    def test_the_missing_amount_counts_both_goods(self):
        self.set_stock(PELTS, 5)
        self.set_stock(HIDES, 10)
        card = self.card("small-2")
        self.assertEqual((card["have"], card["enabled"], card["reason"]), ("In storage: 15 / 20", False, "5 more needed"))

    def test_fulfil_takes_the_larger_stock_first(self):
        self.set_stock(BERRIES, 25)
        self.set_stock(MUSHROOMS, 30)
        self.assertTrue(self.fulfil("small-1")["ok"])
        self.assertEqual((self.stock(MUSHROOMS), self.stock(BERRIES)), (0, 15))

    def test_a_good_alone_can_pay(self):
        self.set_stock(PELTS, 20)
        self.assertTrue(self.fulfil("small-2")["ok"])
        self.assertEqual((self.stock(PELTS), self.stock(HIDES)), (0, 0))

    def test_a_short_take_puts_the_units_back(self):
        self.set_stock(BERRIES, 25)
        self.set_stock(MUSHROOMS, 30)
        self.world.hide_goods(MUSHROOMS, 10)  # the count says 30, the stores hold 20
        before = (self.stock(BERRIES), self.stock(MUSHROOMS))
        answer = self.fulfil("small-1")
        self.assertFalse(answer["ok"], answer)
        self.assertEqual((self.stock(BERRIES), self.stock(MUSHROOMS)), before)
        self.assertFalse(self.card("small-1")["done"])

    def test_a_saved_contract_for_a_group_member_still_loads(self):
        self.offer_now(offer_of(contract(SMALL, MUSHROOMS, 40, "g", SALT, 25), contract(SMALL, PELTS, 20, "g", CLAY, 25), contract(SMALL, EEL, 30, "g", STONE, 20)))
        self.assertEqual(self.card("small-1")["requirement"], "Deliver 40 berries or mushrooms")
        self.assertEqual(self.card("small-2")["requirement"], "Deliver 20 hides or pelts")

    def test_an_offer_never_holds_a_group_twice_or_pays_a_group_good(self):
        data = load_data()
        groups = [set(g["goods"]) for g in data["groups"]]
        for seed in range(1, 31):
            self.game.exec(f"math.randomseed({seed})")
            self.go_to_spring()
            cards = self.contracts()["contracts"]
            for group in groups:
                self.assertLessEqual(len([c for c in cards if c["tier"] == SMALL and c.get("good") in group]), 1)
            for card in cards:
                if card.get("good"):
                    group = next((g for g in groups if card["good"] in g), {card["good"]})
                    self.assertNotIn(card["reward"].get("good"), group)

    def test_the_starter_groups_are_the_two_pairs_and_every_good_has_a_name(self):
        data = load_data()
        self.assertEqual(sorted(sorted(g["goods"]) for g in data["groups"]), [[3, 9], [171, 279]])
        for group in data["groups"]:
            for good in group["goods"]:
                self.assertIn(str(good), data["names"])


class LargeCostTests(ContractsTestCase):
    """The three costs of a Large contract and what they need."""

    def setUp(self):
        super().setUp()
        self.offer_now(NINE)
        self.game.exec('require("config").liege_contracts.tier_limits.large = 3')
        self.vassals_pay(2)

    def test_sending_families_removes_them_for_good_and_pays_the_reward(self):
        self.assertEqual(self.family_count(), 6)
        answer = self.fulfil(FAMILIES_ID)
        self.assertTrue(answer["ok"], answer)
        self.assertEqual(self.family_count(), 3)
        self.assertEqual(self.pawn.kingsFavour, 10)
        self.assertEqual((self.contracts()["done"], self.contracts()["failed_rewards"]), (1, 0))

    def test_the_families_cost_leaves_one_family(self):
        for needed, ok in ((3, False), (4, True)):  # 3 families to send, 1 must stay: 4 families are needed
            self.setUp()
            self.game.exec('local fam = require("features.liege_contracts.world"); fam.family_count = function() return %d end' % needed)
            self.assertEqual(self.fulfil(FAMILIES_ID)["ok"], ok, needed)

    def test_too_few_families_refuse_with_the_missing_amount_and_nothing_moves(self):
        self.game.exec('require("features.liege_contracts.world").family_count = function() return 3 end')
        answer = self.fulfil(FAMILIES_ID)
        self.assertFalse(answer["ok"])
        self.assertIn("1 more family needed (1 must stay)", answer["error"])
        self.assertEqual((self.pawn.kingsFavour, self.contracts()["done"]), (0, 0))
        self.assertFalse(self.card(FAMILIES_ID)["enabled"])
        self.assertTrue(self.card(FAMILIES_ID)["short"])

    def test_the_card_of_a_cost_shows_what_the_player_has(self):
        card = self.card(FAMILIES_ID)
        self.assertEqual((card["requirement"], card["have"], card["reward_text"]), ("Cost: 3 families, for good", "Families: 6", "+10 King's Favour"))
        self.assertEqual(self.card(LOAN_ID)["requirement"], "Cost: 1 squad for 60 days")
        self.assertEqual(self.card(TRIBUTE_ID)["requirement"], "Cost: tribute for 3 months")
        self.assertEqual((self.card(LOAN_ID)["have"], self.card(TRIBUTE_ID)["have"]), ("Squads: 2", "Vassals: 2"))

    def test_a_cost_card_shows_no_storage_text(self):
        for number, card in enumerate(c for c in self.contracts()["contracts"] if c["tier"] == LARGE):
            self.assertIsNone(card.get("stock"), number)
            self.assertNotIn("In storage", card["have"])

    def test_the_tribute_cost_pauses_the_tribute_for_three_months(self):
        answer = self.fulfil(TRIBUTE_ID)
        self.assertTrue(answer["ok"], answer)
        self.assertEqual(self.skip_months(), 3)
        self.assertEqual(self.relief_bonus(), 5)

    def test_the_tribute_cost_needs_a_vassal(self):
        self.vassals_pay(0)
        answer = self.fulfil(TRIBUTE_ID)
        self.assertFalse(answer["ok"])
        self.assertIn("no vassal pays tribute", answer["error"])
        self.assertEqual((self.skip_months(), self.relief_bonus()), (0, 0))

    def skip_months(self):
        return self.game.exec('return require("features.tribute.init").state:get("tribute_skip_months")')

    def relief_bonus(self):
        return self.contracts()["relief_bonus_squads"]

    def test_a_squad_loan_removes_the_biggest_squad_and_writes_the_record(self):
        self.game.exec("local world = require('features.liege_contracts.world'); world.current_day = function() return 100 end")
        answer = self.fulfil(LOAN_ID)
        self.assertTrue(answer["ok"], answer)
        self.assertEqual(list(self.extras.removed_squads.values()), [6])  # 36 men: the retinue squad
        state = self.contracts()
        self.assertEqual(state["loans_text"], "retinue_tier1-36-4-160")
        self.assertEqual((state["loans_started"], state["done"]), (1, 1))
        self.assertEqual(state["law_slots"], 1)

    def test_a_squad_loan_pays_a_law(self):
        self.fulfil(LOAN_ID)
        granted = self.game.exec('return table.concat(require("features.tech_tree.init").granted_laws(), ",")')
        self.assertNotEqual(granted, "")
        self.assertIn("Contract: Large 2", self.game.exec(f'return require("features.tech_tree.init").law_source("{granted}")'))

    def test_the_loan_squad_returns_after_60_days_with_the_same_template(self):
        self.game.exec("""
            local world = require('features.liege_contracts.world')
            now = 100
            world.current_day = function() return now end
            spawned = {}
            world.spawn_squad = function(template, experience) spawned[#spawned + 1] = template .. ":" .. experience; return 21 end
        """)
        self.fulfil(LOAN_ID)
        self.game.exec("now = 159")
        self.game.advance(5)
        self.assertEqual(self.game.exec('return #spawned'), 0)
        self.game.exec("now = 160")
        self.game.advance(5)
        self.assertEqual(self.game.exec('return table.concat(spawned, ",")'), "retinue_tier1:4")
        state = self.contracts()
        self.assertEqual((state["loans_text"], state["loans_returned"]), ("", 1))
        self.game.advance(10)
        self.assertEqual(self.game.exec('return #spawned'), 1)  # once

    def test_a_loan_record_survives_a_save_and_a_load(self):
        self.game.exec("""
            local world = require('features.liege_contracts.world')
            now = 100
            world.current_day = function() return now end
            spawned = {}
            world.spawn_squad = function(template, experience) spawned[#spawned + 1] = template; return 21 end
        """)
        self.fulfil(LOAN_ID)
        self.game.exec(f"{FEATURE}.state:load()")
        self.assertEqual(self.contracts()["loans_text"], "retinue_tier1-36-4-160")
        self.game.exec("now = 200")
        self.game.advance(5)
        self.assertEqual(self.game.exec('return table.concat(spawned, ",")'), "retinue_tier1")

    def test_the_test_command_makes_a_loan_due_now(self):
        self.game.exec("""
            local world = require('features.liege_contracts.world')
            now = 100
            world.current_day = function() return now end
            spawned = 0
            world.spawn_squad = function() spawned = spawned + 1; return 21 end
        """)
        self.fulfil(LOAN_ID)
        answer = self.ask("liege_contracts_loans_due_now")
        self.assertTrue(answer["ok"], answer)
        self.game.advance(5)
        self.assertEqual((self.game.exec("return spawned"), self.contracts()["loans_text"]), (1, ""))

    def test_a_failed_return_keeps_the_record_and_tries_again(self):
        self.game.exec("""
            local world = require('features.liege_contracts.world')
            now = 100
            world.current_day = function() return now end
            attempts = 0
            world.spawn_squad = function() attempts = attempts + 1; if attempts < 3 then return nil, "no player position" end return 21 end
        """)
        self.fulfil(LOAN_ID)
        self.game.exec("now = 170")
        self.game.advance(3)
        self.assertEqual(self.contracts()["loans_text"], "retinue_tier1-36-4-160")
        self.game.advance(8)
        self.assertEqual(self.game.exec("return attempts"), 3)
        self.assertEqual(self.contracts()["loans_text"], "")

    def test_a_squad_of_an_unknown_size_cannot_be_loaned(self):
        self.game.exec("""
            local world = require('features.liege_contracts.world')
            world.player_squads = function() return { { id = 9, men = 50, experience = 0 } } end
        """)
        answer = self.fulfil(LOAN_ID)
        self.assertFalse(answer["ok"])
        self.assertIn("the squad type is not known", answer["error"])
        self.assertEqual((self.contracts()["done"], self.contracts()["loans_text"]), (0, ""))

    def test_a_squad_with_a_known_template_keeps_it(self):
        self.game.exec("""
            local world = require('features.liege_contracts.world')
            world.player_squads = function() return { { id = 9, men = 50, experience = 7 } } end
            world.known_template = function() return "Brigands" end
            world.remove_squad = function() return true end
        """)
        self.assertTrue(self.fulfil(LOAN_ID)["ok"])
        self.assertEqual(self.contracts()["loans_text"].split("-")[0], "Brigands")

    def test_the_loan_needs_a_squad(self):
        self.game.exec("require('features.liege_contracts.world').player_squads = function() return {} end")
        answer = self.fulfil(LOAN_ID)
        self.assertFalse(answer["ok"])
        self.assertIn("1 more squad needed", answer["error"])

    def test_a_size_in_between_takes_the_next_template(self):
        self.assertEqual(self.template_for(30), "spearMilitia")
        self.assertEqual(self.template_for(33), "retinue_tier1")
        self.assertIsNone(self.template_for(37))

    def template_for(self, men):
        return self.game.exec(f'return (require("features.liege_contracts.rules").loan_template({men}, nil, require("config").liege_contracts.loan_templates))')

    def test_a_failed_squad_removal_changes_nothing(self):
        self.game.exec("require('features.liege_contracts.world').remove_squad = function() return nil, 'addRemoveSquadRequest: no' end")
        answer = self.fulfil(LOAN_ID)
        self.assertFalse(answer["ok"])
        self.assertEqual((self.contracts()["done"], self.contracts()["loans_text"], self.contracts()["tiers"]["large"]["used"]), (0, "", 0))


class TributePauseTests(ContractsTestCase):
    def tick(self):
        answer = self.ask("tribute_tick_now")
        self.assertTrue(answer["ok"], answer)
        return answer["result"]["history"][-1]

    def test_a_paused_month_pays_nothing_and_counts_down(self):
        self.game.exec('require("features.tribute.init").skip_months(2)')
        first, second, third = self.tick(), self.tick(), self.tick()
        self.assertEqual((first.get("skipped"), second.get("skipped"), third.get("skipped")), (True, True, None))
        self.assertEqual(self.game.exec('return require("features.tribute.init").state:get("tribute_skip_months")'), 0)

    def test_the_pause_adds_up_and_survives_a_load(self):
        self.game.exec('require("features.tribute.init").skip_months(3); require("features.tribute.init").skip_months(3)')
        self.game.exec('require("features.tribute.init").state:load()')
        self.assertEqual(self.game.exec('return require("features.tribute.init").state:get("tribute_skip_months")'), 6)


class RewardTests(ContractsTestCase):
    def setUp(self):
        super().setUp()
        self.game.exec('require("config").liege_contracts.tier_limits.large = 5')
        self.vassals_pay(1)

    def large(self, reward_kind, reward_good, reward_amount):
        self.offer_now(offer_of(contract(LARGE, TRIBUTE, 3, reward_kind, reward_good, reward_amount)))
        answer = self.fulfil("large-1")
        self.assertTrue(answer["ok"], answer)
        return answer["result"]

    def test_kings_favour_rises_by_the_amount(self):
        self.large("k", 0, 10)
        self.assertEqual(self.pawn.kingsFavour, 10)
        self.assertEqual(self.contracts()["kings_favour"], 10)

    def test_a_kings_favour_that_does_not_rise_is_a_failed_reward(self):
        self.game.exec("require('features.liege_contracts.world').add_kings_favour = function() return nil, 'changeKingsFavour: no' end")
        self.large("k", 0, 10)
        self.assertEqual(self.contracts()["failed_rewards"], 1)

    def test_a_law_reward_unlocks_one_locked_law_with_the_contract_source(self):
        before = self.game.exec('return #require("features.tech_tree.init").granted_laws()')
        result = self.large("l", 0, 1)
        granted = self.game.exec('return table.concat(require("features.tech_tree.init").granted_laws(), ",")')
        self.assertEqual(before, 0)
        self.assertEqual(granted, result["reward"]["law"])
        self.assertEqual(self.game.exec(f'return require("features.tech_tree.init").law_source("{granted}")'), "Contract: Large 1")

    def test_three_law_rewards_unlock_three_different_laws(self):
        self.game.exec('require("config").liege_contracts.tier_limits.large = 5')
        laws = set()
        for _ in range(3):
            self.large("l", 0, 1)
            laws = set(self.game.exec('return table.concat(require("features.tech_tree.init").granted_laws(), ",")').split(","))
            self.offer_now(offer_of(contract(LARGE, TRIBUTE, 3, "l", 0, 1)))
        self.assertEqual(len(laws), 3)

    def test_a_contract_law_of_the_other_path_can_be_enacted(self):
        self.large("l", 0, 1)
        law = self.game.exec('return require("features.tech_tree.init").granted_laws()[1]')
        self.game.exec('local t = require("features.tech_tree.init"); t.choose_path(t.tree.paths[1])')
        other = self.game.exec(f"""
            local t = require("features.tech_tree.init")
            local path = t.path()
            return tostring(t.tree.laws_by_id["{law}"].path) .. ":" .. tostring(path)
        """)
        answer = self.ask("tech_tree_enact_law", law=law)
        self.assertTrue(answer["ok"], (answer, other))

    def test_a_law_slot_reward_adds_a_slot(self):
        self.assertEqual(self.slots(), 1)
        self.large("s", 0, 1)
        self.assertEqual(self.slots(), 2)
        self.assertEqual(self.pawn.kingsFavour, 0)

    def test_a_law_slot_reward_at_five_slots_pays_kings_favour_instead(self):
        self.fill_slots()
        self.assertEqual(self.slots(), 5)
        result = self.large("s", 0, 1)
        self.assertEqual(self.slots(), 5)
        self.assertEqual(self.pawn.kingsFavour, 10)
        self.assertEqual(result["reward"]["fallback"], {"kind": "kings_favour", "amount": 10})
        self.assertEqual(self.contracts()["failed_rewards"], 0)

    def test_a_relief_promise_adds_up(self):
        self.large("p", 0, 5)
        self.offer_now(offer_of(contract(LARGE, TRIBUTE, 3, "p", 0, 5)))
        self.assertTrue(self.fulfil("large-1")["ok"])
        self.assertEqual(self.contracts()["relief_bonus_squads"], 10)


class ManorTests(ContractsTestCase):
    def setUp(self):
        super().setUp()
        self.offer_now(NINE)
        self.set_stock(PLANKS, 60)

    def test_without_a_manor_the_command_refuses_even_with_enough_goods(self):
        self.world.manor.Data.constructed = False
        answer = self.fulfil("small-1")
        self.assertFalse(answer["ok"])
        self.assertIn("Build a manor to fulfil contracts.", answer["error"])
        self.assertEqual((self.stock(PLANKS), self.stock(CLAY)), (60, 0))
        self.assertEqual(self.contracts()["done"], 0)

    def test_without_a_manor_the_window_greys_every_button_and_shows_the_line(self):
        self.world.manor.Data.constructed = False
        state = self.contracts()
        self.assertEqual(len(state["contracts"]), 9)
        self.assertFalse(any(card["enabled"] for card in state["contracts"]))
        self.assertEqual(state["notice_text"], "Build a manor to fulfil contracts.")
        view = self.ask("liege_menu_state")["result"]
        self.assertEqual(view["wanted_texts"]["NoticeText"], "Build a manor to fulfil contracts.")

    def test_with_a_manor_the_button_is_enabled_when_goods_and_limit_allow(self):
        self.assertTrue(self.card("small-1")["enabled"])
        self.assertFalse(self.card("small-3")["enabled"])  # no eel
        self.assertEqual(self.contracts()["notice_text"], "")

    def test_a_lost_manor_greys_the_buttons_again_and_the_offer_stays(self):
        self.assertTrue(self.card("small-1")["enabled"])
        self.world.manor.Data.constructed = False
        self.assertFalse(self.card("small-1")["enabled"])
        self.assertEqual(len(self.contracts()["offer"]), 9)
        self.world.manor.Data.constructed = True
        self.assertTrue(self.card("small-1")["enabled"])

    def test_an_unfinished_manor_site_does_not_count(self):
        self.world.manor.Data.constructed = False
        self.assertFalse(self.contracts()["manor"])


class ExpiryTests(ContractsTestCase):
    def test_winter_clears_the_offer_with_no_penalty(self):
        self.set_influence(300)
        self.go_to_spring()
        silver = self.pawn.silver
        for value in (SUMMER, AUTUMN):
            self.season(value)
            self.assertEqual(len(self.contracts()["offer"]), 9)
        self.season(WINTER)
        state = self.contracts()
        self.assertEqual(state["offer"], [])
        self.assertEqual(self.influence(), 300)
        self.assertEqual((self.pawn.silver, state["done"], state["failed_rewards"]), (silver, 0, 0))

    def test_winter_resets_the_counts_and_the_next_spring_deals_a_new_offer(self):
        self.go_to_spring()
        first = self.contracts()["offer_text"]
        self.set_stock(PLANKS, 500)
        self.game.exec('require("config").liege_contracts.tier_limits.small = 3')
        for card in self.contracts()["contracts"]:
            if card["tier"] == SMALL:
                self.fulfil(card["id"])
        for value in (SUMMER, AUTUMN, WINTER):
            self.season(value)
        self.assertEqual(self.contracts()["tiers"]["small"]["used"], 0)
        self.season(SPRING)
        second = self.contracts()
        self.assertEqual(len(second["offer"]), 9)
        self.assertNotEqual(second["offer_text"], first)

    def test_the_window_in_winter_shows_no_cards_and_the_time_to_spring(self):
        self.go_to_spring()
        for value in (SUMMER, AUTUMN, WINTER):
            self.season(value)
        self.calendar.day = 335
        view = self.ask("liege_menu_state")["result"]["view"]
        self.assertEqual(view["cards"], [])
        self.assertEqual(view["remaining_text"], "Time to fulfil contracts: no contracts now")
        self.assertEqual(view["refresh_text"], "Contracts refresh: In spring, in 90 days")
        self.assertIn("start of spring", view["notice_text"])

    def test_a_contract_is_not_fulfilled_in_winter(self):
        self.offer_now(NINE)
        self.set_stock(PLANKS, 60)
        self.season(WINTER)
        self.assertEqual(self.contracts()["offer"], [])
        self.assertFalse(self.fulfil("small-1")["ok"])


class CountdownTests(ContractsTestCase):
    def test_the_days_to_winter_and_to_spring(self):
        self.calendar.day = 125
        state = self.contracts()
        self.assertEqual((state["days_to_winter"], state["days_to_spring"]), (210, 300))
        self.calendar.day = 60
        state = self.contracts()
        self.assertEqual((state["days_to_winter"], state["days_to_spring"]), (275, 0))

    def test_the_window_texts(self):
        self.calendar.day = 125
        self.offer_now(NINE)
        view = self.ask("liege_menu_state")["result"]["view"]
        self.assertEqual(view["remaining_text"], "Time to fulfil contracts: 210 days remaining")
        self.assertEqual(view["refresh_text"], "Contracts refresh: In spring, in 300 days")


class RemovedCommandsTests(ContractsTestCase):
    def test_the_old_commands_are_gone(self):
        for name, args in (("liege_contract_pick", {"id": "x"}), ("liege_contract_complete", {}), ("liege_contracts_test_progress", {"index": 1, "value": 1}),
                           ("liege_send_tribute", {"amount": 100}), ("liege_request_arms", {}), ("liege_test_set_arms_day", {"day": 1})):
            answer = self.ask(name, **args)
            self.assertFalse(answer["ok"], name)
            self.assertIn("unknown", answer["error"].lower(), name)

    def test_the_penalty_config_and_the_arms_config_are_gone(self):
        values = self.game.exec('local c = require("config"); return tostring(c.liege_contracts.fail_penalty) .. ":" .. tostring(c.liege_influence.arms_shipment)')
        self.assertEqual(values, "nil:nil")

    def test_the_liege_state_has_no_arms_fields(self):
        state = self.ask("liege_state")["result"]
        for key in ("arms_last_day", "arms_enabled", "arms_reason", "arms_days_left"):
            self.assertNotIn(key, state)


class StateTests(ContractsTestCase):
    def reload_state(self):
        self.game.exec(f"{FEATURE}.state:load()")

    def test_the_keys_are_written(self):
        self.offer_now(NINE)
        self.set_stock(PLANKS, 50)
        self.fulfil("small-1")
        keys = self.game.exec(f"""
            local state = {FEATURE}.state
            local out = {{}}
            for _, key in ipairs({{ "contracts_spring_no", "contracts_offer", "contracts_used", "contracts_done", "contracts_loans" }}) do out[#out + 1] = key .. "=" .. tostring(state:get(key)) end
            return table.concat(out, ";")
        """)
        self.assertIn("contracts_used=s-1.m-0.l-0", keys)
        self.assertIn("contracts_done=1", keys)
        self.assertIn(contract(SMALL, PLANKS, 50, "g", CLAY, 30, 1), keys)
        self.assertIn("contracts_loans=;", keys + ";")
        for gone in ("contracts_active", "contracts_start_day", "contracts_baseline", "contracts_progress", "contracts_failed"):
            self.assertNotIn(gone, keys)

    def test_the_round_trip_keeps_the_nine_contracts_and_the_counts(self):
        self.offer_now(NINE)
        self.set_stock(PLANKS, 50)
        self.fulfil("small-1")
        before = self.contracts()
        self.reload_state()
        self.game.advance(4)
        after = self.contracts()
        self.assertEqual(after["offer_text"], before["offer_text"])
        self.assertEqual(after["tiers"], before["tiers"])
        self.assertEqual([(c["id"], c["amount"], c["reward"], c["done"]) for c in after["contracts"]],
                         [(c["id"], c["amount"], c["reward"], c["done"]) for c in before["contracts"]])
        self.assertEqual(after["done"], 1)
        self.assertTrue(self.card("small-1")["done"])

    def test_an_offer_survives_a_load_and_is_not_drawn_again(self):
        self.go_to_spring()
        offer = self.contracts()["offer_text"]
        self.reload_state()
        self.game.advance(10)
        self.assertEqual(self.contracts()["offer_text"], offer)

    def test_a_removed_good_is_dropped_with_no_penalty(self):
        self.set_influence(300)
        self.game.exec(f'{FEATURE}.state:set("contracts_offer", "{offer_of(contract(SMALL, 999, 5, "k", 0, 5), contract(SMALL, PLANKS, 50, "g", CLAY, 30))}")')
        self.game.advance(5)
        state = self.contracts()
        self.assertEqual(len(state["offer"]), 1)
        self.assertEqual(self.influence(), 300)
        self.assertEqual(state["failed_rewards"], 0)
        self.assertIn("s-999-5-k-0-5-0", self.game.read_text("mod.log"))

    def test_an_old_large_contract_is_dropped_with_no_penalty(self):
        # Version 2 had Large contracts with a good (plate armor) and the reward t (a tech point) or i (influence).
        self.game.exec(f'{FEATURE}.state:set("contracts_offer", "{offer_of("l-293-5-i-0-1000-0", "l-273-9-t-0-1-0", contract(SMALL, PLANKS, 50, "g", CLAY, 30))}")')
        self.game.advance(5)
        state = self.contracts()
        self.assertEqual([c["id"] for c in state["contracts"]], ["small-1"])
        self.assertEqual(state["failed_rewards"], 0)

    def test_a_large_cost_contract_round_trips(self):
        self.offer_now(NINE)
        before = self.contracts()
        self.reload_state()
        self.game.advance(4)
        after = self.contracts()
        self.assertEqual(after["offer_text"], before["offer_text"])
        self.assertEqual([(c["id"], c["cost"], c["amount"], c["reward"]) for c in after["contracts"] if c["tier"] == LARGE],
                         [("large-1", "send_families", 3, {"kind": "kings_favour", "amount": 10}),
                          ("large-2", "loan_units", 1, {"kind": "law", "amount": 1}),
                          ("large-3", "tribute_season", 3, {"kind": "relief_promise", "amount": 5})])

    def test_the_relief_bonus_is_saved(self):
        self.game.exec('require("features.invasion.init").add_relief_bonus(5)')
        self.reload_invasion_state()
        self.assertEqual(self.contracts()["relief_bonus_squads"], 5)

    def reload_invasion_state(self):
        self.game.exec('require("features.invasion.init").state:load()')


class OldSaveTests(VassalsTestCase):
    """A save from before the change has liege_influence, arms_last_day and the keys of the active contract."""

    SAVED_TAGS = ("invasion:v=2", "invasion:liege_influence=40", "invasion:arms_last_day=12", "invasion:contracts_spring_no=3",
                  "invasion:contracts_offer=timber_for_the_walls.clear_the_roads.keep_the_peace", "invasion:contracts_active=raise_the_levy",
                  "invasion:contracts_start_day=5", "invasion:contracts_baseline=o0-0.s-3", "invasion:contracts_progress=o0-1", "invasion:contracts_failed=2")

    def test_an_old_save_keeps_its_influence_and_drops_the_old_offer_and_contract(self):
        self.game.advance(5)
        answer = self.ask("liege_contracts_state")["result"]
        self.assertEqual((answer["influence"], answer["offer"], answer["contracts"]), (40, [], []))
        self.assertEqual(self.ask("liege_state")["result"]["influence"], 40)
        self.game.advance(5)
        self.assertEqual(self.ask("liege_contracts_state")["result"]["offer"], [])

    def test_the_old_keys_are_kept_but_ignored(self):
        self.game.advance(5)
        state = self.ask("liege_contracts_state")["result"]
        self.assertEqual(state["failed_rewards"], 0)
        self.assertEqual(state["done"], 0)


class WindowViewTests(ContractsTestCase):
    def view(self):
        answer = self.ask("liege_menu_state")
        self.assertTrue(answer["ok"], answer)
        return answer["result"]

    def test_with_no_offer_the_window_says_the_liege_sends_contracts_at_spring(self):
        view = self.view()["view"]
        self.assertEqual(view["cards"], [])
        self.assertIn("start of spring", view["notice_text"])

    def test_the_tier_boxes_show_the_name_and_the_count_only(self):
        tiers = self.view()["view"]["tiers"]
        self.assertEqual([tiers[t]["name"] for t in (SMALL, MEDIUM, LARGE)], ["Small", "Medium", "Large"])
        self.assertEqual([tiers[t]["count_text"] for t in (SMALL, MEDIUM, LARGE)], ["0 / 1", "0 / 1", "0 / 1"])

    def test_a_card_shows_requirement_storage_and_reward(self):
        self.offer_now(NINE)
        self.set_stock(PLANKS, 52)
        cards = self.view()["view"]["cards"]
        self.assertEqual(len(cards), 9)
        first = cards[0]
        self.assertEqual((first["requirement"], first["have"], first["reward_text"], first["label"]), ("Deliver 50 planks", "In storage: 52 / 50", "+30 clay", "Fulfil"))
        texts = [card["reward_text"] for card in cards]
        self.assertIn("+10 King's Favour", texts)
        self.assertIn("a new law", texts)
        self.assertIn("+5 relief squads", texts)
        self.assertIn("+15 tools", texts)
        for card in cards:
            self.assertNotIn("name", card)
            self.assertNotIn("quote", card)
            self.assertNotIn("penalty", card)

    def test_the_large_cards_show_a_cost_line(self):
        self.offer_now(NINE)
        self.vassals_pay(2)
        large = [card for card in self.view()["view"]["cards"] if card["tier"] == LARGE]
        self.assertEqual([card["requirement"] for card in large],
                         ["Cost: 3 families, for good", "Cost: 1 squad for 60 days", "Cost: tribute for 3 months"])
        wanted = self.view()["wanted_texts"]
        self.assertEqual(wanted["ReqText2_0"], "3 FAMILIES, FOR GOOD")
        self.assertEqual(wanted["RewText2_1"], "A NEW LAW")
        self.assertEqual(wanted["HaveText2_0"], "Families: 6")

    def test_the_reward_texts(self):
        text = self.game.exec("""
            local view = require("features.liege_contracts.view")
            local names = { [17] = "planks" }
            return table.concat({ view.reward_text({ kind = "kings_favour", amount = 10 }, names), view.reward_text({ kind = "law_slot", amount = 1 }, names),
                view.reward_text({ kind = "armor", good = 17, amount = 15 }, names), view.reward_text({ kind = "relief_promise", amount = 5 }, names) }, "|")
        """)
        self.assertEqual(text, "+10 King's Favour|+1 law slot|+15 planks|+5 relief squads")

    def test_after_a_fulfilment_the_label_and_the_count_change(self):
        self.offer_now(NINE)
        self.set_stock(PLANKS, 60)
        self.fulfil("small-1")
        view = self.view()["view"]
        self.assertEqual(view["tiers"][SMALL]["count_text"], "1 / 1")
        self.assertEqual(view["cards"][0]["label"], "Fulfilled")
        self.assertEqual(view["cards"][0]["have"], "In storage: 10 / 50")
        self.assertFalse(view["cards"][0]["enabled"])

    def test_the_top_bar_has_no_influence_and_no_silver_text_and_there_is_no_arms_text(self):
        wanted = self.view()["wanted_texts"]
        for key in ("InfluenceText", "SilverText", "ArmsInfoText", "FooterText"):
            self.assertNotIn(key, wanted)

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


class NoArmsLeftTests(unittest.TestCase):
    def test_no_lua_file_names_the_arms_shipment(self):
        pack = find_pack_mod() / "Scripts"
        for path in pack.rglob("*.lua"):
            text = path.read_text(encoding="utf-8")
            for word in ("shipment_status", "request_arms_shipment", "arms_shipment", "ArmsButton", "ArmsInfoText", "arms_last_day"):
                self.assertNotIn(word, text, f"{path} still names {word}")


if __name__ == "__main__":
    unittest.main()
