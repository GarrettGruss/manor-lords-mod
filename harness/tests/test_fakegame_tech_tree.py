"""Tests for the feature tech_tree of the pack mod (mod feature M12) in the fake game, and for its pure loader.

They run the real Lua files. HarnessBandits and HarnessUnits are stubs.
They do not prove how the real game behaves (see the real-game runs in the iteration files).
"""

import json
import unittest

import fakegame_path  # noqa: F401
from fakegame import FakeGame
from lupa import LuaRuntime
from test_fakegame_modstate import FNAME, HELPERS, find_pack_mod

PACK = find_pack_mod()
TREE_FILE = PACK / "data" / "tech_tree" / "tree.json"

STUB = """
package.loaded["HarnessBandits"] = {
    homeless_rebel = function(request) return { ok = true, families_removed = request.count, squads = { {} }, bandit_units_spawned = 18 } end,
    bandit_tag = function() return { ok = true } end,
    bandit_letter = function() BANDIT_LETTERS = (BANDIT_LETTERS or 0) + 1; return { ok = true } end,
}
package.loaded["HarnessUnits"] = {
    counts = function() return { by_side = { bandit = BANDIT_UNITS or 0 } } end,
    squadMap = function() return SQUAD_MAP or {} end,
}
"""


def tree_document() -> dict:
    return json.loads(TREE_FILE.read_text(encoding="utf-8"))


class LoaderTests(unittest.TestCase):
    """The pure loader (tree.lua) with documents made in Python."""

    def setUp(self):
        self.lua = LuaRuntime()
        self.lua.execute(f'package.path = "{(PACK / "Scripts").as_posix()}/?.lua;{(PACK.parent / "shared").as_posix()}/?/?.lua;" .. package.path')
        self.loader = self.lua.execute('return (require("features.tech_tree.tree"))')
        self.json = self.lua.execute('return (require("HarnessJson"))')

    def build(self, document):
        decoded = self.json.decode(json.dumps(document))
        problem = None
        self.assertIsNotNone(decoded, problem)
        return self.loader.build(decoded)

    def assert_refused(self, document, text):
        with self.assertRaises(Exception) as caught:
            self.build(document)
        self.assertIn(text, str(caught.exception))

    def test_the_shipped_file_loads_with_two_paths_eight_nodes_and_three_common_techs(self):
        tree = self.build(tree_document())
        self.assertEqual(len(tree.nodes), 8)
        self.assertEqual(len(tree.common_nodes), 3)
        self.assertEqual(len(tree.laws), 9)
        self.assertEqual([tree.paths[i].id for i in (1, 2)], ["oppression", "prosperity"])

    def test_an_unknown_required_id_is_refused(self):
        document = tree_document()
        document["nodes"][1]["requires"] = ["nope"]
        self.assert_refused(document, "requires unknown node 'nope'")

    def test_a_cycle_is_refused(self):
        document = tree_document()
        document["nodes"][0]["requires"] = ["fear_of_the_lord"]
        self.assert_refused(document, "cycle in requires")

    def test_a_requirement_across_paths_is_refused(self):
        document = tree_document()
        document["nodes"][4]["requires"] = ["martial_law"]
        self.assert_refused(document, "another path")

    def test_a_duplicate_id_is_refused(self):
        document = tree_document()
        document["nodes"][1]["id"] = "martial_law"
        self.assert_refused(document, "duplicate node id")

    def test_an_unknown_path_and_an_unknown_effect_kind_are_refused(self):
        document = tree_document()
        document["nodes"][0]["path"] = "third"
        self.assert_refused(document, "unknown path")
        document = tree_document()
        document["nodes"][0]["effect"][0]["kind"] = "magic"
        self.assert_refused(document, "unknown kind")

    def test_a_common_tech_may_not_require_a_node_and_needs_a_known_id(self):
        document = tree_document()
        document["common_nodes"][0]["requires"] = ["martial_law"]
        self.assert_refused(document, "may not require")
        document = tree_document()
        document["common_nodes"][0]["id"] = "martial_law"
        self.assert_refused(document, "duplicate node id")

    def test_a_missing_layout_gets_a_default(self):
        document = tree_document()
        for node in document["nodes"]:
            del node["layout"]
        tree = self.build(document)
        self.assertEqual(tree.by_id["iron_hand"].layout.x, 1)
        self.assertEqual(tree.by_id["amnesty"].layout.x, 1)


