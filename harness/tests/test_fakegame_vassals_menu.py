"""Tests for the feature vassals_menu of the pack mod in the fake game (change add-vassals-menu, #564).

They run the real Lua files (the view model, the click handlers, the commands). The cooked widget is not in the fake game, so a
click is sent through the exported `click` function. They do not prove how the real game behaves (see the test scenario
`vassals-menu-window`).
"""

import unittest

import fakegame_path  # noqa: F401
from test_fakegame_tribute import CLUMP_CLASS, MATERIAL, STORE_STUB
from test_fakegame_vassals import RESTORE_STUB, HandoverBase

FEATURE = 'require("features.vassals_menu.init")'
VIEW = 'require("features.vassals_menu.view")'
REGION_X = {"Home": 0, "Eichenhau": 100, "Goldhof": 200}  # a node at this X lies in that region

# Counts the calls of the two commands that the menu may call and keeps the arguments of the last call (the test helpers use other commands).
SPY = """
CALLS, ARGS = 0, nil
local c = require("HarnessCommands")
local old = c.dispatch
c.dispatch = function(name, args, mod)
    if name == "InvasionMod.vassals_set_policy" or name == "InvasionMod.vassals_restore" then CALLS = CALLS + 1; ARGS = args end
    return old(name, args, mod)
end
"""


def refuse(command, reason, schema):
    """Lua that makes one command refuse. The handler is replaced, so the other commands keep working."""
    return f'local c = require("HarnessCommands"); c.unregister("InvasionMod.{command}"); c.register("InvasionMod.{command}", function() return nil, "{reason}" end, {schema})'


REFUSE_POLICY = refuse("vassals_set_policy", "policy refused for the test", '{ slot = { type = "integer", required = true }, policy = { type = "string", required = true } }')
REFUSE_RESTORE = refuse("vassals_restore", "restore refused for the test", '{ region = { type = "string" } }')


class MenuBase(HandoverBase):
    def setUp(self):
        super().setUp()
        self.game.exec(STORE_STUB)
        self.game.exec(RESTORE_STUB)
        self.game.exec("package.loaded['HarnessLords'].lord_declare_peace = function() return { ok = true } end")
        self.calendar.month = 3
        self.calendar.daysTotal = 100
        self.pawn.silver = 500
        self.game.method(self.engine, "getRegionByPos", self.region_by_position)
        # The region rows of the stub carry the numbers that the card shows (families and buildings).
        self.game.exec("REGIONS[2].families, REGIONS[2].buildings = 5, 4; REGIONS[3].families, REGIONS[3].buildings = 7, 6")
        self.add_region("Eichenhau", True, 4)
        self.game.advance(10)
        self.lord_owns("Eichenhau")

    # -- helpers ---------------------------------------------------------------------------

    def region_by_position(self, _self, pos, _flag):
        for name, x in REGION_X.items():
            if pos["X"] == x:
                return self.region_by_name[name]
        return None

    def named(self, class_name, name):
        obj = self.game.obj(class_name)
        self.game.method(obj, "GetFName", lambda _self: self.game.text(name))
        return obj

    def deposit(self, good, region="Eichenhau"):
        decal = self.game.obj("DecalComponent", DecalSize=self.game.struct(X=5000, Y=5000, Z=100))
        material = self.named("MaterialInstance", MATERIAL[good])
        self.game.method(decal, "GetDecalMaterial", lambda _self: material)
        x = REGION_X[region]
        self.game.method(decal, "K2_GetComponentLocation", lambda _self: self.game.struct(X=x, Y=5, Z=0))
        return self.game.obj("ResourceNode", ResourceZoneDecal=decal, resourceClumps=self.game.array([]))

    def second_vassal(self):
        # As the first handover: while the lord is not known, the loss check does not run (the fake gives no region to the lord).
        self.game.exec("package.loaded['features.vassals.world'].lord_status = function() return nil end")
        self.add_region("Goldhof", True, 6)
        self.game.advance(10)
        self.lord_owns("Goldhof")  # the real handover gives the region to the lord; the fake does not

    def view(self):
        answer = self.ask("vassals_menu_view")
        self.assertTrue(answer["ok"], answer)
        return answer["result"]

    def card(self, position):
        return self.view()["cards"][position]

    def click(self, name):
        return self.game.exec(f'return (({FEATURE}).click("{name}"))')  # the extra brackets keep the first value only

    def set_state(self, key, value):
        literal = f'"{value}"' if isinstance(value, str) else str(value).lower()
        self.game.exec(f'require("features.vassals.init").state:set("{key}", {literal})')

    def record_wiped(self, index, region, day):
        self.set_state(f"wiped{index}_region", region)
        self.set_state(f"wiped{index}_lord", "Aldric")
        self.set_state(f"wiped{index}_day", day)

    def policy(self, slot):
        return self.state()["vassals"][slot - 1]["policy"]


