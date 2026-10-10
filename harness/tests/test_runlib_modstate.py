"""Tests for runlib.modstate (spec 10, U10) with a fake mod behind the command channel and fake telemetry files. No game."""

import json
import tempfile
import unittest
from pathlib import Path

import runlib_path  # noqa: F401
from runlib.commands import CommandChannel, CommandError
from runlib.modstate import ModCommandError, ModMetricError, ModState
from runlib.telemetry import TelemetryReader
from test_runlib_scenario import ContextTestCase, FakeGame


class FakeMod:
    """Answers the request files like HarnessActions does. `answers` maps a command name to the result file body."""

    def __init__(self, folder: Path, answers: dict):
        self.folder = folder
        self.answers = answers
        self.requests = []

    def sleep(self, _seconds):
        for request_file in sorted(self.folder.glob("*.json")):
            if request_file.name.endswith(".result.json"):
                continue
            result_file = self.folder / request_file.name.replace(".json", ".result.json")
            if result_file.exists():
                continue
            request = json.loads(request_file.read_text(encoding="utf-8"))
            self.requests.append(request)
            body = self.answers.get(request["command"])
            if body is not None:
                result_file.write_text(json.dumps({"id": request["id"], "command": request["command"], **body}), encoding="utf-8")


class FakeContext:
    """What ModState needs from a scenario context."""

    def __init__(self, folder: Path, answers: dict):
        self.mod_side = FakeMod(folder / "commands", answers)
        self.now = 0.0
        self.commands = CommandChannel(folder / "commands", timeout_s=2, sleep=self.sleep, monotonic=self.clock)
        self.telemetry = TelemetryReader(folder)
        self.alive_checks = 0

    def clock(self):
        return self.now

    def sleep(self, seconds):
        self.now += seconds
        self.mod_side.sleep(seconds)

    def ensure_alive(self, where="scenario"):
        self.alive_checks += 1


def sample(clock, custom, **extra):
    return json.dumps({"n": 1, "clock": clock, "date": {"day": 1}, "custom": custom, **extra}) + "\n"