class TechTreeTestCase(unittest.TestCase):
    START_SEASON = 1  # the season of the calendar when the game starts (spring is 0 in these tests)

    def setUp(self):
        self.game = FakeGame()
        self.game.start()
        self.addCleanup(self.game.close)
        self.mod_name = PACK.name
        self.game.exec(f'package.path = "{(PACK / "Scripts").as_posix()}/?.lua;" .. package.path')
        self.game.exec(FNAME + HELPERS + STUB)
        self.game.exec('require("config").tech_tree.spring_season = 0')  # the tests use spring = 0; the real value is in notes/spring-season.md
        self.pawn = self.game.obj("PawnCPP", Tags=self.game.array([]), commandedSquads=self.game.array([]))
        self.game.method(self.pawn, "playEventMessage", lambda _self, _kind, _text, _sub: None)
        self.game.method(self.pawn, "K2_GetActorLocation", lambda _self: self.game.struct(X=0.0, Y=0.0, Z=0.0))
        self.game.method(self.pawn, "GetAddress", lambda _self: 1)
        self.calendar = self.game.obj("TemporalComponent", daysTotal=61, daysUntilNextRaid=730, Season=self.START_SEASON)
        self.region = self.game.obj("Region", ownerPawn=self.pawn, publicOrder=100, Approval=65, settlementLevel=1)
        self.game.method(self.region, "getTotalNumFamilies", lambda _self: 10)
        self.game.method(self.region, "getAvailableLivingSpace", lambda _self: self.game.struct(constructed=4, unconstructed=0))
        self.pawn.silver = 500
        self.engine = self.game.obj("RTSMultiEngineCPP", playerRef=self.pawn, TemporalComponent=self.calendar,
                                    regions=self.game.array([self.region]), debugLog_AI_general=self.game.array([]))
        self.game.method(self.engine, "getGameTimeAdjusted", lambda _self: 1000.0)
        self.game.load_mod(self.mod_name)
        self.game.advance(3)
        self.counter = 0
        self.ask("invasion_set_difficulty", value=1)  # these tests use the numbers of level 1; the mod default is level 2

    def ask(self, name, **args):
        self.counter += 1
        folder = self.game.run_dir / "modcmd" / self.mod_name
        folder.mkdir(parents=True, exist_ok=True)
        body = {"id": f"{self.counter:04d}", "command": f"{self.mod_name}.{name}", "args": args}
        (folder / f"{self.counter:04d}.json").write_text(json.dumps(body), encoding="utf-8")
        self.game.advance(1)
        return json.loads((folder / f"{self.counter:04d}.result.json").read_text(encoding="utf-8"))

    def state(self):
        answer = self.ask("tech_tree_state")
        self.assertTrue(answer["ok"], answer)
        return answer["result"]

    def choose(self, path):
        return self.ask("tech_tree_choose_path", path=path)

    def unlock(self, node):
        return self.ask("tech_tree_unlock", node=node)

    def grant(self, count):
        """Add picks at once (the start already gave one)."""
        if count > 0:
            self.assertTrue(self.ask("tech_tree_test_grant_picks", count=count)["ok"])

    def new_season(self, season):
        """The calendar enters a new season; the invasion feature counts it."""
        self.calendar.daysTotal = self.calendar.daysTotal + 91
        self.calendar.Season = season
        self.game.advance(4)