class HeaderTests(MenuBase):
    def setUp(self):
        super().setUp()
        self.deposit("iron")
        self.deposit("salt")
        self.deposit("iron", "Goldhof")
        self.deposit("salt", "Goldhof")
        self.second_vassal()

    def test_two_vassals_with_fair_and_heavy_policies_pay_250_of_each_good(self):
        self.ask("vassals_set_policy", slot=2, policy="heavy")
        view = self.view()
        self.assertEqual((view["count"], view["max"], view["count_text"]), (2, 3, "2 / 3"))
        self.assertEqual(view["tribute_text"], "250 iron, 250 salt")
        self.assertEqual((view["silver"], view["silver_text"]), (500, "500 silver"))

    def test_a_rebuilding_vassal_adds_nothing_to_the_tribute(self):
        self.set_state("vassal2_rebuilding", True)
        self.assertEqual(self.view()["tribute_text"], "100 iron, 100 salt")

    def test_no_vassal_pays_nothing(self):
        self.set_state("vassal1_rebuilding", True)
        self.set_state("vassal2_rebuilding", True)
        view = self.view()
        self.assertEqual(view["tribute_text"], "none")

    def test_the_header_follows_a_policy_change(self):
        self.ask("vassals_set_policy", slot=1, policy="light")
        self.assertEqual(self.view()["tribute_text"], "150 iron, 150 salt")  # light 50 + fair 100
        self.click("PolicyButton0_2")
        self.assertEqual(self.view()["tribute_text"], "250 iron, 250 salt")  # heavy 150 + fair 100


class CardTests(MenuBase):
    def setUp(self):
        super().setUp()
        self.deposit("iron")
        self.deposit("salt")
        self.add_families("Eichenhau", 5)

    def test_a_thriving_vassal_card(self):
        card = self.card(0)
        self.assertEqual((card["kind"], card["slot"], card["status"], card["status_text"]), ("vassal", 1, "thriving", "Thriving"))
        self.assertEqual((card["title"], card["lord_line"]), ("Eichenhau", "Lord Aldric"))
        self.assertEqual(card["stats"][:3], ["Thriving", "iron, salt", "100 iron, 100 salt"])
        self.assertEqual(card["stats"][3:5], ["5", "4"])
        self.assertIn("each month", card["note"])
        self.assertEqual([(p["name"], p["selected"]) for p in card["policies"]], [("light", False), ("fair", True), ("heavy", False)])
        self.assertEqual(card["policy_hint"], "Tribute x1: 100 of each rich resource")

    def test_days_as_vassal_count_from_the_handover(self):
        handed = self.state()["vassals"][0]["handed_day"]
        self.assertEqual(handed, 101)  # day 100 plus 1
        self.calendar.daysTotal = 112
        self.assertEqual(self.card(0)["stats"][5], "12 days")

    def test_a_region_without_rich_resources_shows_the_paid_good_flax(self):
        self.set_state("vassal1_region", "Eichenhau")
        self.game.exec('package.loaded["features.tribute.world"].rich_goods = function() return {} end')
        card = self.card(0)
        self.assertEqual(card["stats"][1], "flax, flax")
        self.assertEqual(card["stats"][2], "100 flax, 100 flax")

    def test_the_policy_changes_the_amount_and_the_hint(self):
        self.ask("vassals_set_policy", slot=1, policy="heavy")
        card = self.card(0)
        self.assertEqual(card["policy_hint"], "Tribute x1.5: 150 of each rich resource")
        self.assertEqual(card["stats"][2], "150 iron, 150 salt")
        self.ask("vassals_set_policy", slot=1, policy="light")
        self.assertEqual(self.card(0)["policy_hint"], "Tribute x0.5: 50 of each rich resource")

    def test_the_tech_factor_changes_the_amount(self):
        self.game.exec('require("features.tribute.init").set_share_factor(2)')
        self.assertEqual(self.card(0)["stats"][2], "200 iron, 200 salt")


