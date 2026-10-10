"""Tests for the item table comparison (spec 09) with a fake reader. No game."""

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import runlib_path  # noqa: F401
from runlib import itemtable
from runlib.commands import CommandChannel
from runlib.expectations import Expectations
from runlib.scenario import SCENARIOS

VANILLA = {"row_count": 213, "rows": {"16": {"Value": 0.0, "Weight": 0.0}, "17": {"Value": 0.5, "spoilageRate": 0.09}}}


class FakeActions:
    """Reads rows from a dict. `rows` is the game state."""

    def __init__(self, rows, row_count=213):
        self.rows = rows
        self.row_count = row_count

    def datatable_info(self):
        return {"row_count": self.row_count}

    def datatable_read(self, row, field):
        return self.rows[row][field]


class FakeContext:
    def __init__(self, actions):
        self.actions = actions
        self.expect = Expectations()
        self.log = mock.Mock()

    def result(self):
        return self.expect.result()


def vanilla_state():
    return {row: dict(fields) for row, fields in VANILLA["rows"].items()}


class OverrideTests(unittest.TestCase):
    def test_empty_gives_no_override(self):
        self.assertEqual(itemtable.parse_overrides(None), {})
        self.assertEqual(itemtable.parse_overrides(""), {})

    def test_valid_override_replaces_one_field(self):
        rows = itemtable.expected_rows(VANILLA, itemtable.parse_overrides('{"17": {"Value": 0.75}}'))
        self.assertEqual(rows["17"], {"Value": 0.75, "spoilageRate": 0.09})
        self.assertEqual(VANILLA["rows"]["17"]["Value"], 0.5)  # the vanilla data is not changed

    def test_override_can_add_a_row(self):
        rows = itemtable.expected_rows(VANILLA, {"99": {"Value": 1}})
        self.assertEqual(rows["99"], {"Value": 1})

    def test_bad_overrides_are_refused(self):
        for text in ["{", "[]", '{"17": 5}', '{"17": {}}', '{"17": {"Name": 1}}', '{"17": {"Value": "x"}}', '{"17": {"Value": true}}']:
            with self.subTest(text=text), self.assertRaises(itemtable.ItemTableError):
                itemtable.parse_overrides(text)


class VanillaFileTests(unittest.TestCase):
    def test_the_committed_file_is_valid(self):
        data = itemtable.load_vanilla()
        self.assertEqual(data["row_count"], 213)
        self.assertGreaterEqual(len(data["rows"]), 20)
        for fields in data["rows"].values():
            self.assertEqual(sorted(fields), sorted(itemtable.FIELDS))

    def test_a_missing_or_broken_file_is_an_error(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaises(itemtable.ItemTableError):
                itemtable.load_vanilla(Path(folder) / "none.json")
            broken = Path(folder) / "broken.json"
            broken.write_text(json.dumps({"rows": []}), encoding="utf-8")
            with self.assertRaises(itemtable.ItemTableError):
                itemtable.load_vanilla(broken)


class CompareTests(unittest.TestCase):
    def compare(self, state, rows):
        expect = Expectations()
        itemtable.compare_rows(expect, lambda row, field: state[row][field], rows)
        return expect.result()

    def test_equal_rows_pass(self):
        self.assertTrue(self.compare(vanilla_state(), VANILLA["rows"])["passed"])

    def test_tiny_difference_passes_and_a_real_one_fails(self):
        state = vanilla_state()
        state["17"]["Value"] = 0.50001
        self.assertTrue(self.compare(state, VANILLA["rows"])["passed"])
        state["17"]["Value"] = 0.75
        self.assertFalse(self.compare(state, VANILLA["rows"])["passed"])

    def test_modified_value_passes_when_it_is_expected(self):
        state = vanilla_state()
        state["17"]["Value"] = 0.75
        rows = itemtable.expected_rows(VANILLA, {"17": {"Value": 0.75}})
        self.assertTrue(self.compare(state, rows)["passed"])


class ScenarioTests(unittest.TestCase):
    def run_scenario(self, state, row_count=213, env=None):
        run = SCENARIOS["datatable-vanilla"]
        vanilla = {"row_count": 213, "rows": VANILLA["rows"]}
        with mock.patch.object(itemtable, "load_vanilla", return_value=vanilla), mock.patch.dict("os.environ", env or {}, clear=False):
            return run(FakeContext(FakeActions(state, row_count)))

    def test_vanilla_game_passes(self):
        self.assertTrue(self.run_scenario(vanilla_state())["passed"])

    def test_wrong_row_count_fails(self):
        self.assertFalse(self.run_scenario(vanilla_state(), row_count=212)["passed"])

    def test_changed_value_fails_without_an_expectation(self):
        state = vanilla_state()
        state["17"]["Value"] = 0.75
        self.assertFalse(self.run_scenario(state)["passed"])

    def test_changed_value_passes_with_the_expectation_variable(self):
        state = vanilla_state()
        state["17"]["Value"] = 0.75
        env = {itemtable.EXPECT_ENV: '{"17": {"Value": 0.75}}'}
        self.assertTrue(self.run_scenario(state, env=env)["passed"])


class AnswerReadTests(unittest.TestCase):
    def test_answer_that_cannot_be_read_yet_is_retried(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "0001.result.json"
            self.assertIsNone(CommandChannel._read_answer(path))
            path.write_text('{"ok": tr', encoding="utf-8")
            self.assertIsNone(CommandChannel._read_answer(path))
            with mock.patch.object(Path, "read_text", side_effect=PermissionError):
                self.assertIsNone(CommandChannel._read_answer(path))
            path.write_text('{"ok": true}', encoding="utf-8")
            self.assertEqual(CommandChannel._read_answer(path), {"ok": True})


if __name__ == "__main__":
    unittest.main()