class PathAndSlotTests(TechTreeTestCase):
    def test_the_start_has_no_path_and_the_initial_pick(self):
        state = self.state()
        self.assertEqual((state["path"], state["picks_earned"], state["free_picks"]), ("none", 1, 1))
        self.assertEqual(len(state["nodes"]), 8)
        self.assertEqual([row["id"] for row in state["common_nodes"]], ["corpse_robbing", "armory_census", "night_watch"])

    def test_a_node_needs_a_path(self):
        answer = self.unlock("martial_law")
        self.assertFalse(answer["ok"])
        self.assertIn("no path", answer["error"])

    def test_the_path_choice_is_final(self):
        self.assertTrue(self.choose("oppression")["ok"])
        answer = self.choose("prosperity")
        self.assertFalse(answer["ok"])
        self.assertIn("already chosen", answer["error"])
        self.assertEqual(self.state()["path"], "oppression")

    def test_an_unknown_path_is_refused(self):
        self.assertFalse(self.choose("third")["ok"])

    def test_the_other_path_cannot_be_used(self):
        self.choose("oppression")
        answer = self.unlock("fair_courts")
        self.assertIn("other path", answer["error"])

    def test_one_pick_per_unlock_and_the_requirement_order(self):
        self.choose("oppression")
        self.assertIn("needs 'martial_law'", self.unlock("iron_hand")["error"])
        self.assertTrue(self.unlock("martial_law")["ok"])
        self.assertIn("no free pick", self.unlock("iron_hand")["error"])
        self.grant(1)
        self.assertTrue(self.unlock("iron_hand")["ok"])
        self.assertEqual(self.state()["unlocked"], ["martial_law", "iron_hand"])

    def test_a_node_cannot_be_unlocked_twice(self):
        self.choose("prosperity")
        self.unlock("fair_courts")
        self.grant(2)
        self.assertIn("already unlocked", self.unlock("fair_courts")["error"])

    def test_the_choice_is_kept_in_the_pawn_tags(self):
        self.choose("prosperity")
        self.unlock("fair_courts")
        tags = list(self.game.lua.eval("tag_names")(self.pawn).values())
        self.assertIn("invasion:tech_path=prosperity", tags)
        self.assertIn("invasion:tech_nodes=fair_courts", tags)


class EffectTests(TechTreeTestCase):
    def unlock_chain(self, path, nodes):
        self.choose(path)
        self.grant(len(nodes) - 1)
        for node in nodes:
            answer = self.unlock(node)
            self.assertTrue(answer["ok"], answer)
        self.game.advance(4)

    def manor_term(self):
        self.ask("bandits_set_order", value=0)
        return self.ask("bandits_tick_now")["result"]["last_tick"]["manor_term"]

    def test_oppression_nodes_add_public_order(self):
        # Martial Law and Iron Hand add 10 and 15 to the manor term of each tick (base 10).
        self.game.advance(3)
        self.assertEqual(self.manor_term(), 10)
        self.unlock_chain("oppression", ["martial_law", "iron_hand"])
        self.assertEqual(self.manor_term(), 35)

    def test_fear_of_the_lord_needs_four_squads(self):
        self.unlock_chain("oppression", ["martial_law", "iron_hand", "veteran_levies", "fear_of_the_lord"])
        self.assertEqual(self.manor_term(), 35)  # the last 25 waits for 4 squads
        self.assertEqual(self.state()["totals"]["order_bonus"], 25)

    def test_fear_of_the_lord_counts_with_four_squads(self):
        self.pawn.commandedSquads = self.game.array([1, 2, 3, 4])
        self.unlock_chain("oppression", ["martial_law", "iron_hand", "veteran_levies", "fear_of_the_lord"])
        self.assertEqual(self.state()["totals"]["order_bonus"], 50)
        self.assertEqual(self.manor_term(), 60)

    def test_prosperity_approval_bonus_has_no_effect_on_order(self):
        self.unlock_chain("prosperity", ["fair_courts"])
        self.assertEqual(self.manor_term(), 10)  # approval_bonus is not used by the order rules
        self.assertEqual(self.region.Approval, 65)

    def test_buy_back_price_factor_of_the_nodes(self):
        self.assertEqual(self.state()["totals"]["buy_back_multiplier"], 1)
        self.unlock_chain("oppression", ["martial_law", "iron_hand"])
        self.assertAlmostEqual(self.ask("bandits_state")["result"]["buy_back_multiplier"], 1.25)

    def test_amnesty_halves_the_price(self):
        self.unlock_chain("prosperity", ["fair_courts", "amnesty"])
        self.assertAlmostEqual(self.ask("bandits_state")["result"]["buy_back_multiplier"], 0.5)

    def test_militia_factors_reach_unit_balance(self):
        self.unlock_chain("prosperity", ["fair_courts", "amnesty", "militia_rights"])
        militia = self.state()["militia"]
        self.assertAlmostEqual(militia["attack_factor"], 1.1)
        self.assertEqual(militia["defence_factor"], 1)


