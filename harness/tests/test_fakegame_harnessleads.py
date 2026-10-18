"""Mock tests for HarnessLeads (change spike-community-mod-leads, issue #280): the probe commands on fake objects.

The fake world only checks the code paths and the input checks. The real game answers (signatures, values) come from the probes.
"""

import unittest

import fakegame_path  # noqa: F401
from fakegame import FakeGame

SETUP = """
FName = function(text) return { fname = text } end
package.loaded["HarnessDataTable"] = { has_row = function(name) return name == "spearMilitia" end }
"""


def leads(game, call: str):
    return game.lua.eval(f'(function() local m = require("HarnessLeads"); return {call} end)()')


class GearTests(unittest.TestCase):
    def test_reads_slots_for_the_units_of_one_squad(self):
        with FakeGame() as game:
            game.exec(SETUP)
            for squad, dead in ((7, False), (7, True), (8, False)):
                unit = game.obj("SMUnit", dead=dead, assignedSquadID=game.struct(Value=squad), ItemsLooted=2)
                game.method(unit, "GetEquippedID", lambda _self, slot: game.struct(Value=100 + slot))
            answer = leads(game, "m.lead_unit_gear({ squad = 7 })")
            self.assertEqual((answer["units"], answer["dead"]), (2, 1))
            self.assertEqual(list(answer["rows"][1]["gear"].values()), [100, 101, 102, 103])

    def test_a_failing_slot_call_is_reported_as_text(self):
        with FakeGame() as game:
            game.exec(SETUP)
            unit = game.obj("SMUnit", dead=False, assignedSquadID=game.struct(Value=3))
            game.method(unit, "GetEquippedID", lambda _self, _slot: (_ for _ in ()).throw(RuntimeError("bad slot")))
            gear = leads(game, "m.lead_unit_gear({ squad = 3 })")["rows"][1]["gear"]
            self.assertIn("error", str(gear[1]))

    def test_bad_squad_is_refused(self):
        with FakeGame() as game:
            game.exec(SETUP)
            self.assertFalse(leads(game, "m.lead_unit_gear({ squad = 0 })")["ok"])


class StanceTests(unittest.TestCase):
    def test_reads_then_sets_a_stance(self):
        with FakeGame() as game:
            game.exec(SETUP)
            state = {"stance": 0}
            component = game.obj("SquadComponent")
            game.method(component, "GetSquad", lambda _self, _handle: game.struct(behaviourStance=state["stance"]))

            def set_stance(_self, _handle, value, _voice):
                state["stance"] = value

            game.method(component, "SetBehaviourStance", set_stance)
            answer = leads(game, 'm.lead_stance({ squad = 5, stance = "aggressive" })')
            self.assertEqual((answer["before"], answer["after"]), (0, 1))

    def test_unknown_stance_is_refused(self):
        with FakeGame() as game:
            game.exec(SETUP)
            game.obj("SquadComponent")
            self.assertFalse(leads(game, 'm.lead_stance({ squad = 5, stance = "wild" })')["ok"])


class SpawnTests(unittest.TestCase):
    def test_bad_template_and_count_are_refused(self):
        with FakeGame() as game:
            game.exec(SETUP)
            game.obj("RTSMultiEngineCPP")
            self.assertFalse(leads(game, 'm.lead_spawn_unit({ lord = 1, template = "nope" })')["ok"])
            self.assertFalse(leads(game, 'm.lead_spawn_unit({ lord = 1, template = "spearMilitia", count = 99 })')["ok"])


class MeshTests(unittest.TestCase):
    def build(self, game):
        game.exec(SETUP)
        old = game.obj("StaticMesh", "/Game/Fake/Old.Old")
        new = game.obj("StaticMesh", "/Game/Fake/New.New")
        owner = game.obj("SMBuilding_Fake_C", "/Game/Fake/Owner")
        game.method(owner, "K2_GetActorLocation", lambda _self: game.struct(X=1.0, Y=2.0, Z=3.0))
        component = game.obj("StaticMeshComponent", "/Game/Fake/Owner.Comp", StaticMesh=old)
        game.method(component, "GetOwner", lambda _self: owner)
        game.method(component, "SetStaticMesh", lambda self, mesh: setattr(self, "StaticMesh", mesh))
        game.method(component, "GetAllSocketNames", lambda _self: game.array([]))
        for mesh, path in ((old, "/Game/Fake/Old.Old"), (new, "/Game/Fake/New.New")):
            game.method(mesh, "GetPathName", lambda _self, path=path: path)
        game.static("/Game/Fake/New.New", new)
        return component

    def test_swap_then_restore(self):
        with FakeGame() as game:
            self.build(game)
            rows = leads(game, "m.lead_mesh_list()")["components"]
            self.assertEqual(len(rows), 1)
            name = rows[1]["full"]
            swapped = leads(game, f'm.lead_mesh_swap({{ component = "{name}", mesh = "/Game/Fake/New.New" }})')
            self.assertTrue(swapped["ok"], swapped)
            self.assertNotEqual(swapped["before"]["mesh"], swapped["after"]["mesh"])
            back = leads(game, f'm.lead_mesh_swap({{ component = "{name}", restore = true }})')
            self.assertEqual(back["after"]["mesh"], swapped["before"]["mesh"])

    def test_unknown_component_and_missing_mesh_are_refused(self):
        with FakeGame() as game:
            self.build(game)
            self.assertFalse(leads(game, 'm.lead_mesh_swap({ component = "x", mesh = "y" })')["ok"])
            name = leads(game, "m.lead_mesh_list()")["components"][1]["full"]
            self.assertFalse(leads(game, f'm.lead_mesh_swap({{ component = "{name}", mesh = "/Game/None.None" }})')["ok"])


if __name__ == "__main__":
    unittest.main()
