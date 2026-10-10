"""Tests for the stand-in mod RaidStandIn (spec 10 follow-up of U10): its toy rules, commands and metrics, in the fake game kit.

The stand-in is a test fixture. These tests prove the toy rules and the contract. They do not prove that the real game
accepts the mod; that is a later real-game run of the raid scenarios.
"""

import unittest

import fakegame_path  # noqa: F401
from fakegame import FakeGame
from modstate_support import build_engine, call, dispatch, set_days

PREFIX = "RaidStandIn."
ALL_COMMANDS = ["advance_days", "cancel_raid", "clock", "configure", "current_raid", "damage_morale", "enact", "expire_timer",
                "fill_loot", "kill_leader", "kill_raiders", "next_raid", "raid_log", "repeal", "reset", "sack", "set_day",
                "set_stockpile", "set_timer", "set_war_economy", "settlement", "stockpiles"]
ALL_METRICS = ["bait_hits", "day", "defense", "food", "game_over", "raid_active", "raid_announced", "raids_arrived", "season",
               "silver", "sacks_in_window", "spawned_units", "town_morale", "warlord_level", "workers_farming"]
ALLOWED_SEASONS = {"cuman": {"summer"}, "norse": {"spring", "autumn"}}


def started(game, days=100):
    build_engine(game, days)
    game.load_mod("RaidStandIn")
    return game


def raid(game, name, **args):
    return call(game, PREFIX + name, **args)


def refused(game, name, **args):
    answer = dispatch(game, PREFIX + name, args)
    assert not answer["ok"], f"{name} {args} was accepted: {answer}"
    return answer["error"]


def auto_log(game, tier, seed, days=1080):
    raid(game, "reset")
    raid(game, "configure", tier=tier, seed=seed, auto=True, leader_death_percent=10)
    raid(game, "advance_days", days=days)
    return raid(game, "raid_log", count=100)["raids"]


def arrive(game, faction="cuman", days=2, **config):
    """Set a clean state with one active raid. Random leader death is off, so the test controls every retreat."""
    raid(game, "reset")
    raid(game, "configure", leader_death_percent=0, announce_days=1, **config)
    raid(game, "set_day", day=100)
    raid(game, "set_timer", days=days, faction=faction)
    raid(game, "advance_days", days=days)
    return raid(game, "current_raid")


class RegistrationTests(unittest.TestCase):
    def test_all_commands_are_registered_with_the_mod_name_prefix(self):
        with FakeGame(separate_states=True) as game:
            started(game)
            names = [c["name"] for c in call(game, "harness.list_commands", mod="RaidStandIn")["commands"] if c["name"].startswith(PREFIX)]
            self.assertEqual(names, [PREFIX + name for name in ALL_COMMANDS])

    def test_all_metrics_are_answered_without_error(self):
        with FakeGame(separate_states=True) as game:
            started(game)
            answer = call(game, "harness.metrics", mod="RaidStandIn")
            self.assertEqual(answer["errors"], {})
            self.assertEqual(sorted(answer["metrics"]), sorted(PREFIX + name for name in ALL_METRICS))

    def test_bad_arguments_are_refused_by_the_schema(self):
        with FakeGame(separate_states=True) as game:
            started(game)
            self.assertIn("at most 4", refused(game, "configure", tier=5))
            self.assertIn("unknown argument", refused(game, "configure", colour=1))
            self.assertIn("must be one of", refused(game, "set_timer", days=3, faction="roman"))
            self.assertIn("missing argument", refused(game, "advance_days"))
            self.assertIn("must be at most 4000", refused(game, "advance_days", days=4001))

    def test_a_bad_size_percent_in_the_environment_stops_the_mod_loudly(self):
        with FakeGame(separate_states=True, env={"RAID_STANDIN_SIZE_PERCENT": "5"}) as game:
            build_engine(game, 100)
            with self.assertRaises(Exception) as caught:
                game.load_mod("RaidStandIn")
            self.assertIn("RAID_STANDIN_SIZE_PERCENT", str(caught.exception))


