"""Tests for the feature liege_contracts of the pack mod in the fake game (change update-liege-contracts-tiers, #533).

They run the real Lua files. They do not prove how the real game behaves (see the test scenarios of the feature).
"""

import json
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
# Goods of the tests (item ids of notes/item-ids.md)
PLANKS, BERRIES, CLAY, SALT, BOWS = 17, 171, 146, 145, 205
CUT_STONE, TOOLS, METAL_BARS = 283, 6, 35
PLATE, SWORDS, HELMETS, SAUSAGES = 293, 177, 273, 320
FEATURE = 'require("features.liege_contracts.init")'
SMALL, MEDIUM, LARGE = "small", "medium", "large"
LETTER = {"small": "s", "medium": "m", "large": "l"}


def contract(tier, good, amount, kind, reward_good, reward_amount, done=0):
    """One contract in the saved text form: s-17-50-g-146-30-0."""
    return f"{LETTER[tier]}-{good}-{amount}-{kind}-{reward_good}-{reward_amount}-{done}"


def offer_of(*contracts):
    return ".".join(contracts)


# Nine contracts: three for each tier. Rewards: s = silver, g = goods, i = influence, t = tech point, r = regional wealth, w = weapons.
NINE = offer_of(
    contract(SMALL, PLANKS, 50, "g", CLAY, 30), contract(SMALL, BERRIES, 70, "r", 0, 60), contract(SMALL, SALT, 30, "g", PLANKS, 25),
    contract(MEDIUM, METAL_BARS, 24, "w", SWORDS, 15), contract(MEDIUM, CUT_STONE, 30, "s", 0, 200), contract(MEDIUM, TOOLS, 15, "g", METAL_BARS, 20),
    contract(LARGE, HELMETS, 9, "t", 0, 1), contract(LARGE, PLATE, 5, "i", 0, 1000), contract(LARGE, SAUSAGES, 18, "t", 0, 1),
)


def load_data():
    return json.loads((find_pack_mod() / "data" / "liege_contracts" / "contracts.json").read_text(encoding="utf-8"))


class ContractsTestCase(TechTreeTestCase):
    START_SEASON = SUMMER  # a game that starts in summer makes no offer until spring
    def setUp(self):
        super().setUp()
        self.world = self.game.lua.eval(WORLD)(self.game.fg, self.region)
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

    def tech_picks(self):
        return self.game.exec(f'return {FEATURE}.state:get("tech_picks_earned")')


class SmokeTests(ContractsTestCase):
    def test_the_feature_loads_with_the_starter_table(self):
        state = self.contracts()
        self.assertEqual(state["offer"], [])
        self.assertEqual(state["contracts"], [])
        self.assertEqual(state["tiers"], {"small": {"used": 0, "limit": 1}, "medium": {"used": 0, "limit": 1}, "large": {"used": 0, "limit": 1}})