class StatusTests(MenuBase):
    def test_the_flags_and_the_wiped_record_map_to_the_four_statuses(self):
        self.second_vassal()
        self.set_state("vassal2_stalled", True)
        self.record_wiped(1, "Krumme", 50)
        cards = self.view()["cards"]
        self.assertEqual([c["status_text"] for c in cards], ["Thriving", "Stalled", "Wiped"])
        self.set_state("vassal1_rebuilding", True)
        self.assertEqual(self.card(0)["status_text"], "Rebuilding")

    def test_a_stalled_vassal_still_pays_and_a_rebuilding_vassal_does_not(self):
        self.deposit("iron")
        self.set_state("vassal1_stalled", True)
        self.assertEqual(self.card(0)["stats"][2], "100 iron, 100 flax")
        self.set_state("vassal1_rebuilding", True)
        card = self.card(0)
        self.assertEqual(card["stats"][2], "none")
        self.assertIn("rebuilt", card["note"])
        self.assertEqual(card["status_text"], "Rebuilding")

    def test_a_stalled_note_names_the_growth_rule(self):
        self.set_state("vassal1_stalled", True)
        self.assertEqual(self.card(0)["note"], "The lord has built fewer than 3 buildings in 10 days.")

    def test_the_status_words_of_the_view_module(self):
        words = self.game.exec(f"local v = {VIEW}; return v.status_of({{ lord = 'A' }}) .. v.status_of({{ lord = 'A', stalled = true }}) .. "
                               f"v.status_of({{ lord = 'A', rebuilding = true, stalled = true }}) .. v.status_of({{ lord = 'none' }})")
        self.assertEqual(words, "thrivingstalledrebuildingclaimed")

    def test_a_claimed_region_without_a_lord_pays_nothing_yet(self):
        self.set_state("vassal1_lord", "none")
        card = self.card(0)
        self.assertEqual((card["status_text"], card["lord_line"], card["stats"][2]), ("Claimed", "No lord yet", "none"))


class SlotTests(MenuBase):
    def test_a_never_claimed_slot_is_a_dim_free_slot_card_without_buttons(self):
        cards = self.view()["cards"]
        self.assertEqual(len(cards), 3)
        free = cards[1]
        self.assertEqual((free["kind"], free["title"], free["dim"]), ("free", "Free slot", True))
        self.assertEqual(free["note"], "Claim and settle a region to gain a vassal.")
        self.assertEqual((free["policies"], free.get("restore")), ([], None))

    def test_wiped_villages_fill_the_free_cards_oldest_first(self):
        self.record_wiped(1, "Krumme", 80)
        self.record_wiped(2, "Hochweg", 20)
        cards = self.view()["cards"]
        self.assertEqual([(c["kind"], c["title"]) for c in cards], [("vassal", "Eichenhau"), ("wiped", "Hochweg"), ("wiped", "Krumme")])

    def test_cards_stay_in_slot_order_when_slot_1_is_lost_and_slot_2_stays(self):
        self.second_vassal()
        self.set_state("vassal1_region", "none")
        self.record_wiped(1, "Krumme", 50)
        cards = self.view()["cards"]
        self.assertEqual([(c["kind"], c["title"]) for c in cards], [("wiped", "Krumme"), ("vassal", "Goldhof"), ("free", "Free slot")])
        self.assertEqual(cards[1]["slot"], 2)

    def test_more_wiped_records_than_free_cards_show_the_oldest_ones(self):
        self.second_vassal()
        for index, region in enumerate(("A", "B", "C"), start=1):
            self.record_wiped(index, region, 10 * index)
        cards = self.view()["cards"]
        self.assertEqual([c["title"] for c in cards], ["Eichenhau", "Goldhof", "A"])

    def test_a_wiped_card_has_no_lord_no_policy_buttons_and_a_restore_button(self):
        self.record_wiped(1, "Krumme", 50)
        card = self.card(1)
        self.assertEqual((card["status_text"], card["lord_line"], card["policies"]), ("Wiped", "No lord", []))
        self.assertEqual(card["restore"], {"text": "Restore the village", "cost": 100, "enabled": True, "hint": "Costs 100 silver.", "region": "Krumme"})
        self.assertIn("Hussite sack", card["note"])