class ModStateTestCase(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.folder = Path(temp.name)

    def make(self, answers=None):
        ctx = FakeContext(self.folder, answers or {})
        slept = []

        def sleep(seconds):
            slept.append(seconds)
            ctx.now += seconds

        return ctx, ModState(ctx, sleep=sleep, monotonic=ctx.clock), slept

    def write_samples(self, *lines):
        (self.folder / "telemetry.jsonl").write_text("".join(lines), encoding="utf-8")


class CommandTests(ModStateTestCase):
    def test_the_result_of_the_mod_is_returned_and_args_are_sent_in_args(self):
        ctx, mod, _ = self.make({"Fake.add": {"ok": True, "result": {"total": 5}}})
        self.assertEqual(mod.command("Fake.add", amount=3, label="x"), {"total": 5})
        self.assertEqual(ctx.mod_side.requests[0], {"id": "0001", "command": "Fake.add", "args": {"amount": 3, "label": "x"}})

    def test_a_refusal_raises_with_the_message_of_the_mod(self):
        _, mod, _ = self.make({"Fake.add": {"ok": False, "error": "Fake.add: missing argument amount"}})
        with self.assertRaises(ModCommandError) as caught:
            mod.command("Fake.add")
        self.assertEqual(caught.exception.reason, "Fake.add: missing argument amount")
        self.assertEqual(caught.exception.command, "Fake.add")
        self.assertIn("missing argument amount", str(caught.exception))

    def test_a_missing_answer_is_a_channel_error_not_a_mod_error(self):
        _, mod, _ = self.make({})
        with self.assertRaises(CommandError) as caught:
            mod.command("Fake.add")
        self.assertNotIsInstance(caught.exception, ModCommandError)
        self.assertIn("no answer", str(caught.exception))

    def test_a_bad_name_is_refused_before_anything_is_sent(self):
        ctx, mod, _ = self.make()
        for name in ("add", "Fake.add.more", "Fake.1", "Fake add"):
            with self.subTest(name=name), self.assertRaises(ValueError):
                mod.command(name)
        self.assertEqual(ctx.mod_side.requests, [])

    def test_commands_lists_what_the_mod_registered(self):
        listing = [{"name": "Fake.add", "args": {"amount": {"type": "integer"}}}]
        _, mod, _ = self.make({"harness.list_commands": {"ok": True, "result": {"commands": listing}}})
        self.assertEqual(mod.commands(), listing)

    def test_refusal_returns_the_message_or_none(self):
        _, mod, _ = self.make({"Fake.no": {"ok": False, "error": "nope"}, "Fake.yes": {"ok": True, "result": 1}})
        self.assertEqual(mod.refusal("Fake.no"), "nope")
        self.assertIsNone(mod.refusal("Fake.yes"))

    def test_the_game_is_checked_to_be_alive(self):
        ctx, mod, _ = self.make({"Fake.add": {"ok": True, "result": 1}})
        mod.command("Fake.add")
        self.assertGreaterEqual(ctx.alive_checks, 1)


class MetricTests(ModStateTestCase):
    def test_metric_is_the_latest_value(self):
        _, mod, _ = self.make()
        self.write_samples(sample(1, {"Fake.n": 1}), sample(2, {"Fake.n": 2, "Fake.m": 9}), sample(3, {"Fake.m": 10}))
        self.assertEqual(mod.metric("Fake.m"), 10)
        self.assertEqual(mod.metric("Fake.n"), 2)  # the latest sample that holds it

    def test_a_missing_metric_raises_or_gives_the_default(self):
        _, mod, _ = self.make()
        self.assertEqual(mod.metric("Fake.n", None), None)  # no telemetry file at all
        self.write_samples(sample(1, {}))
        with self.assertRaisesRegex(ModMetricError, "Fake.n"):
            mod.metric("Fake.n")
        self.assertEqual(mod.metric("Fake.n", 0), 0)

    def test_a_false_or_zero_value_is_a_value(self):
        _, mod, _ = self.make()
        self.write_samples(sample(1, {"Fake.flag": False, "Fake.zero": 0}))
        self.assertEqual((mod.metric("Fake.flag"), mod.metric("Fake.zero")), (False, 0))

    def test_a_half_written_last_line_is_skipped(self):
        _, mod, _ = self.make()
        self.write_samples(sample(1, {"Fake.n": 1}), '{"n": 2, "clo')
        self.assertEqual(mod.metric("Fake.n"), 1)

    def test_metric_names_follow_the_naming_rule(self):
        _, mod, _ = self.make()
        with self.assertRaises(ValueError):
            mod.metric("outposts_alive")

    def test_wait_metric_returns_when_the_predicate_is_true(self):
        ctx, mod, slept = self.make()
        self.write_samples(sample(1, {"Fake.n": 1}))
        calls = []

        def predicate(value):
            calls.append(value)
            if len(calls) == 2:  # a new sample arrives while the harness waits
                self.write_samples(sample(1, {"Fake.n": 1}), sample(2, {"Fake.n": 5}))
            return value >= 5

        self.assertEqual(mod.wait_metric("Fake.n", predicate, timeout_s=10), 5)
        self.assertEqual(calls, [1, 1, 5])
        self.assertEqual(len(slept), 2)

    def test_wait_metric_times_out_and_names_the_last_value(self):
        _, mod, slept = self.make()
        self.write_samples(sample(1, {"Fake.n": 1}))
        with self.assertRaisesRegex(ModMetricError, r"did not reach the wanted value in 3 s \(last value: 1\)"):
            mod.wait_metric("Fake.n", lambda value: value > 100, timeout_s=3)
        self.assertGreaterEqual(sum(slept), 3)

    def test_wait_metric_waits_for_a_metric_that_is_not_there_yet(self):
        _, mod, _ = self.make()
        with self.assertRaisesRegex(ModMetricError, "last value: None"):
            mod.wait_metric("Fake.n", lambda value: True, timeout_s=1)

    def test_wait_metric_accepts_false_and_zero_as_values(self):
        _, mod, _ = self.make()
        self.write_samples(sample(1, {"Fake.n": 0}))
        self.assertEqual(mod.wait_metric("Fake.n", lambda value: value == 0, timeout_s=1), 0)

    def test_metrics_window_lists_rows_over_time(self):
        _, mod, _ = self.make()
        self.write_samples(sample(10, {"Fake.n": 1, "Fake.m": 7}), sample(20, {"Fake.n": 2}), sample(30, {"Fake.n": 3}),
                           json.dumps({"n": 4, "clock": None, "custom": {"Fake.n": 4}}) + "\n")
        rows = mod.metrics_window()
        self.assertEqual([r["clock"] for r in rows], [10, 20, 30])
        self.assertEqual(rows[0]["values"], {"Fake.n": 1, "Fake.m": 7})
        self.assertEqual([r["values"] for r in mod.metrics_window(["Fake.n"], start_clock=15, end_clock=30)], [{"Fake.n": 2}, {"Fake.n": 3}])
        self.assertEqual(mod.metrics_window()[0]["date"], {"day": 1})

    def test_metrics_window_checks_the_names(self):
        _, mod, _ = self.make()
        with self.assertRaises(ValueError):
            mod.metrics_window(["bad"])


class ContextTests(ContextTestCase):
    def test_the_scenario_context_has_a_mod_state_on_the_command_channel(self):
        ctx = self.make_context(FakeGame())
        self.assertIsInstance(ctx.mod, ModState)
        self.assertIs(ctx.commands, ctx.actions._commands)
        self.assertEqual(ctx.commands.folder, ctx.run_dir / "commands")


if __name__ == "__main__":
    unittest.main()
