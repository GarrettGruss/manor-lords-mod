"""Tests for runlib.modstate and the ModCommandChannel (spec 10, U10) with a fake mod behind the request files. No game."""

import json
import tempfile
import unittest
from pathlib import Path

import runlib_path  # noqa: F401
from runlib.commands import CommandRefused, ModCommandChannel, ModDidNotAnswer
from runlib.modstate import ModCommandError, ModMetricError, ModState
from test_runlib_scenario import ContextTestCase, FakeGame


class FakeMods:
    """Answers the request files like the poller of HarnessCommands does. `mods` maps a mod name to {command: result body}.

    A mod that is not in `mods` has no folder, like a mod that is not loaded.
    """

    def __init__(self, root: Path, mods: dict):
        self.root = root
        self.mods = mods
        self.requests = []  # (mod, number, request)
        for name in mods:
            (root / name).mkdir(parents=True, exist_ok=True)

    def serve(self):
        for name, answers in self.mods.items():
            for request_file in sorted((self.root / name).glob("*.json")):
                if request_file.name.endswith(".result.json"):
                    continue
                result_file = request_file.with_name(request_file.stem + ".result.json")
                if result_file.exists():
                    continue
                request = json.loads(request_file.read_text(encoding="utf-8"))
                self.requests.append((name, request_file.stem, request))
                body = answers(request) if callable(answers) else answers.get(request["command"])
                if body is not None:
                    result_file.write_text(json.dumps(body), encoding="utf-8")


class FakeContext:
    """What ModState needs from a scenario context."""

    def __init__(self, folder: Path, mods: dict, timeout_s=2):
        self.fake_mods = FakeMods(folder / "modcmd", mods)
        self.now = 0.0
        self.mod_commands = ModCommandChannel(folder / "modcmd", timeout_s=timeout_s, sleep=self.sleep, monotonic=self.clock)
        self.alive_checks = 0

    def clock(self):
        return self.now

    def sleep(self, seconds):
        self.now += seconds
        self.fake_mods.serve()

    def ensure_alive(self, where="scenario"):
        self.alive_checks += 1


def metrics_answer(**values):
    return {"ok": True, "result": {"metrics": values, "errors": {}}}


