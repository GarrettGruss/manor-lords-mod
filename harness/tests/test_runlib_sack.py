"""Tests for the sack actions, the loot ledger actions and the village census helpers (spec 10, S6 and R3). No game."""

import unittest

import runlib_path  # noqa: F401
from runlib import sack
from runlib.actions import Actions
from runlib.expectations import Expectations


def village(standing=4, rubble=0, burning=0, stock=None, families=5, stores=()):
    stock = stock if stock is not None else {"15": 20, "172": 20}
    return {"buildings": {"total": standing + rubble, "standing": standing, "rubble": rubble, "burning": burning},
            "stock": {"total": sum(stock.values()), "by_good": dict(stock)}, "stores": [dict(entry) for entry in stores],
            "people": {"families": families, "population": 2 * families}, "region": "Test"}


class HelperTests(unittest.TestCase):
    def test_share_rounds_half_up(self):
        self.assertEqual([sack.share(4, 50), sack.share(5, 40), sack.share(5, 50), sack.share(3, 50), sack.share(10, 0), sack.share(7, 100)],
                         [2, 2, 3, 2, 0, 7])

    def test_percent_is_checked(self):
        for bad in (-1, 101, 1.5, "5", None, True):
            with self.assertRaises(sack.SackError):
                sack.check_percent("percent", bad)
        self.assertEqual(sack.check_percent("percent", 0), 0)
        self.assertEqual(sack.check_percent("percent", 100), 100)

    def test_method_and_positive(self):
        self.assertEqual(sack.check_method("fire"), "fire")
        with self.assertRaises(sack.SackError):
            sack.check_method("bomb")
        for bad in (0, -3, 2.5, True):
            with self.assertRaises(sack.SackError):
                sack.check_positive("count", bad)

    def test_readers(self):
        census = village(standing=2, rubble=1, burning=1, families=3,
                         stores=[{"id": 9, "goods": 5}, {"id": 4, "goods": 50}, {"id": 2, "goods": 5}])
        self.assertEqual((sack.standing(census), sack.rubble(census), sack.burning(census)), (2, 1, 1))
        self.assertEqual((sack.stock_total(census), sack.families(census), sack.population(census)), (40, 3, 6))
        self.assertEqual([entry["id"] for entry in sack.stores_by_size(census)], [4, 2, 9])
        self.assertEqual(sack.store(census, 9)["goods"], 5)
        with self.assertRaisesRegex(KeyError, "no store with id 77"):
            sack.store(census, 77)

    def test_removed_share(self):
        self.assertEqual(sack.removed_share(80, 40), 50.0)
        self.assertEqual(sack.removed_share(0, 0), 0.0)


class FakeBridge:
    def __init__(self):
        self.stock = {17: 3}

    def engine_path(self):
        return "engine"

    def player_region_path(self):
        return "region"

    def call_function(self, ref, function, args=None):
        assert function == "getStockOfGood", function
        return self.stock.get(args[0], 0)


class FakeVillageChannel:
    """Answers like the mod HarnessActions with a small village."""

    def __init__(self, bridge=None):
        self.bridge = bridge
        self.sent = []
        self.state = village()
        self.piles = []

    def send(self, command, **fields):
        self.sent.append((command, fields))
        before = self.state
        handler = getattr(self, "_" + command)
        return {"ok": True, **handler(before, **fields)}

    def _sack_census(self, before):
        return {"census": before}

    def _sack_buildings(self, before, method, count=None, percent=None):
        want = count if count is not None else sack.share(sack.standing(before), percent)
        hit = min(want, sack.standing(before))
        if method == "fire":   # the real game: a burning building is not rubble yet
            self.state = village(standing=sack.standing(before), rubble=sack.rubble(before), burning=sack.burning(before) + hit,
                                 stock=before["stock"]["by_good"])
        else:
            self.state = village(standing=sack.standing(before) - hit, rubble=sack.rubble(before) + hit, stock=before["stock"]["by_good"])
        return {"wanted": want, "hit": hit, "before": before, "after": self.state}

    def _sack_goods(self, before, percent=None, good=None, amount=None, store=None):
        stock = dict(before["stock"]["by_good"])
        removed = 0
        for kind in list(stock):
            take = sack.share(stock[kind], percent) if percent is not None else (min(amount, stock[kind]) if str(good) == kind else 0)
            stock[kind] -= take
            removed += take
        self.state = village(standing=sack.standing(before), stock=stock, families=sack.families(before))
        return {"removed": removed, "before": before, "after": self.state}

    def _sack_people(self, before, percent=None, count=None):
        want = count if count is not None else sack.share(sack.families(before), percent)
        self.state = village(standing=sack.standing(before), stock=before["stock"]["by_good"], families=sack.families(before) - want)
        return {"wanted": want, "families": want, "people": 2 * want, "before": before, "after": self.state}

    def _sack_village(self, before, buildings_pct, stock_pct, people_pct, method):
        hit = sack.share(sack.standing(before), buildings_pct)
        families = sack.share(sack.families(before), people_pct)
        self.state = village(standing=sack.standing(before) - hit, rubble=hit, families=sack.families(before) - families,
                             stock={kind: amount - sack.share(amount, stock_pct) for kind, amount in before["stock"]["by_good"].items()})
        return {"buildings_hit": hit, "goods_removed": 0, "families_removed": families, "people_removed": 2 * families,
                "before": before, "after": self.state}

    def _drop_loot(self, before, count, good, side):
        made = [{"id": len(self.piles) + 1 + index, "x": 10 * index + 1, "y": 5, "amount": 7, "good": good} for index in range(count)]
        self.piles.extend(made)
        return {"killed": count, "piles": made}

    def _loot_piles(self, before):
        return {"piles": list(self.piles)}

    def _recover_loot(self, before, pile):
        found = [entry for entry in self.piles if entry["id"] == pile][0]
        self.piles.remove(found)
        self.bridge.stock[found["good"]] = self.bridge.stock.get(found["good"], 0) + found["amount"]
        return {"recovered": found}