class ClockTests(unittest.TestCase):
    def test_seasons_change_every_90_days_and_the_year_wraps(self):
        with FakeGame(separate_states=True) as game:
            started(game)
            seen = [(day, raid(game, "set_day", day=day)["season"]) for day in (0, 89, 90, 179, 180, 269, 270, 359, 360)]
            self.assertEqual([s for _, s in seen], ["spring", "spring", "summer", "summer", "autumn", "autumn", "winter", "winter", "spring"])
            self.assertEqual(raid(game, "clock")["year"], 1)

    def test_the_toy_day_follows_the_game_days(self):
        with FakeGame(separate_states=True) as game:
            started(game, days=100)
            raid(game, "reset")
            start = raid(game, "clock")["day"]
            set_days(game, 104)
            self.assertEqual(raid(game, "clock")["day"], start + 4)
            self.assertEqual(call(game, "harness.metrics", mod="RaidStandIn")["metrics"][PREFIX + "day"], start + 4)

    def test_advance_days_moves_the_toy_day_without_the_game(self):
        with FakeGame(separate_states=True) as game:
            started(game)
            before = raid(game, "clock")["day"]
            self.assertEqual(raid(game, "advance_days", days=30)["day"], before + 30)


class DirectorTests(unittest.TestCase):
    def test_a_raid_is_announced_n_days_before_it_arrives(self):
        with FakeGame(separate_states=True) as game:
            started(game)
            raid(game, "reset")
            raid(game, "configure", announce_days=5)
            planned = raid(game, "set_timer", days=10, faction="cuman")
            self.assertEqual((planned["state"], planned["planned_day"]), ("scheduled", 10))
            raid(game, "advance_days", days=4)
            self.assertEqual(raid(game, "next_raid")["state"], "scheduled")
            raid(game, "advance_days", days=1)
            announced = raid(game, "next_raid")
            self.assertEqual((announced["state"], announced["announced_day"]), ("announced", 5))
            raid(game, "advance_days", days=4)
            self.assertEqual(raid(game, "current_raid")["state"], "none")
            raid(game, "advance_days", days=1)
            active = raid(game, "current_raid")
            self.assertEqual((active["state"], active["arrival_day"]), ("active", 10))
            self.assertEqual(raid(game, "next_raid")["state"], "none")

    def test_a_timer_shorter_than_the_lead_time_announces_at_once(self):
        with FakeGame(separate_states=True) as game:
            started(game)
            raid(game, "reset")
            raid(game, "configure", announce_days=5)
            self.assertEqual(raid(game, "set_timer", days=2)["state"], "announced")

    def test_one_raid_can_be_scheduled_at_a_time(self):
        with FakeGame(separate_states=True) as game:
            started(game)
            raid(game, "reset")
            raid(game, "set_timer", days=9)
            self.assertIn("already scheduled", refused(game, "set_timer", days=3))
            self.assertEqual(raid(game, "cancel_raid")["state"], "scheduled")
            self.assertIn("no raid is scheduled", refused(game, "cancel_raid"))
            self.assertEqual(raid(game, "set_timer", days=3)["id"], 2)

    def test_the_announced_kind_is_the_dominant_unit_of_the_composition_for_every_tier(self):
        with FakeGame(separate_states=True) as game:
            started(game)
            for tier, variety in ((1, 1), (2, 2), (3, 3), (4, 4)):
                for faction, kind in (("cuman", "horse_archers"), ("norse", "shock_infantry")):
                    raid(game, "reset")
                    raid(game, "configure", tier=tier, seed=tier)
                    planned = raid(game, "set_timer", days=3, faction=faction)
                    composition = planned["composition"]
                    self.assertEqual(planned["kind"], kind)
                    self.assertEqual(sum(composition.values()), planned["size"])
                    self.assertEqual(max(composition, key=composition.get), kind)
                    self.assertEqual(len(composition), variety)

    def test_the_same_seed_gives_the_same_raids_and_another_seed_does_not(self):
        with FakeGame(separate_states=True) as game:
            started(game)
            first, second, other = auto_log(game, 2, 7, 720), auto_log(game, 2, 7, 720), auto_log(game, 2, 8, 720)
            self.assertEqual(first, second)
            self.assertNotEqual(first, other)

    def test_auto_raids_obey_the_season_rules_over_three_years(self):
        with FakeGame(separate_states=True) as game:
            started(game)
            for tier in (1, 2, 3):
                raids = auto_log(game, tier, 3)
                self.assertGreaterEqual(len(raids), 3, tier)
                for entry in raids:
                    self.assertIn(entry["arrival_season"], ALLOWED_SEASONS[entry["faction"]], entry)
                self.assertEqual({entry["faction"] for entry in raids}, {"cuman", "norse"})

    def test_winter_pauses_an_active_raid_and_resumes_it_in_spring(self):
        with FakeGame(separate_states=True) as game:
            started(game)
            raid(game, "reset")
            raid(game, "configure", leader_death_percent=0, announce_days=1)
            raid(game, "set_day", day=275)
            raid(game, "set_timer", days=2)
            raid(game, "advance_days", days=2)
            raid(game, "advance_days", days=30)
            paused = raid(game, "current_raid")
            self.assertEqual((paused["state"], paused["loot"], paused["morale"], paused["paused_days"]), ("active", 0, 100, 30))
            raid(game, "set_day", day=0)
            raid(game, "advance_days", days=1)
            self.assertGreater(raid(game, "current_raid")["morale"], 0)
            self.assertLess(raid(game, "current_raid")["morale"], 100)


