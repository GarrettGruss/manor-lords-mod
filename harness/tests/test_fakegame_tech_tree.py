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

    def test_the_shipped_file_loads_with_two_paths_and_eight_nodes(self):
        tree = self.build(tree_document())
        self.assertEqual(len(tree.nodes), 8)
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

    def test_a_missing_layout_gets_a_default(self):
        document = tree_document()
        for node in document["nodes"]:
            del node["layout"]
        tree = self.build(document)
        self.assertEqual(tree.by_id["iron_hand"].layout.x, 1)
        self.assertEqual(tree.by_id["amnesty"].layout.x, 1)


class TechTreeTestCase(unittest.TestCase):
    def setUp(self):
        self.game = FakeGame()
        self.game.start()
        self.addCleanup(self.game.close)
        self.mod_name = PACK.name
        self.game.exec(f'package.path = "{(PACK / "Scripts").as_posix()}/?.lua;" .. package.path')
        self.game.exec(FNAME + HELPERS + STUB)
        self.pawn = self.game.obj("PawnCPP", Tags=self.game.array([]), commandedSquads=self.game.array([]))
        self.game.method(self.pawn, "playEventMessage", lambda _self, _kind, _text, _sub: None)
        self.game.method(self.pawn, "K2_GetActorLocation", lambda _self: self.game.struct(X=0.0, Y=0.0, Z=0.0))
        self.game.method(self.pawn, "GetAddress", lambda _self: 1)
        self.calendar = self.game.obj("TemporalComponent", daysTotal=61, daysUntilNextRaid=730, Season=1)
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


class PathAndSlotTests(TechTreeTestCase):
    def test_the_start_has_no_path_and_one_slot_at_level_one(self):
        state = self.state()
        self.assertEqual((state["path"], state["slots"], state["free_slots"]), ("none", 1, 1))
        self.assertEqual(len(state["nodes"]), 8)

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

    def test_one_slot_per_level_and_the_requirement_order(self):
        self.choose("oppression")
        self.assertIn("needs 'martial_law'", self.unlock("iron_hand")["error"])
        self.assertTrue(self.unlock("martial_law")["ok"])
        self.assertIn("no free node slot", self.unlock("iron_hand")["error"])
        self.region.settlementLevel = 2
        self.assertTrue(self.unlock("iron_hand")["ok"])
        self.assertEqual(self.state()["unlocked"], ["martial_law", "iron_hand"])

    def test_a_node_cannot_be_unlocked_twice(self):
        self.choose("prosperity")
        self.unlock("fair_courts")
        self.region.settlementLevel = 3
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
        self.region.settlementLevel = len(nodes)
        for node in nodes:
            answer = self.unlock(node)
            self.assertTrue(answer["ok"], answer)
        self.game.advance(4)

    def test_oppression_nodes_add_public_order(self):
        # approval 65 gives a debuff of 35: order 100 - 35 = 65. Martial Law and Iron Hand add 10 and 15.
        self.game.advance(3)
        self.assertEqual(self.region.publicOrder, 65)
        self.unlock_chain("oppression", ["martial_law", "iron_hand"])
        self.assertEqual(self.region.publicOrder, 90)

    def test_fear_of_the_lord_needs_four_squads(self):
        self.unlock_chain("oppression", ["martial_law", "iron_hand", "veteran_levies", "fear_of_the_lord"])
        self.assertEqual(self.region.publicOrder, 90)  # 100 - 35 + 25; the last 25 waits for 4 squads
        self.assertEqual(self.state()["totals"]["order_bonus"], 25)

    def test_fear_of_the_lord_counts_with_four_squads(self):
        self.pawn.commandedSquads = self.game.array([1, 2, 3, 4])
        self.unlock_chain("oppression", ["martial_law", "iron_hand", "veteran_levies", "fear_of_the_lord"])
        self.assertEqual(self.state()["totals"]["order_bonus"], 50)
        self.assertEqual(self.region.publicOrder, 100)

    def test_prosperity_raises_the_approval_used_by_the_debuff(self):
        self.unlock_chain("prosperity", ["fair_courts"])
        self.assertEqual(self.region.publicOrder, 70)  # approval 65 + 5 gives a debuff of 30
        self.assertEqual(self.region.Approval, 65)     # the real approval is not written

    def test_golden_age_removes_the_debuff_at_high_approval(self):
        self.region.Approval = 90
        self.unlock_chain("prosperity", ["fair_courts", "amnesty", "militia_rights", "golden_age"])
        self.assertEqual(self.region.publicOrder, 100)  # approval 90 + 5 + 15 is capped at 100

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
        self.region.settlementLevel = 3
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