class MilitiaFactorTests(TechTreeTestCase):
    def make_unit(self, squad, role, number):
        unit = self.game.obj("SMUnit", dead=False, att=10.0, block=2.0, assignedSquadID=self.game.struct(Value=squad),
                             currentUnitRole=role, **{"def": 20.0})
        self.game.method(unit, "GetAddress", lambda _self: number)
        return unit

    def setUp(self):
        super().setUp()
        self.game.exec('SQUAD_MAP = { [7] = { side = "player" }, [8] = { side = "bandit" } }')
        self.militia = self.make_unit(7, 0, 6001)
        self.bandit = self.make_unit(8, 0, 6002)
        self.retinue = self.make_unit(7, 5, 6003)

    def unlock_militia_rights(self):
        self.choose("prosperity")
        self.grant(2)
        for node in ("fair_courts", "amnesty", "militia_rights"):
            self.assertTrue(self.unlock(node)["ok"])
        self.game.advance(8)

    def test_only_player_militia_gets_the_attack_factor(self):
        self.unlock_militia_rights()
        self.assertAlmostEqual(self.militia.att, 11.0)
        self.assertEqual(self.bandit.att, 10.0)
        self.assertEqual(self.retinue.att, 10.0)
        self.assertEqual(self.militia.block, 2.0)

    def test_the_factor_is_not_applied_twice(self):
        self.unlock_militia_rights()
        self.game.advance(12)
        self.assertAlmostEqual(self.militia.att, 11.0)


class WidgetFeatureTests(TechTreeTestCase):
    """The pak cannot load in the fake game: these tests cover the text rules, the view and the message without the pak."""

    def test_open_without_the_pak_gives_a_clear_message(self):
        answer = self.ask("tech_tree_widget_open")
        self.assertTrue(answer["ok"], answer)
        self.assertFalse(answer["result"]["ok"])
        self.assertTrue(answer["result"]["error"])

    def test_the_wanted_lines_follow_the_tree(self):
        wanted = self.ask("tech_tree_widget_state")["result"]["wanted_lines"]
        self.assertEqual(wanted[0], "Path: not chosen yet")
        self.assertEqual(wanted[1], "Node slots: 1 free of 1 (settlement level 1)")
        self.assertEqual(wanted[2], "Effects: none")
        self.choose("oppression")
        self.unlock("martial_law")
        wanted = self.ask("tech_tree_widget_state")["result"]["wanted_lines"]
        self.assertEqual(wanted, ["Path: Oppression (final)", "Node slots: 0 free of 1 (settlement level 1)", "Effects: Public Order +10"])

    def test_effect_text_lists_every_change(self):
        text = self.game.exec(
            "return require('features.tech_tree.rules').describe_totals({ order_bonus = 25, approval_bonus = 0, buy_back_multiplier = 1.25,"
            " militia_attack_multiplier = 1, militia_defence_multiplier = 1.1 })")
        self.assertEqual(text, "Public Order +25, Buy-back price x1.25, Militia defence x1.10")


