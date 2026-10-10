"""Tests for the stand-in mod InvasionStandIn (spec 10, U10): its toy rules, its commands and its metrics, in the fake game kit.

The stand-in is a test fixture. These tests prove the toy rules and the contract (commands and metrics). They do not prove
that the real game accepts the mod; that is the real-game run of the three stand-in scenarios.
"""

import unittest

import fakegame_path  # noqa: F401
from fakegame import FakeGame
from modstate_support import build_engine, call, dispatch, set_days

PREFIX = "InvasionStandIn."
ALL_COMMANDS = ["accept_tribute", "captives", "capture", "evacuate", "found_outpost", "free_captives", "lose_outpost", "offer_tribute",
                "outpost", "raid_target", "region_stock", "reject_tribute", "reset", "reveal", "set_year_days", "tribute", "upgrade_outpost"]
ALL_METRICS = ["captives", "leaked", "outposts_alive", "trade_value", "tribute_paid"]


def started(game, days=100):
    build_engine(game, days)
    game.load_mod("InvasionStandIn")
    return game


def standin(game, name, **args):
    return call(game, PREFIX + name, **args)


def refused(game, name, **args):
    answer = dispatch(game, PREFIX + name, args)
    assert not answer["ok"], f"{name} {args} was accepted: {answer}"
    return answer["error"]


def list_commands(game):
    return call(game, "harness.list_commands", mod="InvasionStandIn")["commands"]


def read_metrics(game):
    return call(game, "harness.metrics", mod="InvasionStandIn")["metrics"]


class RegistrationTests(unittest.TestCase):
    def test_all_commands_are_registered_with_the_mod_name_prefix(self):
        with FakeGame(separate_states=True) as game:
            started(game)
            names = [c["name"] for c in list_commands(game) if c["name"].startswith(PREFIX)]
            self.assertEqual(names, [PREFIX + name for name in ALL_COMMANDS])

    def test_all_metrics_are_registered_and_answered_by_the_mod(self):
        with FakeGame(separate_states=True) as game:
            started(game)
            self.assertEqual(sorted(read_metrics(game)), [PREFIX + name for name in ALL_METRICS])
            self.assertEqual(call(game, "harness.metrics", mod="InvasionStandIn")["errors"], {})

    def test_metrics_follow_the_state(self):
        with FakeGame(separate_states=True) as game:
            started(game)
            standin(game, "found_outpost", region_id=2, protected=False)
            standin(game, "capture", count=3)
            self.assertEqual({k.split(".")[1]: v for k, v in read_metrics(game).items()},
                             {"outposts_alive": 1, "trade_value": 20, "captives": 3, "tribute_paid": 0, "leaked": 0})

    def test_the_mod_registers_in_its_own_state_not_in_the_state_of_another_mod(self):
        # This test fails with the old design (one shared registry): the first state would know the stand-in commands.
        with FakeGame(separate_states=True) as game:
            started(game)
            game.load_mod("HarnessActions")
            names = game.exec('local n = {}; for _, c in ipairs(require("HarnessCommands").list()) do n[#n + 1] = c.name end; return table.concat(n, ",")',
                              state="HarnessActions")
            self.assertEqual(names, "harness.list_commands,harness.metrics")  # no stand-in command in the state of another mod
            self.assertEqual(call(game, "InvasionStandIn.tribute")["pending"], "none")

    def test_loading_the_mod_again_gives_a_fresh_state_and_one_poller(self):
        with FakeGame(separate_states=True) as game:
            started(game)
            standin(game, "capture", count=2)
            game.load_mod("InvasionStandIn")  # a hot reload: UE4SS gives the mod a new Lua state
            game.advance(1)
            self.assertEqual(standin(game, "captives")["held"], 0)
            self.assertIn(PREFIX + "reset", [c["name"] for c in list_commands(game)])
            self.assertEqual(game.fg.live_loops(), 1)  # the poller of the old state stopped itself (the owner token changed)

    def test_the_mod_logs_its_name_and_version(self):
        with FakeGame(separate_states=True) as game:
            started(game)
            self.assertTrue(any("[InvasionStandIn] loaded version" in line and "test fixture" in line for line in game.log_lines()))

    def test_the_mod_adds_no_loop_except_the_command_poller(self):
        with FakeGame(separate_states=True) as game:
            started(game)
            standin(game, "reset")
            self.assertEqual(game.fg.live_loops(), 1)

    def test_it_works_next_to_the_other_harness_mods(self):
        with FakeGame(separate_states=True) as game:
            build_engine(game)
            for name in ("HarnessActions", "HarnessTelemetry", "InvasionStandIn"):
                game.load_mod(name)
            game.advance(1)
            self.assertEqual(standin(game, "capture", count=1)["held"], 1)


