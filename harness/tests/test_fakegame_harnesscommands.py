"""Tests for the command registry HarnessCommands and the JSON decoder (spec 10, U10), run in the fake game kit.

The dispatch through the HarnessActions mod uses the real mod file in the kit (the file channel, no game).
"""

import json
import re
import unittest
from pathlib import Path

import fakegame_path  # noqa: F401
from fakegame import FakeGame
from modstate_support import call, dispatch
from test_fakegame_harnessactions import commands_dir, result, send, start

MOD_DIR = Path(__file__).resolve().parents[2] / "mod"
SCHEMA = """{ amount = { type = "integer", required = true, min = 1, max = 10 },
              note = { type = "string", maxLength = 5 },
              ratio = { type = "number", min = 0, max = 1 },
              flag = { type = "boolean" },
              kind = { type = "string", oneOf = { "a", "b" } } }"""


def lua_register(game, name="Test.add", handler="function(args) return { got = args } end", schema=SCHEMA):
    game.exec(f'require("HarnessCommands").register("{name}", {handler}, {schema})')


def registration_error(game, name, handler="function() return 1 end", schema="{}"):
    with unittest.TestCase().assertRaises(Exception) as caught:
        lua_register(game, name, handler, schema)
    return str(caught.exception)


class RegisterTests(unittest.TestCase):
    def test_a_valid_command_runs_with_checked_arguments(self):
        with FakeGame() as game:
            lua_register(game)
            answer = dispatch(game, "Test.add", {"amount": 3, "note": "abc", "ratio": 0.5, "flag": True, "kind": "b"})
            self.assertEqual(answer, {"ok": True, "result": {"got": {"amount": 3, "note": "abc", "ratio": 0.5, "flag": True, "kind": "b"}}})

    def test_good_names_are_accepted(self):
        with FakeGame() as game:
            for name in ("A.b", "InvasionStandIn.found_outpost", "mod_1.cmd2"):
                lua_register(game, name, schema="{}")
            names = [command["name"] for command in call(game, "harness.list_commands")["commands"]]
            self.assertEqual(names, ["A.b", "InvasionStandIn.found_outpost", "harness.list_commands", "mod_1.cmd2"])

    def test_bad_names_are_refused(self):
        bad = ["nodot", "a.b.c", "1Mod.cmd", "Mod.1cmd", "Mod.", ".cmd", "Mod.cm d", "Mod.cmd;x", "Mod-x.cmd", ""]
        with FakeGame() as game:
            for name in bad:
                with self.subTest(name=name):
                    self.assertIn("ModName.command", registration_error(game, name.replace("\n", "\\n")))

    def test_the_harness_prefix_is_reserved(self):
        with FakeGame() as game:
            self.assertIn("reserved", registration_error(game, "harness.evil"))

    def test_a_duplicate_name_is_refused_until_it_is_unregistered(self):
        with FakeGame() as game:
            lua_register(game, "Test.once", schema="{}")
            self.assertIn("already registered", registration_error(game, "Test.once"))
            self.assertTrue(game.exec('return require("HarnessCommands").unregister("Test.once")'))
            lua_register(game, "Test.once", schema="{}")
            self.assertFalse(game.exec('return require("HarnessCommands").unregister("Test.nothing")'))

    def test_a_handler_must_be_a_function(self):
        with FakeGame() as game:
            self.assertIn("handler must be a function", registration_error(game, "Test.x", handler="5"))

    def test_bad_schemas_are_refused(self):
        cases = {
            "unknown type": ("{ a = { type = 'date' } }", "needs a type"),
            "no type": ("{ a = { required = true } }", "needs a type"),
            "typo in a rule": ("{ a = { type = 'integer', minimum = 1 } }", "unknown rule key"),
            "min on a string": ("{ a = { type = 'string', min = 1 } }", "min and max need a number type"),
            "maxLength on a number": ("{ a = { type = 'number', maxLength = 1 } }", "maxLength needs a string type"),
            "bad argument name": ("{ ['a b'] = { type = 'string' } }", "bad argument name"),
            "schema not a table": ("5", "schema must be a table"),
            "required not a boolean": ("{ a = { type = 'string', required = 'yes' } }", "required must be a boolean"),
        }
        for label, (schema, message) in cases.items():
            with self.subTest(case=label), FakeGame() as game:
                self.assertIn(message, registration_error(game, "Test.x", schema=schema))

    def test_a_later_change_of_the_schema_table_has_no_effect(self):
        with FakeGame() as game:
            game.exec("""
                local schema = { amount = { type = "integer", required = true } }
                require("HarnessCommands").register("Test.copy", function(args) return args end, schema)
                schema.amount.type = "string"
            """)
            self.assertEqual(call(game, "Test.copy", amount=4), {"amount": 4})