class RaidBehaviorTests(unittest.TestCase):
    def test_every_raid_has_one_objective_and_one_breaking_point(self):
        with FakeGame(separate_states=True) as game:
            started(game)
            raids = auto_log(game, 3, 5)
            self.assertGreaterEqual(len(raids), 5)
            for entry in raids:
                self.assertIn(entry["objective"], ("loot", "burn"))
                self.assertIsInstance(entry["breaking_point"], int)
                self.assertEqual(entry["state"], "ended")
                self.assertIn(entry["retreat_reason"], ("leader_dead", "morale_break", "full_loot", "timer_end"))

    def test_full_loot_makes_the_raid_retreat(self):
        with FakeGame(separate_states=True) as game:
            started(game)
            active = arrive(game)
            self.assertEqual((active["state"], active["retreat_reason"]), ("active", ""))
            ended = raid(game, "fill_loot")
            self.assertEqual((ended["state"], ended["retreat_reason"]), ("ended", "full_loot"))
            self.assertEqual(raid(game, "current_raid")["state"], "none")

    def test_a_morale_break_makes_the_raid_retreat(self):
        with FakeGame(separate_states=True) as game:
            started(game)
            active = arrive(game)
            self.assertEqual(raid(game, "damage_morale", amount=active["morale"] - active["breaking_point"] - 1)["state"], "active")
            self.assertEqual(raid(game, "damage_morale", amount=1)["retreat_reason"], "morale_break")

    def test_killing_raiders_lowers_morale_and_keeps_one_unit(self):
        with FakeGame(separate_states=True) as game:
            started(game)
            active = arrive(game)
            hurt = raid(game, "kill_raiders", count=2)
            self.assertEqual((hurt["units_left"], hurt["morale"]), (active["size"] - 2, active["morale"] - 8))
            last = raid(game, "kill_raiders", count=50)
            self.assertEqual(last["units_left"], 1)

    def test_the_timer_end_makes_the_raid_retreat(self):
        with FakeGame(separate_states=True) as game:
            started(game)
            arrive(game)
            self.assertEqual(raid(game, "expire_timer")["retreat_reason"], "timer_end")

    def test_a_raid_with_nothing_to_loot_ends_by_the_timer(self):
        with FakeGame(separate_states=True) as game:
            started(game)
            raid(game, "reset")
            for pile in range(1, 5):
                raid(game, "set_stockpile", id=pile, distance=5 * pile, stock=0)
            raid(game, "configure", leader_death_percent=0, announce_days=1)
            raid(game, "set_timer", days=2)
            raid(game, "advance_days", days=2 + 6)
            entry = raid(game, "raid_log", count=1)["raids"][0]
            self.assertEqual((entry["retreat_reason"], entry["loot"], entry["target"]), ("timer_end", 0, 1))

    def test_a_dead_leader_makes_the_raid_retreat(self):
        with FakeGame(separate_states=True) as game:
            started(game)
            arrive(game)
            ended = raid(game, "kill_leader")
            self.assertEqual((ended["state"], ended["retreat_reason"], ended["leader_alive"]), ("ended", "leader_dead", False))

    def test_forcing_a_condition_without_a_raid_is_refused(self):
        with FakeGame(separate_states=True) as game:
            started(game)
            raid(game, "reset")
            for name, args in (("fill_loot", {}), ("kill_leader", {}), ("expire_timer", {}), ("damage_morale", {"amount": 5}), ("kill_raiders", {"count": 1})):
                self.assertIn("no raid is active", refused(game, name, **args))

    def test_the_top_tier_retreats_only_when_the_leader_dies(self):
        with FakeGame(separate_states=True) as game:
            started(game)
            arrive(game, tier=4)
            for name, args in (("fill_loot", {}), ("expire_timer", {}), ("damage_morale", {"amount": 500})):
                self.assertEqual(raid(game, name, **args)["state"], "active", name)
            raid(game, "advance_days", days=5)
            self.assertEqual(raid(game, "current_raid")["state"], "active")
            self.assertEqual(raid(game, "kill_leader")["retreat_reason"], "leader_dead")

    def test_a_lower_tier_retreats_for_the_other_reasons(self):
        with FakeGame(separate_states=True) as game:
            started(game)
            arrive(game, tier=3)
            self.assertEqual(raid(game, "fill_loot")["retreat_reason"], "full_loot")

    def test_a_raid_loots_the_stockpile_it_targets(self):
        with FakeGame(separate_states=True) as game:
            started(game)
            active = arrive(game)
            before = {p["id"]: p["stock"] for p in raid(game, "stockpiles")["stockpiles"]}
            raid(game, "advance_days", days=1)
            after = {p["id"]: p["stock"] for p in raid(game, "stockpiles")["stockpiles"]}
            loot = raid(game, "current_raid")["loot"]
            self.assertEqual(active["target"], 2)
            self.assertGreater(loot, 0)
            self.assertEqual(before[2] - after[2], loot)
            self.assertEqual(before[3], after[3])