class LoaderTests(ContractsTestCase):
    GOOD_TIER = '{ requests = { { good = 1, weight = 1 } }, rewards = { { kind = "silver", min = 5, max = 6 } } }'

    def build(self, small=None, extra="offer_per_tier = 1", version="2"):
        tier = small or self.GOOD_TIER
        return self.game.exec(f"""
            local loader = require("features.liege_contracts.loader")
            local tier = {tier}
            local ok, err = pcall(loader.build, {{ version = {version}, {extra}, tiers = {{ small = tier, medium = tier, large = tier }} }})
            return ok and "ok" or tostring(err)
        """)

    def data(self):
        return load_data()

    def test_the_table_fields(self):
        data = self.data()
        self.assertEqual((data["version"], data["offer_per_tier"]), (2, 3))
        self.assertEqual(sorted(data["tiers"]), ["large", "medium", "small"])
        text = json.dumps(data)
        for word in ("duration", "penalty", "objectives", "envoy"):
            self.assertNotIn(word, text)

    def test_the_starter_table_loads_with_the_pools_of_the_design(self):
        sizes = self.game.exec(f"""
            local c = {FEATURE}.contracts
            return #c.tiers.small.requests .. ":" .. #c.tiers.medium.requests .. ":" .. #c.tiers.large.requests .. ":" .. c.offer_per_tier
        """)
        self.assertEqual(sizes, "13:8:12:3")

    def test_every_good_of_the_starter_table_has_a_name(self):
        data = self.data()
        goods = set()
        for tier in data["tiers"].values():
            goods.update(request["good"] for request in tier["requests"])
            for reward in tier["rewards"]:
                goods.update(data["good_lists"].get(reward.get("goods"), []))
        self.assertEqual(sorted(goods - {int(key) for key in data["names"]}), [])
        for tier in data["tiers"].values():
            for request in tier["requests"]:
                self.assertGreater(request["weight"], 0)

    def test_the_reward_pools_follow_table_2(self):
        data = self.data()
        kinds = {name: {reward["kind"] for reward in tier["rewards"]} for name, tier in data["tiers"].items()}
        self.assertEqual(kinds, {"small": {"goods", "regional_wealth"}, "medium": {"weapons", "goods", "silver"}, "large": {"tech_point", "influence"}})
        weapons = next(r for r in data["tiers"]["medium"]["rewards"] if r["kind"] == "weapons")
        self.assertEqual(sorted(data["good_lists"][weapons["goods"]]), sorted([177, 270, 178, 133, 271, 206]))
        large = {r["kind"]: r for r in data["tiers"]["large"]["rewards"]}
        self.assertEqual((large["tech_point"]["min"], large["tech_point"]["max"]), (1, 1))
        self.assertEqual((large["influence"]["min"], large["influence"]["max"]), (1000, 1000))

    def test_a_good_table_loads(self):
        self.assertEqual(self.build(), "ok")

    def test_an_unknown_kind_names_the_tier_and_the_kind(self):
        answer = self.build(self.GOOD_TIER.replace("silver", "dance"))
        self.assertIn("tier 'small' reward 1", answer)
        self.assertIn("unknown kind 'dance'", answer)

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
        answer = self.build(self.GOOD_TIER.replace('"silver"', '"goods"'))
        self.assertIn("needs the field 'goods'", answer)

    def test_the_old_version_is_refused(self):
        self.assertIn("'version' must be 2", self.build(version="1"))


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
        weight = next(r["weight"] for r in data["tiers"][card["tier"]]["requests"] if r["good"] == card["good"])
        base = {"small": 50, "medium": 30, "large": 15}[card["tier"]]
        return max(1, int(base * weight * 1.25 + 0.5 + 1e-9))

    def test_a_changed_config_value_changes_the_amount(self):
        self.game.exec('local c = require("config").liege_contracts; c.base.small = 100; c.base.medium = 1; c.base.large = 1; c.weight[17] = 2')
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
                goods = [card["good"] for card in cards if card["tier"] == tier]
                self.assertEqual(len(goods), 3)
                self.assertEqual(len(set(goods)), 3)

    def test_a_request_good_belongs_to_the_pool_of_its_tier(self):
        data = load_data()
        for card in self.draw(7):
            self.assertIn(card["good"], [r["good"] for r in data["tiers"][card["tier"]]["requests"]])

    def test_rewards_follow_the_tier_and_never_repeat_the_request_good(self):
        allowed = {SMALL: {"goods", "regional_wealth"}, MEDIUM: {"weapons", "goods", "silver"}, LARGE: {"tech_point", "influence"}}
        ranges = {"goods": {SMALL: (20, 40), MEDIUM: (15, 30)}, "weapons": {MEDIUM: (10, 20)}, "regional_wealth": {SMALL: (40, 80)},
                  "silver": {MEDIUM: (150, 300)}, "tech_point": {LARGE: (1, 1)}, "influence": {LARGE: (1000, 1000)}}
        for seed in range(1, 25):
            self.setUp()
            for card in self.draw(seed):
                reward = card["reward"]
                self.assertIn(reward["kind"], allowed[card["tier"]])
                low, high = ranges[reward["kind"]][card["tier"]]
                self.assertTrue(low <= reward["amount"] <= high, card)
                if reward["kind"] in ("goods", "weapons"):
                    self.assertNotEqual(reward["good"], card["good"])

    def test_small_goods_rewards_are_tier_1_goods_and_medium_goods_rewards_are_tier_2_goods(self):
        data = load_data()
        pools = {tier: {r["good"] for r in data["tiers"][tier]["requests"]} for tier in data["tiers"]}
        for seed in range(1, 25):
            self.setUp()
            for card in self.draw(seed):
                if card["reward"]["kind"] == "goods":
                    self.assertIn(card["reward"]["good"], pools[card["tier"]])

    def test_the_draw_gives_different_offers(self):
        first = [card["good"] for card in self.draw(1)]
        self.setUp()
        second = [card["good"] for card in self.draw(99)]
        self.assertNotEqual(first, second)

    def test_the_tech_point_reward_is_drawn_only_when_the_picks_exist(self):
        self.game.exec(f"""
            local rules = require("features.liege_contracts.rules")
            local data = {FEATURE}.contracts
            seen_tech = false
            math.randomseed(5)
            for _ = 1, 40 do
                local offer = rules.draw_offer({{ tiers = data.tiers, base = {{ small = 1, medium = 1, large = 1 }}, difficulty = 1,
                    allowed = function(kind) return kind ~= "tech_point" end }}, 3, math.random)
                for _, c in ipairs(offer) do if c.reward.kind == "tech_point" then seen_tech = true end end
            end
        """)
        self.assertFalse(self.game.exec("return seen_tech"))

    def test_a_draw_of_more_than_the_pool_fails(self):
        self.assertIn("fewer than", self.game.exec(f"""
            local rules = require("features.liege_contracts.rules")
            local data = {FEATURE}.contracts
            local offer, why = rules.draw_offer({{ tiers = data.tiers, base = {{ small = 1, medium = 1, large = 1 }}, difficulty = 1 }}, 20, math.random)
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

    def test_offer_now_without_ids_draws(self):
        self.assertEqual(len(self.offer_now()["offer"]), 9)

    def test_offer_now_refuses_an_unknown_good(self):
        answer = self.ask("liege_contracts_offer_now", ids=contract(SMALL, 999, 5, "s", 0, 5))
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

    def test_a_silver_reward_raises_the_treasury(self):
        self.set_stock(CUT_STONE, 30)
        silver = self.pawn.silver
        self.assertTrue(self.fulfil("medium-2")["ok"])
        self.assertEqual(self.pawn.silver, silver + 200)
        self.assertEqual(self.stock(CUT_STONE), 0)

    def test_a_weapons_reward_adds_the_weapons(self):
        self.set_stock(METAL_BARS, 24)
        self.assertTrue(self.fulfil("medium-1")["ok"])
        self.assertEqual(self.stock(SWORDS), 15)

    def test_a_regional_wealth_reward_raises_the_wealth(self):
        self.set_stock(BERRIES, 70)
        self.assertTrue(self.fulfil("small-2")["ok"])
        self.assertEqual(self.region.regionalWealth, 160)

    def test_an_influence_reward_raises_the_influence(self):
        self.set_stock(PLATE, 5)
        self.assertTrue(self.fulfil("large-2")["ok"])
        self.assertEqual(self.influence(), 1000)

    def test_a_tech_point_reward_pays_or_is_counted(self):
        self.set_stock(HELMETS, 9)
        before = self.tech_picks()
        self.assertTrue(self.fulfil("large-1")["ok"])
        self.assertEqual(self.tech_picks(), max(0, before) + 1)
        self.assertEqual(self.contracts()["failed_rewards"], 0)

    def test_goods_are_taken_from_any_storehouse(self):
        self.set_stock(PLANKS, 20)
        self.set_stock(PLANKS, 40, self.world.store2)
        self.assertTrue(self.fulfil("small-1")["ok"])
        self.assertEqual(self.stock(PLANKS), 10)

    def test_not_enough_goods_is_refused_with_the_missing_amount_and_nothing_moves(self):
        self.set_stock(PLANKS, 45)
        silver = self.pawn.silver
        answer = self.fulfil("small-1")
        self.assertFalse(answer["ok"])
        self.assertIn("5 more needed", answer["error"])
        self.assertEqual((self.stock(PLANKS), self.stock(CLAY), self.pawn.silver), (45, 0, silver))
        self.assertEqual(self.contracts()["done"], 0)

    def test_the_tier_limit_stops_a_second_contract_of_the_tier(self):
        self.set_stock(PLANKS, 50)
        self.set_stock(SALT, 30)
        self.assertTrue(self.fulfil("small-1")["ok"])
        answer = self.fulfil("small-3")
        self.assertFalse(answer["ok"])
        self.assertIn("limit of 1", answer["error"])
        self.assertEqual(self.stock(SALT), 30)

    def test_the_other_tiers_are_not_affected_by_a_full_tier(self):
        self.set_stock(PLANKS, 50)
        self.set_stock(CUT_STONE, 30)
        self.assertTrue(self.fulfil("small-1")["ok"])
        self.assertTrue(self.fulfil("medium-2")["ok"])
        state = self.contracts()
        self.assertEqual((state["tiers"]["small"]["used"], state["tiers"]["medium"]["used"], state["tiers"]["large"]["used"]), (1, 1, 0))

    def test_a_changed_limit_in_the_config_allows_more(self):
        self.game.exec('require("config").liege_contracts.tier_limits.small = 2')
        self.set_stock(PLANKS, 50)
        self.set_stock(SALT, 30)
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
        self.assertEqual(self.influence(), 0)

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
        self.assertFalse(self.card("small-3")["enabled"])  # no salt
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
            for _, key in ipairs({{ "contracts_spring_no", "contracts_offer", "contracts_used", "contracts_done" }}) do out[#out + 1] = key .. "=" .. tostring(state:get(key)) end
            return table.concat(out, ";")
        """)
        self.assertIn("contracts_used=s-1.m-0.l-0", keys)
        self.assertIn("contracts_done=1", keys)
        self.assertIn(contract(SMALL, PLANKS, 50, "g", CLAY, 30, 1), keys)
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
        self.game.exec(f'{FEATURE}.state:set("contracts_offer", "{offer_of(contract(SMALL, 999, 5, "s", 0, 5), contract(SMALL, PLANKS, 50, "g", CLAY, 30))}")')
        self.game.advance(5)
        state = self.contracts()
        self.assertEqual(len(state["offer"]), 1)
        self.assertEqual(self.influence(), 300)
        self.assertEqual(state["failed_rewards"], 0)
        self.assertIn("s-999-5-s-0-5-0", self.game.read_text("mod.log"))


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
        self.assertIn("+60 regional wealth", texts)
        self.assertIn("+200 treasury silver", texts)
        self.assertIn("+1 tech point", texts)
        self.assertIn("+1000 influence", texts)
        self.assertIn("+15 swords", texts)
        for card in cards:
            self.assertNotIn("name", card)
            self.assertNotIn("quote", card)
            self.assertNotIn("penalty", card)

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