class PolicyClickTests(MenuBase):
    def test_a_click_on_heavy_sets_the_policy_of_that_slot(self):
        self.assertEqual(self.policy(1), "fair")
        self.assertTrue(self.click("PolicyButton0_2"))
        self.assertEqual(self.policy(1), "heavy")
        self.assertEqual(self.card(0)["policy_hint"], "Tribute x1.5: 150 of each rich resource")
        self.assertTrue(self.card(0)["policies"][2]["selected"])

    def test_the_next_tribute_is_1_5_times_the_fair_tribute(self):
        self.deposit("iron")
        self.deposit("salt")
        self.click("PolicyButton0_2")
        self.calendar.month = 4
        self.game.advance(5)
        payment = self.ask("tribute_state")["result"]["history"][-1]["payments"][0]
        self.assertEqual((payment["policy"], payment["amount"]), ("heavy", 150))

    def test_a_refused_command_leaves_the_selection_and_shows_the_reason(self):
        self.game.exec(REFUSE_POLICY)
        self.assertFalse(self.click("PolicyButton0_0"))
        self.assertEqual(self.policy(1), "fair")
        self.assertTrue(self.card(0)["policies"][1]["selected"])
        shown = self.ask("vassals_menu_state")["result"]["wanted_texts"]
        self.assertEqual(shown["NoteText0"], "policy refused for the test")

    def test_a_click_on_a_free_slot_runs_no_command(self):
        self.game.exec(SPY)
        self.assertIsNone(self.click("PolicyButton1_2"))
        self.assertEqual(self.game.exec("return CALLS"), 0)

    def test_the_policy_command_gets_the_slot_of_the_card(self):
        self.second_vassal()
        self.click("PolicyButton1_0")
        self.assertEqual((self.policy(1), self.policy(2)), ("fair", "light"))


class RestoreClickTests(MenuBase):
    def setUp(self):
        super().setUp()
        self.add_families("Eichenhau", 4)
        self.ask("vassals_sack", slot=1)
        self.game.advance(150)
        self.game.exec("SETTLES = {}")

    def test_the_sacked_village_shows_a_restore_card(self):
        card = self.card(0)
        self.assertEqual((card["kind"], card["status_text"], card["title"]), ("wiped", "Wiped", "Eichenhau"))
        self.assertTrue(card["restore"]["enabled"])

    def test_a_restore_click_takes_100_silver_and_the_card_shows_rebuilding(self):
        self.game.exec(SPY)
        self.assertTrue(self.click("RestoreButton0"))
        self.assertEqual((self.game.exec("return CALLS"), self.pawn.silver), (1, 400))
        card = self.card(0)
        self.assertEqual((card["kind"], card["status_text"], card["stats"][2]), ("vassal", "Rebuilding", "none"))
        self.assertEqual(self.view()["silver_text"], "400 silver")

    def test_with_less_than_100_silver_the_button_is_disabled_and_no_command_runs(self):
        self.pawn.silver = 99
        self.game.exec(SPY)
        card = self.card(0)
        self.assertEqual((card["restore"]["enabled"], card["restore"]["hint"]), (False, "Needs 100 silver."))
        self.assertIsNone(self.click("RestoreButton0"))
        self.assertEqual((self.game.exec("return CALLS"), self.pawn.silver), (0, 99))

    def test_a_refused_restore_shows_the_reason_in_the_note_line(self):
        self.game.exec(REFUSE_RESTORE)
        self.assertFalse(self.click("RestoreButton0"))
        self.assertEqual(self.ask("vassals_menu_state")["result"]["wanted_texts"]["NoteText0"], "restore refused for the test")

    def test_the_restore_command_gets_the_region_and_nothing_else(self):
        self.game.exec(SPY)
        self.click("RestoreButton0")
        self.assertEqual(self.game.exec('return ARGS.region .. ":" .. tostring(next(ARGS, "region"))'), "Eichenhau:nil")


