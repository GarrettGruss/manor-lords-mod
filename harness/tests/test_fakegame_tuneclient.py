"""Tests for the unit tuning client (spec 28, runlib/tune.py) against HarnessActions in the fake game."""

import json
import tempfile
import unittest
from pathlib import Path

import fakegame_path  # noqa: F401
from fakegame import FakeGame
from modstate_support import sleep_in
from runlib.commands import CommandError, CommandRefused
from runlib.tune import TuneClient, export_preset, find_newest_run, overrides_to_preset, resolve_run
from test_fakegame_harnesstune import build_world


class ClientTests(unittest.TestCase):
    def setUp(self):
        self.game = FakeGame()
        self.game.start()
        self.addCleanup(self.game.close)
        self.units = build_world(self.game)
        self.game.load_mod("HarnessActions")
        self.game.advance(1)
        self.client = TuneClient(self.game.run_dir)
        sleep = sleep_in(self.game)
        self.client._channel._sleep = sleep
        self.client._channel._monotonic = self.game.now

    def test_state_set_and_reset_round_trip(self):
        self.assertEqual(self.client.state()["sides"]["bandit"]["alive"], 3)
        answers = self.client.apply_values({"bandit": {"att": 9, "def": 20}, "player": {"morale": 5}})
        self.assertEqual([a["changed"] for a in answers], [3, 3, 2])
        self.assertEqual(len(self.client.state()["overrides"]), 3)
        self.assertEqual(self.client.reset(side="bandit")["removed"], 2)
        self.assertEqual(self.client.reset()["removed"], 1)
        self.assertEqual([getattr(u, "def") for u in self.units["bandit"]], [4, 4, 4])

    def test_a_refusal_raises_with_the_reason(self):
        with self.assertRaises(CommandRefused) as caught:
            self.client.set("king", "att", 1)
        self.assertIn("side must be", caught.exception.reason)

    def test_a_second_client_continues_after_the_used_numbers(self):
        self.client.state()
        self.client.state()
        second = TuneClient(self.game.run_dir)
        sleep = sleep_in(self.game)
        second._channel._sleep = sleep
        second._channel._monotonic = self.game.now
        self.assertEqual(second.state()["ok"], True)

    def test_spawn_count_outside_the_limit_is_refused_before_sending(self):
        with self.assertRaises(CommandError):
            self.client.spawn_fight([{"side": "player", "template": "spearMilitia", "count": 7}])


class PresetTests(unittest.TestCase):
    rows = [{"scope": "side:bandit", "field": "att", "value": 3}, {"scope": "side:player", "field": "def", "value": 50},
            {"scope": "squad:12", "field": "att", "value": 1}]

    def test_overrides_become_a_side_map(self):
        preset = overrides_to_preset(self.rows, "r1")
        self.assertEqual(preset["overrides"], {"bandit": {"att": 3}, "player": {"def": 50}, "squad:12": {"att": 1}})
        self.assertEqual(preset["run"], "r1")

    def test_export_writes_a_clean_file_name(self):
        with tempfile.TemporaryDirectory() as folder:
            path = export_preset(self.rows, "r1", Path(folder) / "presets", "../my preset!")
            self.assertEqual(path.name, "mypreset.json")
            self.assertEqual(json.loads(path.read_text(encoding="utf-8"))["overrides"]["bandit"], {"att": 3})
            self.assertEqual(list(path.parent.glob("*.tmp")), [])


class RunLookupTests(unittest.TestCase):
    def test_newest_run_with_commands_and_clear_failures(self):
        with tempfile.TemporaryDirectory() as folder:
            runs = Path(folder)
            with self.assertRaises(CommandError):
                find_newest_run(runs)
            (runs / "old" / "commands").mkdir(parents=True)
            (runs / "new" / "commands").mkdir(parents=True)
            (runs / "nocmd").mkdir()
            (runs / "old" / "commands").touch()
            (runs / "new" / "commands" / "0001.json").write_text("{}", encoding="utf-8")
            self.assertEqual(resolve_run(runs, "old"), runs / "old")
            self.assertEqual(find_newest_run(runs).name in ("old", "new"), True)
            with self.assertRaises(CommandError):
                resolve_run(runs, "nocmd")


if __name__ == "__main__":
    unittest.main()