class TargetTests(unittest.TestCase):
    def test_a_bait_stockpile_is_the_target_and_losing_its_value_ends_the_bait(self):
        with FakeGame(separate_states=True) as game:
            started(game)
            self.assertEqual(arrive(game, tier=2)["target"], 2)
            bait = raid(game, "set_stockpile", id=5, distance=3, stock=500)
            self.assertEqual(bait["nearest_high_value"], 5)
            raid(game, "expire_timer")
            raid(game, "set_timer", days=2)
            raid(game, "advance_days", days=2)
            self.assertEqual((raid(game, "current_raid")["target"], raid(game, "current_raid")["bait_hit"]), (5, True))
            raid(game, "expire_timer")
            self.assertEqual(raid(game, "set_stockpile", id=5, distance=3, stock=99)["nearest_high_value"], 2)

    def test_a_near_pile_with_little_stock_is_not_high_value(self):
        with FakeGame(separate_states=True) as game:
            started(game)
            raid(game, "reset")
            self.assertEqual(raid(game, "stockpiles")["nearest_high_value"], 2)
            raid(game, "set_stockpile", id=2, distance=20, stock=99)
            self.assertEqual(raid(game, "stockpiles")["nearest_high_value"], 3)

    def test_tier_one_targets_at_random_and_tier_two_goes_for_the_bait(self):
        with FakeGame(separate_states=True) as game:
            started(game)
            low = auto_log(game, 1, 11, 2000)
            high = auto_log(game, 2, 11, 2000)
            self.assertGreaterEqual(len({entry["target"] for entry in low}), 3)
            self.assertTrue(all(entry["bait_hit"] for entry in high))
            self.assertFalse(all(entry["bait_hit"] for entry in low))