class OutpostTests(unittest.TestCase):
    def test_found_sets_the_fields(self):
        with FakeGame(separate_states=True) as game:
            started(game)
            outpost = standin(game, "found_outpost", region_id=2)
            self.assertEqual(outpost, {"region_id": 2, "alive": True, "level": 1, "protected": True, "trade_value": 20,
                                       "scouting_range": 10, "tribute_to_invader": False, "leaks_intel": False, "unprotected_days": 0})

    def test_found_refusals(self):
        with FakeGame(separate_states=True) as game:
            started(game)
            self.assertIn("home region", refused(game, "found_outpost", region_id=1))
            standin(game, "found_outpost", region_id=2)
            self.assertIn("an outpost is alive in region 2", refused(game, "found_outpost", region_id=2))
            self.assertIn("region_id must be at most 8", refused(game, "found_outpost", region_id=9))

    def test_a_lost_outpost_has_no_trade_and_no_scouting_and_may_be_founded_again(self):
        with FakeGame(separate_states=True) as game:
            started(game)
            standin(game, "found_outpost", region_id=2)
            lost = standin(game, "lose_outpost", region_id=2)
            self.assertEqual((lost["alive"], lost["trade_value"], lost["scouting_range"]), (False, 0, 0))
            self.assertIn("no alive outpost", refused(game, "lose_outpost", region_id=2))
            self.assertTrue(standin(game, "found_outpost", region_id=2)["alive"])

    def test_upgrade_raises_trade_and_range_up_to_level_3(self):
        with FakeGame(separate_states=True) as game:
            started(game)
            standin(game, "found_outpost", region_id=2)
            levels = [standin(game, "upgrade_outpost", region_id=2) for _ in range(2)]
            self.assertEqual([(o["level"], o["trade_value"], o["scouting_range"]) for o in levels], [(2, 30, 15), (3, 40, 20)])
            self.assertIn("highest level", refused(game, "upgrade_outpost", region_id=2))

    def test_reveal_depends_on_the_border_distance(self):
        with FakeGame(separate_states=True) as game:
            started(game)
            self.assertEqual(standin(game, "reveal", region_id=2, distance=0), {"sees": False, "scouting_range": 0})
            standin(game, "found_outpost", region_id=2)
            self.assertTrue(standin(game, "reveal", region_id=2, distance=10)["sees"])
            self.assertFalse(standin(game, "reveal", region_id=2, distance=10.5)["sees"])
            standin(game, "lose_outpost", region_id=2)
            self.assertFalse(standin(game, "reveal", region_id=2, distance=0)["sees"])

    def test_raiders_hit_the_lowest_alive_outpost_first_then_the_town(self):
        with FakeGame(separate_states=True) as game:
            started(game)
            self.assertEqual(standin(game, "raid_target"), {"target": "town", "region_id": 1})
            standin(game, "found_outpost", region_id=5)
            standin(game, "found_outpost", region_id=3)
            self.assertEqual(standin(game, "raid_target"), {"target": "outpost", "region_id": 3})
            standin(game, "lose_outpost", region_id=3)
            self.assertEqual(standin(game, "raid_target")["region_id"], 5)

    def test_an_unprotected_outpost_pays_and_leaks_after_three_game_days(self):
        with FakeGame(separate_states=True) as game:
            started(game)
            standin(game, "found_outpost", region_id=2, protected=False)
            standin(game, "found_outpost", region_id=3, protected=True)
            set_days(game, 102)
            self.assertEqual(standin(game, "outpost", region_id=2)["leaks_intel"], False)
            set_days(game, 103)
            unprotected, protected = standin(game, "outpost", region_id=2), standin(game, "outpost", region_id=3)
            self.assertEqual((unprotected["tribute_to_invader"], unprotected["leaks_intel"], unprotected["unprotected_days"]), (True, True, 3))
            self.assertEqual((protected["tribute_to_invader"], protected["leaks_intel"]), (False, False))

    def test_days_that_passed_between_two_calls_are_all_counted(self):
        with FakeGame(separate_states=True) as game:
            started(game)
            standin(game, "found_outpost", region_id=2, protected=False)
            set_days(game, 110)
            self.assertEqual(standin(game, "outpost", region_id=2)["unprotected_days"], 10)

    def test_a_lost_outpost_stops_leaking(self):
        with FakeGame(separate_states=True) as game:
            started(game)
            standin(game, "found_outpost", region_id=2, protected=False)
            set_days(game, 105)
            standin(game, "lose_outpost", region_id=2)
            self.assertEqual(standin(game, "outpost", region_id=2)["leaks_intel"], False)

    def test_reading_an_outpost_that_never_existed_is_refused(self):
        with FakeGame(separate_states=True) as game:
            started(game)
            self.assertIn("no outpost was ever founded", refused(game, "outpost", region_id=4))