class ValidationTests(unittest.TestCase):
    def refused(self, args, message):
        with FakeGame() as game:
            game.exec("CALLS = 0")
            lua_register(game, handler="function(args) CALLS = CALLS + 1; return 1 end")
            answer = dispatch(game, "Test.add", args)
            self.assertFalse(answer["ok"], answer)
            self.assertIn(message, answer["error"])
            self.assertEqual(game.exec("return CALLS"), 0, "the handler must not run")

    def test_unknown_argument(self):
        self.refused({"amount": 1, "color": "red"}, "unknown argument color (allowed: amount, flag, kind, note, ratio)")

    def test_missing_required_argument(self):
        self.refused({}, "missing argument amount")

    def test_wrong_types(self):
        self.refused({"amount": "5"}, "argument amount must be an integer, got string")
        self.refused({"amount": 1.5}, "argument amount must be an integer")
        self.refused({"amount": None}, "argument amount must be an integer, got null")
        self.refused({"amount": True}, "must be an integer, got boolean")
        self.refused({"amount": 1, "ratio": "x"}, "argument ratio must be a number")
        self.refused({"amount": 1, "flag": 1}, "argument flag must be a boolean")
        self.refused({"amount": 1, "note": 5}, "argument note must be a string")
        self.refused({"amount": [1]}, "got table")

    def test_limits(self):
        self.refused({"amount": 0}, "argument amount must be at least 1")
        self.refused({"amount": 11}, "argument amount must be at most 10")
        self.refused({"amount": 1, "ratio": 1.5}, "argument ratio must be at most 1")
        self.refused({"amount": 1, "note": "toolong"}, "argument note is longer than 5 characters")
        self.refused({"amount": 1, "kind": "c"}, "argument kind must be one of: a, b")

    def test_the_default_string_limit_is_64_characters(self):
        with FakeGame() as game:
            lua_register(game, "Test.text", schema="{ text = { type = 'string' } }")
            self.assertTrue(dispatch(game, "Test.text", {"text": "x" * 64})["ok"])
            self.assertFalse(dispatch(game, "Test.text", {"text": "x" * 65})["ok"])

    def test_args_must_be_an_object(self):
        with FakeGame() as game:
            lua_register(game, "Test.none", schema="{}")
            self.assertTrue(dispatch(game, "Test.none", None)["ok"])
            self.assertIn("args must be an object", game.exec(
                'return require("HarnessCommands").dispatch("Test.none", 5).error'))

    def test_an_unknown_command_is_refused(self):
        with FakeGame() as game:
            self.assertEqual(dispatch(game, "Nobody.home"), {"ok": False, "error": "unknown command: Nobody.home"})

    def test_optional_arguments_may_be_left_out(self):
        with FakeGame() as game:
            lua_register(game)
            self.assertEqual(call(game, "Test.add", amount=2), {"got": {"amount": 2}})