def make():
    bridge, expect = FakeBridge(), Expectations()
    channel = FakeVillageChannel(bridge)
    return Actions(bridge, expect, [], commands=channel), channel, expect


class SackActionTests(unittest.TestCase):
    def test_census_is_read_only(self):
        actions, channel, _ = make()
        self.assertEqual(actions.sack_census()["buildings"]["standing"], 4)
        self.assertEqual(channel.sent, [("sack_census", {})])

    def test_buildings_by_percent_and_count(self):
        actions, channel, expect = make()
        self.assertTrue(actions.sack_buildings(percent=50, method="fire")["ok"])
        self.assertEqual(channel.sent[-1], ("sack_buildings", {"percent": 50, "method": "fire"}))
        self.assertTrue(actions.sack_buildings(count=1)["ok"])
        census = actions.sack_census()
        self.assertEqual(sack.rubble(census), 1)
        self.assertTrue(expect.result()["passed"])

    def test_a_building_action_that_hits_less_than_wanted_fails(self):
        actions, _, expect = make()
        self.assertFalse(actions.sack_buildings(count=9)["ok"])  # only 4 stand
        self.assertFalse(expect.result()["passed"])

    def test_goods(self):
        actions, channel, expect = make()
        self.assertTrue(actions.sack_goods(percent=50)["ok"])
        self.assertTrue(actions.sack_goods(good=15, amount=3, store=77)["ok"])
        self.assertEqual(channel.sent[-1], ("sack_goods", {"store": 77, "good": 15, "amount": 3}))
        self.assertTrue(expect.result()["passed"])

    def test_people(self):
        actions, _, _ = make()
        self.assertTrue(actions.sack_people(percent=40)["ok"])
        self.assertEqual(sack.families(actions.sack_census()), 3)

    def test_village_checks_the_rounding_rule(self):
        actions, _, expect = make()
        answer = actions.sack_village(50, 50, 40)
        self.assertEqual((answer["buildings_hit"], answer["families_removed"]), (2, 2))
        self.assertTrue(expect.result()["passed"])

    def test_village_that_removes_the_wrong_share_fails(self):
        actions, channel, expect = make()
        original = channel._sack_village
        channel._sack_village = lambda before, **fields: original(before, **{**fields, "people_pct": 0})
        actions.sack_village(50, 50, 40)
        self.assertFalse(expect.result()["passed"])

    def test_bad_arguments_are_refused_before_any_command(self):
        actions, channel, _ = make()
        for call in (lambda: actions.sack_buildings(), lambda: actions.sack_buildings(percent=5, count=1),
                     lambda: actions.sack_buildings(percent=101), lambda: actions.sack_buildings(count=0),
                     lambda: actions.sack_buildings(percent=5, method="bomb"), lambda: actions.sack_goods(),
                     lambda: actions.sack_goods(percent=5, good=15), lambda: actions.sack_goods(good=15),
                     lambda: actions.sack_people(percent=-1), lambda: actions.sack_village(1, 2, 300)):
            with self.assertRaises(sack.SackError):
                call()
        self.assertEqual(channel.sent, [])

    def test_names_are_listed(self):
        names = make()[0].available()
        for name in ("sack_census", "sack_buildings", "sack_goods", "sack_people", "sack_village", "drop_loot", "loot_piles", "recover_loot"):
            self.assertIn(name, names)


class LootActionTests(unittest.TestCase):
    def test_drop_then_recover_checks_the_stock(self):
        actions, _, expect = make()
        record = actions.drop_loot(2, 17)
        self.assertTrue(record["ok"])
        self.assertEqual(len(record["answer"]["piles"]), 2)
        self.assertEqual(len(actions.loot_piles()), 2)
        self.assertTrue(actions.recover_loot(1)["ok"])
        self.assertEqual(len(actions.loot_piles()), 1)
        self.assertTrue(expect.result()["passed"])

    def test_a_pile_that_does_not_exist_is_refused_before_the_command(self):
        actions, channel, _ = make()
        with self.assertRaisesRegex(sack.SackError, "no pile with id 4"):
            actions.recover_loot(4)
        self.assertNotIn("recover_loot", [name for name, _ in channel.sent])

    def test_recovery_that_adds_nothing_fails(self):
        actions, channel, expect = make()
        actions.drop_loot(1, 17)
        channel._recover_loot = lambda before, pile: channel.piles.clear() or {"recovered": {}}  # the pile goes, the stock does not grow
        self.assertFalse(actions.recover_loot(1)["ok"])
        self.assertFalse(expect.result()["passed"])

    def test_drop_that_kills_fewer_fails(self):
        actions, channel, _ = make()
        channel._drop_loot = lambda before, count, good, side: {"killed": 1, "piles": [{"id": 1}]}
        self.assertFalse(actions.drop_loot(2, 17)["ok"])

    def test_bad_arguments(self):
        actions, _, _ = make()
        with self.assertRaises(sack.SackError):
            actions.drop_loot(0, 17)
        with self.assertRaises(sack.SackError):
            actions.drop_loot(1, 0)


if __name__ == "__main__":
    unittest.main()