class EvacuationTests(unittest.TestCase):
    def test_families_and_grain_move_and_both_places_are_read_back(self):
        with FakeGame(separate_states=True) as game:
            started(game)
            standin(game, "found_outpost", region_id=2)
            answer = standin(game, "evacuate", from_region=1, to_region=2, families=5, grain=50)
            self.assertEqual(answer, {"from": {"families": 15, "grain": 150}, "to": {"families": 25, "grain": 250},
                                      "moved": {"families": 5, "grain": 50}})
            self.assertEqual(standin(game, "region_stock", region_id=1), {"families": 15, "grain": 150})
            self.assertEqual(standin(game, "region_stock", region_id=2), {"families": 25, "grain": 250})

    def test_refusals_change_nothing(self):
        with FakeGame(separate_states=True) as game:
            started(game)
            standin(game, "found_outpost", region_id=2)
            self.assertIn("has no alive outpost", refused(game, "evacuate", from_region=1, to_region=4, families=1, grain=1))
            self.assertIn("must differ", refused(game, "evacuate", from_region=2, to_region=2, families=1, grain=1))
            self.assertIn("has only 20 families", refused(game, "evacuate", from_region=1, to_region=2, families=21, grain=0))
            self.assertIn("has only 200 grain", refused(game, "evacuate", from_region=1, to_region=2, families=0, grain=201))
            self.assertEqual(standin(game, "region_stock", region_id=1), {"families": 20, "grain": 200})

    def test_a_lost_outpost_cannot_be_the_fallback(self):
        with FakeGame(separate_states=True) as game:
            started(game)
            standin(game, "found_outpost", region_id=2)
            standin(game, "lose_outpost", region_id=2)
            self.assertIn("has no alive outpost", refused(game, "evacuate", from_region=1, to_region=2, families=1, grain=0))


class CaptiveTests(unittest.TestCase):
    def test_capture_and_free(self):
        with FakeGame(separate_states=True) as game:
            started(game)
            self.assertEqual(standin(game, "capture", count=5), {"held": 5, "freed": 0, "ransom_value": 75})
            self.assertEqual(standin(game, "free_captives", count=2), {"held": 3, "freed": 2, "ransom_value": 45})
            self.assertIn("only 3 captives", refused(game, "free_captives", count=4))
            self.assertEqual(standin(game, "captives"), {"held": 3, "freed": 2, "ransom_value": 45})

    def test_counts_must_be_in_range(self):
        with FakeGame(separate_states=True) as game:
            started(game)
            self.assertIn("at least 1", refused(game, "capture", count=0))
            self.assertIn("at most 50", refused(game, "capture", count=51))


