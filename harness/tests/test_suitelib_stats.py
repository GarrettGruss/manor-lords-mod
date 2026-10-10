import math
import random
import unittest

import runlib_path  # noqa: F401
from suitelib import stats


class SummaryTest(unittest.TestCase):
    def test_summary_values(self):
        data = stats.summarize([1, 2, 3, 4, 10])
        self.assertEqual((data["n"], data["min"], data["median"], data["max"], data["mean"]), (5, 1, 3, 10, 4))
        self.assertAlmostEqual(data["stdev"], 3.5355, places=3)

    def test_empty_and_single(self):
        self.assertEqual(stats.summarize([]), {"n": 0})
        self.assertEqual(stats.summarize([7])["stdev"], 0.0)


class WilsonTest(unittest.TestCase):
    def test_known_interval(self):
        low, high = stats.wilson_interval(8, 10)
        self.assertAlmostEqual(low, 0.490, places=2)
        self.assertAlmostEqual(high, 0.943, places=2)

    def test_edges_stay_in_range(self):
        for passes, total in ((0, 5), (5, 5), (0, 0)):
            low, high = stats.wilson_interval(passes, total)
            self.assertTrue(0.0 <= low <= high <= 1.0)


class EffectSizeTest(unittest.TestCase):
    def test_cohens_d(self):
        self.assertAlmostEqual(stats.cohens_d([1, 2, 3], [3, 4, 5]), 2.0)

    def test_zero_variance_is_safe(self):
        self.assertEqual(stats.cohens_d([5, 5, 5], [5, 5, 5]), 0.0)
        self.assertEqual(stats.cohens_d([5, 5, 5], [7, 7, 7]), stats.EFFECT_CAP)
        self.assertEqual(stats.cohens_d([7, 7, 7], [5, 5, 5]), -stats.EFFECT_CAP)

    def test_too_few_values(self):
        self.assertIsNone(stats.cohens_d([1], [2]))

    def test_relative_difference_and_overlap(self):
        self.assertAlmostEqual(stats.relative_difference([10, 10, 10], [8, 8, 8]), -0.2)
        self.assertEqual(stats.relative_difference([0, 0], [0, 0]), 0.0)
        self.assertIsNone(stats.relative_difference([0, 0], [1, 1]))
        self.assertTrue(stats.ranges_overlap([1, 5], [4, 9]))
        self.assertFalse(stats.ranges_overlap([1, 3], [4, 9]))


class PermutationTest(unittest.TestCase):
    def test_full_separation_of_3_and_3_is_exactly_one_tenth(self):
        # 20 splits. Only the real split and its mirror are as extreme.
        self.assertAlmostEqual(stats.permutation_p_value([1, 2, 3], [7, 8, 9]), 2 / 20)

    def test_identical_values_give_p_one(self):
        self.assertEqual(stats.permutation_p_value([4, 4, 4], [4, 4, 4]), 1.0)

    def test_random_mode_is_deterministic(self):
        generator = random.Random(1)
        a = [generator.gauss(10, 1) for _ in range(20)]
        b = [generator.gauss(10, 1) for _ in range(20)]
        first = stats.permutation_p_value(a, b)
        self.assertEqual(first, stats.permutation_p_value(a, b))
        self.assertGreater(first, 0.0)

    def test_empty_group(self):
        self.assertIsNone(stats.permutation_p_value([], [1]))


class CompareTest(unittest.TestCase):
    def sample(self, seed, mean, count=8, spread=1.0):
        generator = random.Random(seed)
        return [generator.gauss(mean, spread) for _ in range(count)]

    def test_same_distribution_is_same(self):
        result = stats.compare(self.sample(1, 100), self.sample(2, 100))
        self.assertEqual(result["verdict"], "same")

    def test_shifted_distribution_is_different(self):
        result = stats.compare(self.sample(1, 100), self.sample(2, 105))
        self.assertEqual(result["verdict"], "different")
        self.assertFalse(result["overlap"])
        self.assertGreater(result["effect_size"], 2)

    def test_two_runs_are_inconclusive(self):
        self.assertEqual(stats.compare([1, 1], [9, 9])["verdict"], "inconclusive")

    def test_large_effect_without_significance_is_inconclusive(self):
        # 3 against 3 with heavy overlap: d is large but the exact p is above alpha.
        result = stats.compare([1, 5, 9], [4, 8, 12])
        self.assertEqual(result["verdict"], "inconclusive")

    def test_result_keys(self):
        keys = set(stats.compare([1, 2, 3], [4, 5, 6]))
        self.assertEqual(keys, {"a_summary", "b_summary", "effect_size", "rel_diff", "overlap", "p_value", "verdict"})
        self.assertFalse(math.isnan(stats.compare([1, 2, 3], [4, 5, 6])["p_value"]))


if __name__ == "__main__":
    unittest.main()