class PicksTests(TechTreeTestCase):
    """Change update-tech-tree-yearly-picks: one pick at the start and one at each start of spring."""

    START_SEASON = 2  # autumn

    def picks(self):
        state = self.state()
        return state["picks_earned"], state["free_picks"]

    def test_the_start_gives_the_initial_pick_in_every_season(self):
        self.assertEqual(self.picks(), (1, 1))

    def test_only_spring_gives_a_pick_and_an_autumn_start_gets_it_at_the_next_spring(self):
        self.new_season(3)  # winter
        self.assertEqual(self.picks(), (1, 1))
        self.new_season(0)  # spring
        self.assertEqual(self.picks(), (2, 2))
        for season in (1, 2, 3):  # summer, autumn, winter
            self.new_season(season)
        self.assertEqual(self.picks(), (2, 2))

    def test_the_same_spring_gives_one_pick_only(self):
        self.new_season(0)
        self.game.advance(20)
        self.assertEqual(self.picks(), (2, 2))

    def test_unused_picks_are_banked(self):
        for _ in range(3):
            self.new_season(1)
            self.new_season(0)
        self.assertEqual(self.picks(), (4, 4))

    def test_the_picks_are_kept_in_the_pawn_tags(self):
        self.new_season(0)
        tags = list(self.game.lua.eval("tag_names")(self.pawn).values())
        self.assertIn("invasion:tech_picks_earned=2", tags)
        self.assertTrue(any(tag.startswith("invasion:tech_spring_no=") and tag != "invasion:tech_spring_no=-1" for tag in tags), tags)

    def test_a_pick_is_spent_on_each_unlock_and_the_level_does_not_matter(self):
        self.choose("oppression")
        self.assertTrue(self.unlock("martial_law")["ok"])
        self.assertEqual(self.picks(), (1, 0))
        self.assertIn("no free pick", self.unlock("iron_hand")["error"])
        self.new_season(0)
        self.assertTrue(self.unlock("iron_hand")["ok"])
        self.assertEqual(self.region.settlementLevel, 1)

    def test_three_free_picks_buy_three_unlocks_at_level_one(self):
        self.grant(2)
        self.choose("prosperity")
        for node in ("fair_courts", "amnesty", "militia_rights"):
            self.assertTrue(self.unlock(node)["ok"], node)
        self.assertEqual(self.picks(), (3, 0))


class SpringStartTests(TechTreeTestCase):
    START_SEASON = 0  # the game starts in spring

    def test_a_spring_start_gives_the_initial_pick_only(self):
        state = self.state()
        self.assertEqual((state["picks_earned"], state["free_picks"]), (1, 1))
        self.game.advance(10)
        self.assertEqual(self.state()["picks_earned"], 1)
        for season in (1, 2, 3):
            self.new_season(season)
        self.assertEqual(self.state()["picks_earned"], 1)
        self.new_season(0)
        self.assertEqual(self.state()["picks_earned"], 2)


class CommonTechTests(TechTreeTestCase):
    def test_a_common_tech_needs_no_path(self):
        answer = self.unlock("night_watch")
        self.assertTrue(answer["ok"], answer)
        state = self.state()
        self.assertEqual((state["path"], state["unlocked"], state["free_picks"]), ("none", ["night_watch"], 0))
        self.assertEqual([row["status"] for row in state["common_nodes"]], ["locked", "locked", "unlocked"])

    def test_a_path_node_with_no_path_costs_no_pick(self):
        self.assertIn("no path is chosen", self.unlock("martial_law")["error"])
        self.assertEqual(self.state()["free_picks"], 1)

    def test_a_taken_common_tech_is_refused_and_costs_nothing(self):
        self.grant(1)
        self.unlock("armory_census")
        self.assertIn("already unlocked", self.unlock("armory_census")["error"])
        self.assertEqual(self.state()["free_picks"], 1)

    def test_the_oppression_path_unlocks_a_common_tech_out_of_order(self):
        self.choose("oppression")
        self.assertTrue(self.unlock("armory_census")["ok"])
        self.assertEqual(self.state()["unlocked"], ["armory_census"])

    def test_a_common_tech_after_the_other_path_choice_still_works(self):
        self.choose("prosperity")
        self.assertTrue(self.unlock("corpse_robbing")["ok"])
        self.assertEqual(self.state()["free_picks"], 0)