class ModStateTestCase(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.folder = Path(temp.name)

    def make(self, mods=None):
        ctx = FakeContext(self.folder, mods if mods is not None else {})
        slept = []

        def sleep(seconds):
            slept.append(seconds)
            ctx.sleep(seconds)

        return ctx, ModState(ctx, sleep=sleep, monotonic=ctx.clock), slept


class ChannelTests(ModStateTestCase):
    def test_a_request_goes_to_the_folder_of_the_mod_and_the_number_counts_up(self):
        ctx, _, _ = self.make({"Fake": {"Fake.add": {"ok": True, "result": 1}}})
        ctx.mod_commands.send("Fake", "Fake.add", {"amount": 3})
        ctx.mod_commands.send("Fake", "Fake.add")
        self.assertEqual([(m, n) for m, n, _ in ctx.fake_mods.requests], [("Fake", "0001"), ("Fake", "0002")])
        self.assertEqual(ctx.fake_mods.requests[0][2], {"command": "Fake.add", "args": {"amount": 3}})
        self.assertEqual(ctx.fake_mods.requests[1][2]["args"], {})

    def test_every_mod_has_its_own_numbers(self):
        ctx, _, _ = self.make({"A": {"A.x": {"ok": True, "result": 1}}, "B": {"B.x": {"ok": True, "result": 2}}})
        ctx.mod_commands.send("A", "A.x")
        ctx.mod_commands.send("B", "B.x")
        self.assertEqual([(m, n) for m, n, _ in ctx.fake_mods.requests], [("A", "0001"), ("B", "0001")])

    def test_a_new_client_continues_after_the_highest_request_in_the_folder(self):
        ctx, _, _ = self.make({"Fake": {"Fake.add": {"ok": True, "result": 1}}})
        ctx.mod_commands.send("Fake", "Fake.add")
        ctx.mod_commands.send("Fake", "Fake.add")
        second = ModCommandChannel(self.folder / "modcmd", timeout_s=2, sleep=ctx.sleep, monotonic=ctx.clock)
        second.send("Fake", "Fake.add")
        self.assertEqual(ctx.fake_mods.requests[-1][1], "0003")

    def test_a_refusal_raises_command_refused_with_the_reason(self):
        ctx, _, _ = self.make({"Fake": {"Fake.add": {"ok": False, "error": "Fake.add: missing argument amount"}}})
        with self.assertRaises(CommandRefused) as caught:
            ctx.mod_commands.send("Fake", "Fake.add")
        self.assertEqual(caught.exception.reason, "Fake.add: missing argument amount")

    def test_a_mod_without_a_folder_did_not_answer_and_the_message_names_the_mod(self):
        ctx, _, _ = self.make({"Fake": {}})
        with self.assertRaises(ModDidNotAnswer) as caught:
            ctx.mod_commands.send("Missing", "Missing.add")
        self.assertIn("mod did not answer: Missing", str(caught.exception))
        self.assertEqual(caught.exception.mod, "Missing")
        self.assertFalse((self.folder / "modcmd" / "Missing").exists())  # the client never makes the folder

    def test_a_mod_that_has_a_folder_but_never_answers_did_not_answer(self):
        ctx, _, _ = self.make({"Fake": {}})
        with self.assertRaisesRegex(ModDidNotAnswer, r"mod did not answer: Fake\. No answer to command Fake.add"):
            ctx.mod_commands.send("Fake", "Fake.add")

    def test_a_folder_that_appears_late_is_used(self):
        ctx, _, _ = self.make({})
        original_sleep = ctx.sleep

        def sleep(seconds):
            ctx.fake_mods.mods["Late"] = {"Late.x": {"ok": True, "result": 7}}
            (ctx.fake_mods.root / "Late").mkdir(parents=True, exist_ok=True)
            original_sleep(seconds)

        channel = ModCommandChannel(self.folder / "modcmd", timeout_s=2, sleep=sleep, monotonic=ctx.clock)
        self.assertEqual(channel.send("Late", "Late.x")["result"], 7)


class CommandTests(ModStateTestCase):
    def test_the_result_of_the_mod_is_returned_and_args_are_sent_in_args(self):
        ctx, mod, _ = self.make({"Fake": {"Fake.add": {"ok": True, "result": {"total": 5}}}})
        self.assertEqual(mod.command("Fake.add", amount=3, label="x"), {"total": 5})
        self.assertEqual(ctx.fake_mods.requests[0], ("Fake", "0001", {"command": "Fake.add", "args": {"amount": 3, "label": "x"}}))

    def test_a_refusal_raises_with_the_message_of_the_mod(self):
        _, mod, _ = self.make({"Fake": {"Fake.add": {"ok": False, "error": "Fake.add: missing argument amount"}}})
        with self.assertRaises(ModCommandError) as caught:
            mod.command("Fake.add")
        self.assertEqual(caught.exception.reason, "Fake.add: missing argument amount")
        self.assertEqual(caught.exception.command, "Fake.add")
        self.assertIn("missing argument amount", str(caught.exception))

    def test_a_mod_that_is_not_loaded_is_a_channel_error_not_a_mod_error(self):
        _, mod, _ = self.make({})
        with self.assertRaises(ModDidNotAnswer) as caught:
            mod.command("Fake.add")
        self.assertNotIsInstance(caught.exception, ModCommandError)
        self.assertIn("mod did not answer: Fake", str(caught.exception))

    def test_a_bad_name_is_refused_before_anything_is_sent(self):
        ctx, mod, _ = self.make({"Fake": {}})
        for name in ("add", "Fake.add.more", "Fake.1", "Fake add", "../x.add"):
            with self.subTest(name=name), self.assertRaises(ValueError):
                mod.command(name)
        self.assertEqual(ctx.fake_mods.requests, [])

    def test_commands_lists_what_the_mod_registered(self):
        listing = [{"name": "Fake.add", "args": {"amount": {"type": "integer"}}}]
        ctx, mod, _ = self.make({"Fake": {"harness.list_commands": {"ok": True, "result": {"commands": listing}}}})
        self.assertEqual(mod.commands("Fake"), listing)
        self.assertEqual(ctx.fake_mods.requests[0][0], "Fake")

    def test_commands_checks_the_mod_name(self):
        _, mod, _ = self.make({})
        for name in ("", "Fake.add", "1Fake", "a/b"):
            with self.subTest(name=name), self.assertRaises(ValueError):
                mod.commands(name)

    def test_refusal_returns_the_message_or_none(self):
        _, mod, _ = self.make({"Fake": {"Fake.no": {"ok": False, "error": "nope"}, "Fake.yes": {"ok": True, "result": 1}}})
        self.assertEqual(mod.refusal("Fake.no"), "nope")
        self.assertIsNone(mod.refusal("Fake.yes"))

    def test_the_game_is_checked_to_be_alive(self):
        ctx, mod, _ = self.make({"Fake": {"Fake.add": {"ok": True, "result": 1}}})
        mod.command("Fake.add")
        self.assertGreaterEqual(ctx.alive_checks, 1)


class MetricTests(ModStateTestCase):
    def serve_metrics(self, values):
        """A mod whose metric values can change between reads."""
        state = {"values": values}
        ctx = FakeContext(self.folder, {"Fake": lambda request: metrics_answer(**state["values"])})
        slept = []

        def sleep(seconds):
            slept.append(seconds)
            ctx.sleep(seconds)

        return state, ctx, ModState(ctx, sleep=sleep, monotonic=ctx.clock), slept

    def test_metric_is_read_from_the_mod_with_the_built_in_command(self):
        _, ctx, mod, _ = self.serve_metrics({"Fake.n": 1, "Fake.m": 9})
        self.assertEqual(mod.metric("Fake.m"), 9)
        self.assertEqual(ctx.fake_mods.requests[0], ("Fake", "0001", {"command": "harness.metrics", "args": {}}))

    def test_a_missing_metric_raises_or_gives_the_default(self):
        _, _, mod, _ = self.serve_metrics({"Fake.m": 1})
        with self.assertRaisesRegex(ModMetricError, "Fake.n"):
            mod.metric("Fake.n")
        self.assertEqual(mod.metric("Fake.n", 0), 0)
        self.assertIsNone(mod.metric("Fake.n", None))

    def test_a_metric_that_failed_in_the_mod_names_the_reason(self):
        ctx = FakeContext(self.folder, {"Fake": {"harness.metrics": {"ok": True, "result": {"metrics": {}, "errors": {"Fake.n": "boom"}}}}})
        with self.assertRaisesRegex(ModMetricError, "metric function failed: boom"):
            ModState(ctx).metric("Fake.n")

    def test_a_false_or_zero_value_is_a_value(self):
        _, _, mod, _ = self.serve_metrics({"Fake.flag": False, "Fake.zero": 0})
        self.assertEqual((mod.metric("Fake.flag"), mod.metric("Fake.zero")), (False, 0))

    def test_metric_names_follow_the_naming_rule(self):
        _, _, mod, _ = self.serve_metrics({})
        with self.assertRaises(ValueError):
            mod.metric("outposts_alive")

    def test_a_mod_that_does_not_answer_raises_even_with_a_default(self):
        _, mod, _ = self.make({})
        with self.assertRaises(ModDidNotAnswer):
            mod.metric("Fake.n", None)

    def test_wait_metric_returns_when_the_predicate_is_true(self):
        state, _, mod, slept = self.serve_metrics({"Fake.n": 1})
        calls = []

        def predicate(value):
            calls.append(value)
            if len(calls) == 2:  # the value changes while the harness waits
                state["values"] = {"Fake.n": 5}
            return value >= 5

        self.assertEqual(mod.wait_metric("Fake.n", predicate, timeout_s=10), 5)
        self.assertEqual(calls, [1, 1, 5])

    def test_wait_metric_times_out_and_names_the_last_value(self):
        _, ctx, mod, _ = self.serve_metrics({"Fake.n": 1})
        with self.assertRaisesRegex(ModMetricError, r"did not reach the wanted value in 3 s \(last value: 1\)"):
            mod.wait_metric("Fake.n", lambda value: value > 100, timeout_s=3)
        self.assertGreaterEqual(ctx.now, 3)

    def test_wait_metric_waits_for_a_metric_that_is_not_there_yet(self):
        _, _, mod, _ = self.serve_metrics({})
        with self.assertRaisesRegex(ModMetricError, "last value: None"):
            mod.wait_metric("Fake.n", lambda value: True, timeout_s=1)

    def test_wait_metric_accepts_false_and_zero_as_values(self):
        _, _, mod, _ = self.serve_metrics({"Fake.n": 0})
        self.assertEqual(mod.wait_metric("Fake.n", lambda value: value == 0, timeout_s=1), 0)

    def test_metrics_window_lists_the_reads_of_this_run(self):
        state, ctx, mod, _ = self.serve_metrics({"Fake.n": 1, "Fake.m": 7})
        mod.metric("Fake.n")
        ctx.now = 20
        state["values"] = {"Fake.n": 2}
        mod.metric("Fake.n")
        ctx.now = 30
        state["values"] = {"Fake.n": 3}
        mod.read_metrics("Fake")
        rows = mod.metrics_window()
        self.assertEqual([r["values"].get("Fake.n") for r in rows], [1, 2, 3])
        self.assertEqual(rows[0]["values"], {"Fake.n": 1, "Fake.m": 7})
        self.assertEqual([r["values"] for r in mod.metrics_window(["Fake.n"], start_s=15, end_s=31)], [{"Fake.n": 2}, {"Fake.n": 3}])

    def test_metrics_window_checks_the_names(self):
        _, _, mod, _ = self.serve_metrics({})
        with self.assertRaises(ValueError):
            mod.metrics_window(["bad"])


class ContextTests(ContextTestCase):
    def test_the_scenario_context_has_a_mod_state_on_the_mod_command_channel(self):
        ctx = self.make_context(FakeGame())
        self.assertIsInstance(ctx.mod, ModState)
        self.assertIs(ctx.mod_commands, ctx.mod._channel)
        self.assertEqual(ctx.mod_commands.folder, ctx.run_dir / "modcmd")
        self.assertEqual(ctx.commands.folder, ctx.run_dir / "commands")  # the HarnessActions channel is unchanged


if __name__ == "__main__":
    unittest.main()