class HandlerTests(unittest.TestCase):
    def test_an_error_in_the_handler_becomes_an_error_result(self):
        with FakeGame() as game:
            lua_register(game, schema="{}", handler="function() error('boom') end")
            answer = dispatch(game, "Test.add")
            self.assertFalse(answer["ok"])
            self.assertIn("Test.add failed", answer["error"])
            self.assertIn("boom", answer["error"])
            self.assertTrue(dispatch(game, "harness.list_commands")["ok"])  # the registry goes on

    def test_nil_and_a_message_is_a_clear_refusal(self):
        with FakeGame() as game:
            lua_register(game, schema="{}", handler="function() return nil, 'the town is empty' end")
            self.assertEqual(dispatch(game, "Test.add"), {"ok": False, "error": "Test.add refused: the town is empty"})

    def test_nil_alone_is_refused(self):
        with FakeGame() as game:
            lua_register(game, schema="{}", handler="function() end")
            self.assertIn("returned nothing", dispatch(game, "Test.add")["error"])

    def test_a_result_that_is_not_json_is_refused(self):
        with FakeGame() as game:
            lua_register(game, schema="{}", handler="function() return { f = function() end } end")
            answer = dispatch(game, "Test.add")
            self.assertFalse(answer["ok"])
            self.assertIn("not JSON", answer["error"])

    def test_a_slow_handler_is_logged_not_stopped(self):
        with FakeGame() as game:
            lua_register(game, schema="{}", handler="function() fg.now = fg.now + 1; return 7 end")
            game.lua.globals().fg = game.fg
            self.assertEqual(call(game, "Test.add"), 7)
            self.assertTrue(any("must be quick" in line for line in game.log_lines()), game.log_lines())

    def test_strings_are_data_and_never_run(self):
        with FakeGame() as game:
            game.exec("EVIL = 0")
            lua_register(game, "Test.echo", schema="{ text = { type = 'string' } }", handler="function(args) return args.text end")
            code = 'EVIL = 1; os.exit()'
            self.assertEqual(call(game, "Test.echo", text=code), code)
            self.assertEqual(game.exec("return EVIL"), 0)

    def test_no_source_text_is_run_as_code(self):
        for path in (MOD_DIR / "shared" / "HarnessCommands" / "HarnessCommands.lua",
                     MOD_DIR / "shared" / "HarnessJson" / "HarnessJson.lua",
                     MOD_DIR / "InvasionStandIn" / "Scripts" / "main.lua"):
            code = "\n".join(line.split("--", 1)[0] for line in path.read_text(encoding="utf-8").splitlines())
            for forbidden in (r"\bload\s*\(", r"\bloadstring\s*\(", r"\bdofile\s*\(", r"\bloadfile\s*\(", r"\bos\.execute", r"\bio\.popen"):
                self.assertIsNone(re.search(forbidden, code), f"{path.name}: {forbidden}")


class ListTests(unittest.TestCase):
    def test_list_shows_names_and_schemas_sorted(self):
        with FakeGame() as game:
            lua_register(game, "Zeta.go", schema="{}")
            lua_register(game)
            commands = call(game, "harness.list_commands")["commands"]
            by_name = {c["name"]: c for c in commands}
            self.assertEqual(sorted(by_name), ["Test.add", "Zeta.go", "harness.list_commands"])
            self.assertEqual(by_name["Zeta.go"]["args"], {})
            self.assertEqual(by_name["Test.add"]["args"]["amount"], {"type": "integer", "required": True, "min": 1, "max": 10})
            self.assertEqual(by_name["Test.add"]["args"]["kind"]["oneOf"], ["a", "b"])


class HandleRequestTests(unittest.TestCase):
    def handle(self, game, text):
        game.lua.globals().TEST_TEXT = text
        return json.loads(game.exec('local j = require("HarnessJson"); return j.encode(require("HarnessCommands").handleRequest("Test.add", TEST_TEXT))'))

    def test_args_are_taken_from_the_request(self):
        with FakeGame() as game:
            lua_register(game)
            answer = self.handle(game, '{"id":"0001","command":"Test.add","args":{"amount":4,"note":"a\\"b"}}')
            self.assertEqual(answer["result"]["got"], {"amount": 4, "note": 'a"b'})

    def test_a_request_without_args_has_no_arguments(self):
        with FakeGame() as game:
            lua_register(game, schema="{}")
            self.assertTrue(self.handle(game, '{"id":"0001","command":"Test.add"}')["ok"])

    def test_bad_requests_are_refused(self):
        with FakeGame() as game:
            lua_register(game)
            self.assertIn("not valid JSON", self.handle(game, '{"id":"0001",')["error"])
            self.assertIn("must be a JSON object", self.handle(game, "[1]")["error"])
            self.assertIn("args must be an object", self.handle(game, '{"args":5}')["error"])
            self.assertIn("must be an integer, got null", self.handle(game, '{"args":{"amount":null}}')["error"])