class TributeTests(unittest.TestCase):
    def test_a_payment_moves_silver(self):
        with FakeGame(separate_states=True) as game:
            started(game)
            self.assertEqual(standin(game, "offer_tribute", kind="payment", amount=100)["pending"], "payment")
            state = standin(game, "accept_tribute")
            self.assertEqual((state["treasury"], state["paid_total"], state["pending"]), (900, 100, "none"))

    def test_hostages_are_counted_and_cost_no_silver(self):
        with FakeGame(separate_states=True) as game:
            started(game)
            standin(game, "offer_tribute", kind="hostages", amount=4)
            state = standin(game, "accept_tribute")
            self.assertEqual((state["hostages_given"], state["treasury"]), (4, 1000))

    def test_vassalage_pays_every_toy_year(self):
        with FakeGame(separate_states=True) as game:
            started(game)
            standin(game, "set_year_days", days=2)
            standin(game, "offer_tribute", kind="vassal", amount=50)
            self.assertTrue(standin(game, "accept_tribute")["vassal"])
            set_days(game, 101)
            self.assertEqual(standin(game, "tribute")["years_paid"], 0)
            set_days(game, 105)
            state = standin(game, "tribute")
            self.assertEqual((state["years_paid"], state["treasury"], state["paid_total"]), (2, 900, 100))

    def test_vassal_tribute_never_takes_more_than_the_treasury_holds(self):
        with FakeGame(separate_states=True) as game:
            started(game)
            standin(game, "set_year_days", days=1)
            standin(game, "offer_tribute", kind="payment", amount=980)
            standin(game, "accept_tribute")
            standin(game, "offer_tribute", kind="vassal", amount=50)
            standin(game, "accept_tribute")
            set_days(game, 105)
            self.assertEqual(standin(game, "tribute")["treasury"], 0)

    def test_refusals(self):
        with FakeGame(separate_states=True) as game:
            started(game)
            self.assertIn("no offer is pending", refused(game, "accept_tribute"))
            self.assertIn("no offer is pending", refused(game, "reject_tribute"))
            self.assertIn("must be one of: payment, hostages, vassal", refused(game, "offer_tribute", kind="gift", amount=1))
            standin(game, "offer_tribute", kind="payment", amount=5000)
            self.assertIn("already pending", refused(game, "offer_tribute", kind="hostages", amount=1))
            self.assertIn("treasury has only 1000", refused(game, "accept_tribute"))
            self.assertEqual(standin(game, "reject_tribute")["pending"], "none")

    def test_a_second_vassalage_is_refused(self):
        with FakeGame(separate_states=True) as game:
            started(game)
            for _ in range(2):
                standin(game, "offer_tribute", kind="vassal", amount=5)
                answer = dispatch(game, PREFIX + "accept_tribute")
            self.assertIn("already a vassal", answer["error"])


class ResetTests(unittest.TestCase):
    def test_reset_clears_everything(self):
        with FakeGame(separate_states=True) as game:
            started(game)
            standin(game, "found_outpost", region_id=2, protected=False)
            standin(game, "capture", count=2)
            standin(game, "offer_tribute", kind="payment", amount=10)
            standin(game, "accept_tribute")
            standin(game, "reset")
            self.assertEqual(standin(game, "captives")["held"], 0)
            self.assertEqual(standin(game, "tribute")["treasury"], 1000)
            self.assertIn("no outpost was ever founded", refused(game, "outpost", region_id=2))


class NoGameMapTests(unittest.TestCase):
    def test_without_an_engine_the_commands_still_work_and_time_does_not_move(self):
        with FakeGame(separate_states=True) as game:
            game.load_mod("InvasionStandIn")
            standin(game, "found_outpost", region_id=2, protected=False)
            self.assertEqual(standin(game, "outpost", region_id=2)["unprotected_days"], 0)


if __name__ == "__main__":
    unittest.main()