class CommandTests(MenuBase):
    def test_the_view_command_returns_the_header_and_one_card_for_each_slot(self):
        view = self.view()
        self.assertEqual(sorted(k for k in ("count_text", "tribute_text", "silver_text", "cards") if k in view), ["cards", "count_text", "silver_text", "tribute_text"])
        self.assertEqual([c["position"] for c in view["cards"]], [0, 1, 2])

    def test_the_menu_is_registered_in_the_bottom_bar_as_vassals(self):
        state = self.ask("menu_state")["result"]
        self.assertIn("vassals", state["registered"])
        row = next(r for r in state["buttons"] if r["id"] == "vassals")
        self.assertEqual(row["label"], "Vassals")

    def test_open_without_the_pak_gives_a_clear_message(self):
        answer = self.ask("vassals_menu_open")
        self.assertTrue(answer["ok"], answer)
        self.assertFalse(answer["result"]["ok"])
        self.assertTrue(answer["result"]["error"])

    def test_close_without_an_open_menu_is_fine(self):
        self.assertTrue(self.ask("vassals_menu_close")["result"]["ok"])

    def test_the_press_command_needs_an_open_window(self):
        self.assertFalse(self.ask("vassals_menu_press", button="PolicyButton0_2")["ok"])

    def test_the_window_tick_is_not_faster_than_100_ms(self):
        from test_fakegame_modstate import find_pack_mod
        source = (find_pack_mod() / "Scripts" / "features" / "vassals_menu" / "init.lua").read_text(encoding="utf-8")
        self.assertIn("math.max(100, config.poll_ms)", source)

    def test_the_menu_changes_state_only_through_the_two_commands(self):
        from test_fakegame_modstate import find_pack_mod
        source = (find_pack_mod() / "Scripts" / "features" / "vassals_menu" / "init.lua").read_text(encoding="utf-8")
        for word in ("set_policy(", "restore_vassal(", "state:set", "requestSaveFile", "SaveGameToSlot"):
            self.assertNotIn(word, source, word)
        self.assertIn('run_command("vassals_set_policy"', source)
        self.assertIn('run_command("vassals_restore"', source)


class ViewModuleTests(unittest.TestCase):
    """The pure functions, run in the fake game."""

    def setUp(self):
        from test_fakegame_vassals import VassalsTestCase
        self.case = VassalsTestCase("setUp")
        self.case.setUp()
        self.addCleanup(self.case.game.close)

    def run_lua(self, expression):
        return self.case.game.exec(f"local v = {VIEW}; return {expression}")

    def test_factor_text(self):
        self.assertEqual(self.run_lua("v.factor_text(0.5) .. ' ' .. v.factor_text(1.0) .. ' ' .. v.factor_text(1.5)"), "0.5 1 1.5")

    def test_days_as_vassal(self):
        self.assertEqual(self.run_lua("v.days_as_vassal(101, 112) .. ',' .. v.days_as_vassal(0, 112) .. ',' .. v.days_as_vassal(101, 90)"), "12,0,0")

    def test_region_text(self):
        self.assertEqual(self.run_lua("v.region_text('hochweg') .. ',' .. v.region_text('none')"), "Hochweg,-")


if __name__ == "__main__":
    unittest.main()