class DecodeTests(unittest.TestCase):
    def decode(self, game, text):
        game.lua.globals().TEST_TEXT = text
        return json.loads(game.exec(
            'local j = require("HarnessJson"); local v, e = j.decode(TEST_TEXT); return j.encode({ value = v, error = e })'))

    def test_values_round_trip_with_the_encoder(self):
        with FakeGame() as game:
            for value in (3, -2.5, 1e3, True, False, "x", "a\"b\\c\n\t/", "é", [1, [2, 3], {"a": []}], {"k": {"z": 1, "a": None}}, {}, []):
                with self.subTest(value=value):
                    answer = self.decode(game, json.dumps(value))
                    self.assertEqual(answer["value"], value if value != {} else {})

    def test_whitespace_is_allowed(self):
        with FakeGame() as game:
            self.assertEqual(self.decode(game, ' \n{ "a" : [ 1 , 2 ] }\r\n')["value"], {"a": [1, 2]})

    def test_bad_text_gives_a_message_and_no_value(self):
        bad = ["", "{", '{"a":1,}', '{"a":1 "b":2}', "tru", "01", "1.", '"abc', '"a\x01b"', '"\\q"', '"\\u12"', "[1 2]",
               '{"a":1}{"b":2}', '{"a":1,"a":2}', "[" * 20 + "]" * 20, "nul", "-", '{1:2}']
        with FakeGame() as game:
            for text in bad:
                with self.subTest(text=text[:20]):
                    answer = self.decode(game, text)
                    self.assertIsNone(answer.get("value"))
                    self.assertIn("JSON", answer["error"])

    def test_text_over_the_limit_is_refused(self):
        with FakeGame() as game:
            answer = self.decode(game, '"' + "x" * 20000 + '"')
            self.assertIn("at most", answer["error"])


class DispatchThroughHarnessActionsTests(unittest.TestCase):
    """The real HarnessActions mod file in the kit. The game objects are fakes."""

    def test_a_registered_command_is_run_from_a_request_file(self):
        with FakeGame() as game:
            start(game)
            lua_register(game)
            send(game, 1, {"command": "Test.add", "args": {"amount": 3, "note": "hi"}})
            answer = result(game, 1)
            self.assertEqual((answer["ok"], answer["id"], answer["command"]), (True, "0001", "Test.add"))
            self.assertEqual(answer["result"], {"got": {"amount": 3, "note": "hi"}})

    def test_a_bad_argument_is_refused_with_the_command_name(self):
        with FakeGame() as game:
            start(game)
            lua_register(game)
            send(game, 1, {"command": "Test.add", "args": {"amount": 99}})
            answer = result(game, 1)
            self.assertFalse(answer["ok"])
            self.assertIn("argument amount must be at most 10", answer["error"])
            self.assertEqual(answer["command"], "Test.add")

    def test_an_unknown_dotted_command_is_refused(self):
        with FakeGame() as game:
            start(game)
            send(game, 1, {"command": "Nobody.home"})
            self.assertIn("unknown command: Nobody.home", result(game, 1)["error"])

    def test_list_commands_is_built_in(self):
        with FakeGame() as game:
            start(game)
            lua_register(game)
            send(game, 1, {"command": "harness.list_commands"})
            names = [c["name"] for c in result(game, 1)["result"]["commands"]]
            self.assertEqual(names, ["Test.add", "harness.list_commands"])

    def test_old_commands_still_work_and_the_id_is_still_checked(self):
        with FakeGame() as game:
            start(game)
            send(game, 1, {"command": "ping"})
            self.assertTrue(result(game, 1)["ok"])
            (commands_dir(game) / "0002.json").write_text('{"id":"0009","command":"Test.add"}', encoding="utf-8")
            game.advance(1)
            self.assertIn("request id must be 0002", result(game, 2)["error"])

    def test_a_command_name_with_a_bad_character_is_not_matched(self):
        with FakeGame() as game:
            start(game)
            lua_register(game, "Test.add", schema="{}")
            send(game, 1, {"command": "Test.add;os.exit()"})
            self.assertIn("unknown command", result(game, 1)["error"])


if __name__ == "__main__":
    unittest.main()
