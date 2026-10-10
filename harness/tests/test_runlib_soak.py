"""Tests for the soak helpers and the soak-days checks (spec 10, U9 and Q1). No game."""

import unittest
from unittest import mock

import runlib_path  # noqa: F401
from runlib import soak
from runlib.expectations import Expectations
from runlib.soak import Sample, Sampler
from runlib.waiting import GameStalled
from scenarios import soak_days


def sample(wall, clock, days=0, rss=1000.0):
    return Sample(wall, clock, days, rss)


class RateTests(unittest.TestCase):
    def test_running_rate_ignores_stalled_gaps(self):
        samples = [sample(0, 0), sample(2, 16), sample(4, 16), sample(6, 16), sample(8, 32)]
        self.assertEqual(soak.running_rate(samples), 8.0)
        self.assertEqual(soak.overall_rate(samples), 4.0)
        self.assertEqual(soak.stalled_gaps(samples), 2)
        self.assertEqual(soak.longest_stall_s(samples), 4.0)

    def test_no_progress_gives_none(self):
        self.assertIsNone(soak.running_rate([sample(0, 5), sample(2, 5)]))
        self.assertIsNone(soak.running_rate([sample(0, 5)]))
        self.assertIsNone(soak.overall_rate([sample(0, 5)]))

    def test_longest_stall_restarts_after_progress(self):
        samples = [sample(0, 0), sample(2, 0), sample(4, 10), sample(6, 10), sample(8, 10), sample(10, 10)]
        self.assertEqual(soak.longest_stall_s(samples), 6.0)


class MemoryTests(unittest.TestCase):
    def test_sums_processes_and_skips_dead_ones(self):
        alive = mock.Mock()
        alive.memory_info.return_value = mock.Mock(rss=512 * soak.MB)
        dead = mock.Mock()
        dead.memory_info.side_effect = OSError("gone")
        self.assertEqual(soak.process_memory_mb([alive, dead, alive]), 1024.0)
        self.assertIsNone(soak.process_memory_mb([dead]))
        self.assertIsNone(soak.process_memory_mb([]))


class SamplerTests(unittest.TestCase):
    def test_sampler_records_wall_time_from_its_start(self):
        wall = iter([100.0, 102.5, 105.0])
        sampler = Sampler(lambda: next(wall), lambda: 7.0, lambda: 3, lambda: 900.0)
        sampler()
        sampler()
        self.assertEqual([s.wall_s for s in sampler.samples], [2.5, 5.0])
        self.assertEqual(sampler.samples[0], Sample(2.5, 7.0, 3, 900.0))


class MemoryCheckTests(unittest.TestCase):
    def check(self, first, last):
        expect = Expectations()
        soak_days.check_memory(expect, sample(0, 0, rss=first), sample(600, 0, rss=last))
        return expect.result()["passed"]

    def test_steady_memory_passes(self):
        self.assertTrue(self.check(1200.0, 1500.0))

    def test_large_growth_fails(self):
        self.assertFalse(self.check(1200.0, 4000.0))

    def test_huge_total_fails(self):
        self.assertFalse(self.check(7000.0, 8300.0))

    def test_unreadable_memory_fails(self):
        expect = Expectations()
        soak_days.check_memory(expect, sample(0, 0, rss=None), sample(1, 0, rss=None))
        self.assertFalse(expect.result()["passed"])


class GameOverTests(unittest.TestCase):
    def test_playing_is_fine(self):
        soak.check_game_over(0, 50)

    def test_other_status_raises_a_clear_scenario_failure(self):
        from runlib.waiting import ScenarioFailure
        with self.assertRaisesRegex(soak.GameOver, "game over: currentGameVictoryStatus is 2 at daysTotal 137") as caught:
            soak.check_game_over(2, 137)
        self.assertIsInstance(caught.exception, ScenarioFailure)


class FeederTests(unittest.TestCase):
    def test_feeds_every_n_days(self):
        gave = []
        feeder = soak.Feeder(10, lambda: gave.append(1), first_day=5)
        results = [feeder(day) for day in (5, 9, 15, 16, 24, 25)]
        self.assertEqual(results, [False, False, True, False, False, True])
        self.assertEqual((len(gave), feeder.times), (2, 2))


class ScenarioShapeTests(unittest.TestCase):
    def test_scenario_is_long_and_covers_q1(self):
        self.assertEqual(soak_days.COVERS, ["Q1"])
        self.assertGreater(soak_days.LIMIT_S, soak_days.SOAK_WALL_S)
        self.assertTrue(soak_days.LONG_REASON)

    def test_a_stalled_game_is_a_scenario_failure(self):
        from runlib.waiting import ScenarioFailure
        self.assertTrue(issubclass(GameStalled, ScenarioFailure))


if __name__ == "__main__":
    unittest.main()