class TierTests(unittest.TestCase):
    def mean(self, game, tier, key):
        values = []
        for seed in range(1, 6):
            raids = auto_log(game, tier, seed, 720)
            values.append(len(raids) if key == "count" else sum(entry[key] for entry in raids) / len(raids))
        return sum(values) / len(values)

    def test_higher_tiers_bring_bigger_and_more_frequent_raids(self):
        with FakeGame(separate_states=True) as game:
            started(game)
            sizes = [self.mean(game, tier, "size") for tier in (1, 2, 3, 4)]
            counts = [self.mean(game, tier, "count") for tier in (1, 2, 3, 4)]
            self.assertEqual(sizes, sorted(sizes))
            self.assertLess(sizes[0], sizes[3] / 2)
            self.assertEqual(counts[:3], sorted(set(counts[:3])))
            self.assertGreater(counts[3], counts[0])

    def test_the_size_percent_setting_scales_the_raid_size(self):
        with FakeGame(separate_states=True) as game:
            started(game)
            raid(game, "reset")
            raid(game, "configure", seed=4)
            normal = raid(game, "set_timer", days=3)["size"]
            raid(game, "reset")
            raid(game, "configure", seed=4, size_percent=200)
            self.assertAlmostEqual(raid(game, "set_timer", days=3)["size"], normal * 2, delta=1)

    def test_the_size_percent_comes_from_the_environment_at_load(self):
        with FakeGame(separate_states=True, env={"RAID_STANDIN_SIZE_PERCENT": "150"}) as game:
            started(game)
            self.assertEqual(raid(game, "reset")["size_percent"], 150)


class WarlordTests(unittest.TestCase):
    def test_an_escaped_warlord_returns_stronger_and_a_dead_one_resets(self):
        with FakeGame(separate_states=True) as game:
            started(game)
            arrive(game)
            self.assertEqual(raid(game, "fill_loot")["leader_alive"], True)
            self.assertEqual(raid(game, "settlement")["warlord_level"], 1)
            second = raid(game, "set_timer", days=2)
            self.assertEqual(second["warlord_level"], 1)
            raid(game, "advance_days", days=2)
            raid(game, "fill_loot")
            self.assertEqual(raid(game, "settlement")["warlord_level"], 2)
            raid(game, "set_timer", days=2)
            raid(game, "advance_days", days=2)
            raid(game, "kill_leader")
            self.assertEqual(raid(game, "settlement")["warlord_level"], 0)
            self.assertEqual([r["warlord_level"] for r in raid(game, "raid_log")["raids"]], [0, 1, 2])

    def test_the_warlord_bonus_grows_with_the_level(self):
        with FakeGame(separate_states=True) as game:
            started(game)
            raid(game, "reset")
            raid(game, "configure", seed=3, leader_death_percent=0, announce_days=1)
            base = raid(game, "set_timer", days=2)["size"]
            raid(game, "cancel_raid")
            for _ in range(2):
                raid(game, "set_timer", days=2)
                raid(game, "advance_days", days=2)
                raid(game, "fill_loot")
            self.assertEqual(raid(game, "settlement")["warlord_level"], 2)
            raid(game, "configure", seed=3)
            bigger = raid(game, "set_timer", days=2)["size"]
            self.assertGreater(bigger, base * 1.4)


