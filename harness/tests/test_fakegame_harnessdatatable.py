"""Mock test for the DataTable commands of HarnessActions (spec 09, first check): only listed number fields, only one table."""

import json
import unittest

import fakegame_path  # noqa: F401
from fakegame import FakeGame


def build_world(game):
    rows = {"16": game.obj("ItemRow", Value=0.5, Weight=0, Name="secret"), "17": game.obj("ItemRow", Value=2.0, Weight=0)}
    table = game.obj("DataTable", _path="/Game/NotStronghold/Data/DT_Items.DT_Items")
    game.method(table, "GetRowNames", lambda _self: game.lua.table_from(list(rows)))
    game.method(table, "GetRowStruct", lambda _self: game.obj("ScriptStruct", _path="/Script/ManorLords.Item"))
    game.method(table, "FindRow", lambda _self, name: rows.get(name))
    game.obj("RTSMultiEngineCPP", itemStats=table)
    return rows


def send(game, number, body):
    folder = game.run_dir / "commands"
    folder.mkdir(exist_ok=True)
    (folder / f"{number:04d}.json").write_text(json.dumps({"id": f"{number:04d}", **body}), encoding="utf-8")
    game.advance(1)
    return json.loads((folder / f"{number:04d}.result.json").read_text(encoding="utf-8"))


class DataTableCommandTests(unittest.TestCase):
    def start(self, game):
        rows = build_world(game)
        game.load_mod("HarnessActions")
        game.advance(1)
        return rows

    def test_info_lists_the_row_names_and_the_row_struct(self):
        with FakeGame() as game:
            self.start(game)
            answer = send(game, 1, {"command": "datatable_info"})
            self.assertEqual(answer["info"]["names"], ["16", "17"])
            self.assertIn("ScriptStruct", answer["info"]["row_struct"])

    def test_read_gives_one_number_field(self):
        with FakeGame() as game:
            self.start(game)
            answer = send(game, 1, {"command": "datatable_read", "row": "16", "field": "Value"})
            self.assertEqual(answer["values"], {"Value": 0.5})

    def test_a_field_that_is_not_listed_is_refused_and_not_read(self):
        with FakeGame() as game:
            self.start(game)
            answer = send(game, 1, {"command": "datatable_read", "row": "16", "field": "Name"})
            self.assertFalse(answer["ok"])
            self.assertIn("not allowed", answer["error"])

    def test_write_changes_the_row_and_reads_it_back(self):
        with FakeGame() as game:
            rows = self.start(game)
            answer = send(game, 1, {"command": "datatable_write", "row": "17", "field": "Value", "value": 3.5})
            self.assertEqual((answer["change"]["before"], answer["change"]["after"]), (2.0, 3.5))
            self.assertEqual(rows["17"].Value, 3.5)

    def test_write_to_a_field_that_is_not_listed_is_refused(self):
        with FakeGame() as game:
            rows = self.start(game)
            answer = send(game, 1, {"command": "datatable_write", "row": "16", "field": "Name", "value": 1})
            self.assertFalse(answer["ok"])
            self.assertEqual(rows["16"].Name, "secret")

    def test_unknown_row_and_missing_arguments_give_clear_errors(self):
        with FakeGame() as game:
            self.start(game)
            self.assertIn("no row named", send(game, 1, {"command": "datatable_read", "row": "99", "field": "Value"})["error"])
            self.assertIn("required", send(game, 2, {"command": "datatable_write", "row": "16", "field": "Value"})["error"])


if __name__ == "__main__":
    unittest.main()
