"""Tests for the raid and unit actions and the census helpers (spec 10). No game."""

import unittest

import runlib_path  # noqa: F401
from runlib.actions import ActionNotPossible, Actions
from runlib.expectations import Expectations
from runlib.units import loot_max, loot_total, side_count, squad_regions

CALENDAR = "calendar"


def census(bandit=0, civil=10, dead=0, loot_sum=0, loot_top=0, squads=()):
    return {"units": bandit + civil, "by_side": {"bandit": bandit, "civil": civil}, "by_state": {"dead": dead} if dead else {},
            "loot": {"carriers": 0, "total": loot_sum, "max": loot_top}, "squads": list(squads), "sample": [], "ms": 8}


class FakeBridge:
    def __init__(self):
        self.values = {(CALENDAR, "daysUntilNextRaid"): 730, (CALENDAR, "daysSinceLastRaid"): 0}
        self.ignore_write = False

    def engine_path(self):
        return "engine"

    def calendar_path(self, engine=None):
        return CALENDAR

    def read_property(self, ref, name):
        return self.values[(ref, name)]

    def write_property(self, ref, name, value):
        if not self.ignore_write:
            self.values[(ref, name)] = value


class FakeChannel:
    """Answers like the mod: a spawn adds `per_squad` bandit units."""

    def __init__(self, per_squad=18):
        self.bandit = 0
        self.per_squad = per_squad
        self.sent = []

    def send(self, command, **fields):
        self.sent.append((command, fields))
        before = {"by_side": {"bandit": self.bandit}, "dead": 0}
        if command == "spawn_raiders":
            self.bandit += self.per_squad * fields["squads"]
        elif command == "spawn_elite_raiders":
            self.bandit += 3 * self.per_squad
        elif command == "spawn_bandit_camp":
            self.bandit += self.per_squad
        elif command == "kill_units":
            return {"ok": True, "killed": fields["count"], "loot_carried": 0, "before": {"dead": 0}, "after": {"dead": fields["count"]}}
        elif command == "set_unit_loot":
            return {"ok": True, "wanted": fields["count"], "changed": fields["count"]}
        elif command == "units_census":
            return {"ok": True, "census": census(self.bandit)}
        return {"ok": True, "before": before, "after": {"by_side": {"bandit": self.bandit}, "dead": 0}}


def make(per_squad=18):
    bridge, expect = FakeBridge(), Expectations()
    channel = FakeChannel(per_squad)
    return Actions(bridge, expect, [], commands=channel), bridge, channel, expect


class CensusHelperTests(unittest.TestCase):
    def test_reads(self):
        data = census(bandit=18, loot_sum=21, loot_top=7, squads=[{"side": "bandit", "region": "A"}, {"side": "ai"}, {"side": "bandit"}])
        self.assertEqual(side_count(data, "bandit"), 18)
        self.assertEqual(side_count(data, "ai"), 0)
        self.assertEqual((loot_total(data), loot_max(data)), (21, 7))
        self.assertEqual(squad_regions(data, "bandit"), ["A"])


class RaidTimerTests(unittest.TestCase):
    def test_set_timer_checks_the_read_back(self):
        actions, bridge, _, _ = make()
        record = actions.set_raid_timer(2, days_since=5)
        self.assertTrue(record["ok"])
        self.assertEqual(bridge.values[(CALENDAR, "daysSinceLastRaid")], 5)

    def test_a_write_that_does_not_hold_fails(self):
        actions, bridge, _, expect = make()
        bridge.ignore_write = True
        self.assertFalse(actions.set_raid_timer(2)["ok"])
        self.assertFalse(expect.result()["passed"])


class SpawnTests(unittest.TestCase):
    def test_spawn_raid_expects_18_a_squad(self):
        actions, _, channel, _ = make()
        self.assertTrue(actions.spawn_raid(squads=2)["ok"])
        self.assertEqual(channel.sent[0], ("spawn_raiders", {"squads": 2}))

    def test_elite_raid_expects_54(self):
        actions, _, channel, _ = make()
        self.assertTrue(actions.spawn_raid(elite=True)["ok"])
        self.assertEqual(channel.sent[0][0], "spawn_elite_raiders")

    def test_a_spawn_with_the_wrong_size_fails(self):
        actions, _, _, expect = make(per_squad=10)
        self.assertFalse(actions.spawn_raid(squads=1)["ok"])
        self.assertFalse(expect.result()["passed"])

    def test_bandit_camp(self):
        self.assertTrue(make()[0].spawn_bandit_camp()["ok"])

    def test_kill_and_loot(self):
        actions, _, _, _ = make()
        self.assertTrue(actions.kill_units("bandit", 3)["ok"])
        self.assertTrue(actions.set_unit_loot("bandit", 3, 7)["ok"])

    def test_no_channel(self):
        with self.assertRaisesRegex(ActionNotPossible, "no command channel"):
            Actions(FakeBridge()).spawn_raid()

    def test_unsupported_raid_choices_say_why(self):
        actions = make()[0]
        for name in ("choose_raid_type", "steer_squad", "spawn_raiders"):
            with self.assertRaises(ActionNotPossible):
                getattr(actions, name)()


if __name__ == "__main__":
    unittest.main()