class SackTests(unittest.TestCase):
    def test_the_first_sack_is_not_fatal_and_the_run_continues(self):
        with FakeGame(separate_states=True) as game:
            started(game)
            raid(game, "reset")
            town = raid(game, "sack")
            self.assertEqual((town["sacks_in_window"], town["game_over"], town["food"]), (1, False, 700))
            self.assertEqual(raid(game, "advance_days", days=10)["day"], 10)
            self.assertEqual(raid(game, "settlement")["game_over"], False)

    def test_a_second_sack_inside_the_window_is_fatal(self):
        with FakeGame(separate_states=True) as game:
            started(game)
            raid(game, "reset")
            raid(game, "sack")
            raid(game, "advance_days", days=100)
            town = raid(game, "sack")
            self.assertEqual((town["sacks_in_window"], town["game_over"]), (2, True))
            self.assertIn("game is over", refused(game, "sack"))

    def test_a_sack_outside_the_window_is_forgotten(self):
        with FakeGame(separate_states=True) as game:
            started(game)
            raid(game, "reset")
            raid(game, "sack")
            raid(game, "advance_days", days=360)
            town = raid(game, "sack")
            self.assertEqual((town["sacks_in_window"], town["sacks_total"], town["game_over"]), (1, 2, False))

    def test_the_window_and_the_limit_are_configurable(self):
        with FakeGame(separate_states=True) as game:
            started(game)
            raid(game, "reset")
            raid(game, "configure", sack_limit=3, sack_window_days=50)
            raid(game, "sack")
            raid(game, "sack")
            self.assertEqual(raid(game, "settlement")["game_over"], False)
            self.assertEqual(raid(game, "sack")["game_over"], True)

    def test_a_sack_costs_food_and_hope(self):
        with FakeGame(separate_states=True) as game:
            started(game)
            raid(game, "reset")
            before = raid(game, "settlement")
            after = raid(game, "sack")
            self.assertEqual(after["town_morale"], before["town_morale"] - 30)
            self.assertLess(after["food"], before["food"])


class PoliticsTests(unittest.TestCase):
    def test_conscription_costs_silver_and_food_and_adds_defense(self):
        with FakeGame(separate_states=True) as game:
            started(game)
            raid(game, "reset")
            before = raid(game, "settlement")
            after = raid(game, "enact", law="conscription")
            self.assertEqual(before["silver"] - after["silver"], 100)
            self.assertEqual(after["defense"] - before["defense"], 20)
            self.assertEqual(after["food_use"] - before["food_use"], 3)
            self.assertIn("already in force", refused(game, "enact", law="conscription"))
            self.assertEqual(raid(game, "repeal", law="conscription")["defense"], before["defense"])
            self.assertIn("not in force", refused(game, "repeal", law="conscription"))

    def test_a_law_that_the_town_cannot_pay_is_refused(self):
        with FakeGame(separate_states=True) as game:
            started(game)
            raid(game, "reset")
            for _ in range(2):  # a repeal gives no refund, so the silver runs out
                raid(game, "enact", law="cuman_pact")
                raid(game, "repeal", law="cuman_pact")
            self.assertEqual(raid(game, "settlement")["silver"], 100)
            self.assertIn("costs 200 silver", refused(game, "enact", law="cuman_pact"))
            self.assertEqual(raid(game, "settlement")["laws"], [])

    def test_the_tithe_gives_silver_a_day_and_costs_hope(self):
        with FakeGame(separate_states=True) as game:
            started(game)
            raid(game, "reset")
            before = raid(game, "settlement")
            raid(game, "enact", law="tithe")
            raid(game, "advance_days", days=10)
            after = raid(game, "settlement")
            self.assertEqual(after["silver"] - before["silver"], 50)
            self.assertEqual(after["town_morale"], before["town_morale"] - 10 + 10)  # -10 for the law, +1 a day without threat

    def test_the_cuman_pact_halves_cuman_raids_only(self):
        with FakeGame(separate_states=True) as game:
            started(game)
            sizes = {}
            for pact in (False, True):
                for faction in ("cuman", "norse"):
                    raid(game, "reset")
                    raid(game, "configure", seed=9, tier=3)
                    if pact:
                        raid(game, "enact", law="cuman_pact")
                    sizes[pact, faction] = raid(game, "set_timer", days=3, faction=faction)["size"]
            self.assertAlmostEqual(sizes[True, "cuman"], sizes[False, "cuman"] / 2, delta=1)
            self.assertEqual(sizes[True, "norse"], sizes[False, "norse"])

    def test_morale_falls_with_the_threat_and_recovers_after_it(self):
        with FakeGame(separate_states=True) as game:
            started(game)
            raid(game, "reset")
            raid(game, "configure", announce_days=30, leader_death_percent=0)
            start = raid(game, "settlement")["town_morale"]
            raid(game, "advance_days", days=5)
            self.assertEqual(raid(game, "settlement")["town_morale"], start + 5)
            raid(game, "set_timer", days=20)  # shorter than the lead time: announced at once
            raid(game, "advance_days", days=10)
            self.assertEqual(raid(game, "settlement")["town_morale"], start + 5 - 20)
            raid(game, "advance_days", days=10)  # the raid arrives on the last day
            self.assertEqual(raid(game, "current_raid")["state"], "active")
            self.assertEqual(raid(game, "settlement")["town_morale"], start + 5 - 40)
            raid(game, "fill_loot")
            raid(game, "advance_days", days=10)
            self.assertEqual(raid(game, "settlement")["town_morale"], start + 5 - 40 + 10)

    def test_repelling_a_raid_gives_hope(self):
        with FakeGame(separate_states=True) as game:
            started(game)
            arrive(game)
            before = raid(game, "settlement")["town_morale"]
            raid(game, "kill_leader")
            self.assertEqual(raid(game, "settlement")["town_morale"], before + 10)

    def test_morale_stays_between_0_and_100(self):
        with FakeGame(separate_states=True) as game:
            started(game)
            raid(game, "reset")
            raid(game, "advance_days", days=200)
            self.assertEqual(raid(game, "settlement")["town_morale"], 100)
            raid(game, "configure", announce_days=30, tier=4, leader_death_percent=0)  # a top tier raid never leaves
            raid(game, "set_timer", days=40)
            raid(game, "advance_days", days=100)
            self.assertEqual(raid(game, "settlement")["town_morale"], 0)

    def test_the_war_economy_moves_workers_and_back(self):
        with FakeGame(separate_states=True) as game:
            started(game)
            raid(game, "reset")
            before = raid(game, "settlement")
            on = raid(game, "set_war_economy", on=True)
            self.assertEqual(on["workers"], {"farming": 30, "crafting": 20, "military": 10})
            self.assertEqual(sum(on["workers"].values()), sum(before["workers"].values()))
            self.assertEqual((on["defense"], on["food_income"]), (before["defense"] + 10, before["food_income"] - 5))
            self.assertIn("already on", refused(game, "set_war_economy", on=True))
            self.assertEqual(raid(game, "set_war_economy", on=False)["workers"], before["workers"])

    def test_winter_stops_the_harvest_and_strains_the_food(self):
        with FakeGame(separate_states=True) as game:
            started(game)
            raid(game, "reset")
            raid(game, "set_day", day=100)
            summer = raid(game, "settlement")
            raid(game, "set_day", day=300)
            winter = raid(game, "settlement")
            self.assertEqual((summer["food_income"], winter["food_income"]), (20, 0))
            self.assertEqual(winter["food_use"] - summer["food_use"], 5)
            food = winter["food"]
            raid(game, "advance_days", days=10)
            self.assertEqual(raid(game, "settlement")["food"], food - 150)

    def test_food_never_falls_below_zero(self):
        with FakeGame(separate_states=True) as game:
            started(game)
            raid(game, "reset")
            raid(game, "set_day", day=270)
            raid(game, "advance_days", days=80)
            self.assertEqual(raid(game, "settlement")["food"], 0)


if __name__ == "__main__":
    unittest.main()
